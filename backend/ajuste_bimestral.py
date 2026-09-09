"""
Ajuste Bimestral automático (100% local, offline).

Ejecuta el notebook `Mileforum_Aprendiz_Ajuste_Bimestral_v0_1.ipynb` de forma
programática (nbclient, sin Jupyter server ni internet) sobre las decisiones
registradas del dominio, y **reemplaza el modelo** del aprendiz con el
`policy_adapter.pt` recién entrenado más los vocabularios/allowlist producidos.

Se dispara:
  - automáticamente cada 50 días desde la activación (scheduler en server.py)
  - manualmente vía POST /api/aprendiz/{dominio}/ajuste/ejecutar

Requiere PyTorch (igual que el notebook). Si no está disponible, la rutina
lo reporta en el estado sin tumbar la app.
"""

import re
import io
import json
import shutil
import zipfile
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

NOTEBOOK_NAME = "Mileforum_Aprendiz_Ajuste_Bimestral_v0_1.ipynb"

# Bundles reales del repo por dominio (unipersonales). Empresas no tienen
# bundle base: se sintetiza uno mínimo sólo para satisfacer al notebook.
BUNDLE_NAMES = {
    "abogado":          "abogado_unipersonal_multiceph_bundle_v1",
    "arquitecto":       "arquitectura_unipersonal_multiceph_bundle_v1",
    "contador":         "contador_multiceph_bundle_v1",
    "consultor_pyme":   "consultor_pyme_multiceph_bundle_v1",
    "diseno_producto":  "diseno_produccion_unipersonal_multiceph_bundle_v1",
    "operaciones":      "logistica_multiceph_bundle_v1",
}


def _patch_source(src: str, dominio: str, ll_path: Path, ad_path: Path,
                  sd_path: Path, bundle_zip: Path, workdir: Path, outdir: Path) -> str:
    """Reemplaza las constantes de la Celda 1 del notebook por rutas absolutas."""
    reps = {
        r'^(\s*BUNDLE_ZIP_PATH\s*=).*$': f'BUNDLE_ZIP_PATH = r"{bundle_zip}"',
        r'^(\s*WORKDIR\s*=).*$':         f'WORKDIR = Path(r"{workdir}")',
        r'^(\s*OUTPUT_DIR\s*=).*$':      f'OUTPUT_DIR = Path(r"{outdir}")',
        r'^(\s*LEARNING_LOG_PATH\s*=).*$': f'LEARNING_LOG_PATH = Path(r"{ll_path}")',
        r'^(\s*ACTION_DICT_PATH\s*=).*$':  f'ACTION_DICT_PATH = Path(r"{ad_path}")',
        r'^(\s*SOFT_DICT_PATH\s*=).*$':    f'SOFT_DICT_PATH = Path(r"{sd_path}")',
        r'^(\s*BIMESTER_START\s*=).*$':  'BIMESTER_START = "2000-01-01"',
        r'^(\s*BIMESTER_END\s*=).*$':    'BIMESTER_END   = "2100-01-01"',
        r'^(\s*TARGET_DOMAIN\s*:.*=).*$': f'TARGET_DOMAIN: Optional[str] = "{dominio}"',
    }
    out = []
    for line in src.split("\n"):
        for pat, new in reps.items():
            if re.match(pat, line):
                line = new
                break
        out.append(line)
    return "\n".join(out)


def _sintetizar_bundle(dominio: str, destino: Path) -> Path:
    """Crea un bundle mínimo (config.json + model.pt) para dominios sin bundle real."""
    import torch
    zpath = destino / f"{dominio}_synthetic_bundle.zip"
    buf = io.BytesIO()
    torch.save({"placeholder": torch.zeros(1)}, buf)
    with zipfile.ZipFile(zpath, "w") as z:
        z.writestr(f"{dominio}/config.json", json.dumps({"domain": dominio}))
        z.writestr(f"{dominio}/model.pt", buf.getvalue())
    return zpath


def _bundle_para(dominio: str, root_dir: Path, workdir: Path) -> Path:
    nombre = BUNDLE_NAMES.get(dominio)
    if nombre:
        real = root_dir / f"{nombre}.zip"
        if real.exists():
            return real
    return _sintetizar_bundle(dominio, workdir)


def preparar_local_store(aprendiz_dir: Path, dominio: str, local_store: Path):
    """Copia learning_log + diccionarios del dominio al local_store del notebook."""
    local_store.mkdir(parents=True, exist_ok=True)

    ll = aprendiz_dir / f"{dominio}_learning_log.jsonl"
    if not ll.exists():
        raise FileNotFoundError(
            f"No hay learning_log para '{dominio}'. Registra decisiones antes de ajustar."
        )
    shutil.copy(ll, local_store / "learning_log.jsonl")

    ad = aprendiz_dir / f"{dominio}_action_dictionary_state.json"
    (local_store / "action_dictionary_state.json").write_text(
        ad.read_text(encoding="utf-8") if ad.exists()
        else json.dumps({"actions_by_phase": {}}), encoding="utf-8")

    sd = aprendiz_dir / f"{dominio}_soft_dictionary_state.json"
    (local_store / "soft_dictionary_state.json").write_text(
        sd.read_text(encoding="utf-8") if sd.exists()
        else json.dumps({"custom_soft_vars": []}), encoding="utf-8")


def estado(aprendiz_dir: Path, dominio: str) -> dict:
    ruta = aprendiz_dir / f"{dominio}_ajuste_estado.json"
    if ruta.exists():
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"dominio": dominio, "estado": "nunca_ejecutado", "ultimo_run": None}


def _guardar_estado(aprendiz_dir: Path, dominio: str, data: dict):
    (aprendiz_dir / f"{dominio}_ajuste_estado.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolver_repo_root(root_dir: Path) -> Path:
    """El notebook y los bundles viven en la raíz del repo, no en backend/."""
    for cand in (root_dir, root_dir.parent, root_dir.parent.parent):
        if (cand / NOTEBOOK_NAME).exists():
            return cand
    return root_dir


def ejecutar(dominio: str, root_dir: Path, aprendiz_dir: Path) -> dict:
    """
    Ejecuta el notebook de ajuste para el dominio y promueve el nuevo modelo.
    Devuelve un resumen del run. No lanza excepción: registra el error en estado.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = {"dominio": dominio, "run_id": ts,
            "iniciado_at": datetime.now(timezone.utc).isoformat()}
    try:
        import nbformat
        from nbclient import NotebookClient
        try:
            import torch  # noqa: F401
        except ImportError:
            raise RuntimeError("PyTorch no está instalado; el ajuste requiere torch.")

        repo_root = _resolver_repo_root(root_dir)

        run_dir = aprendiz_dir / "ajuste_runs" / dominio / ts
        run_dir.mkdir(parents=True, exist_ok=True)
        local_store = run_dir / "local_store"
        workdir = run_dir / "work"
        outdir = run_dir / "bimester_outputs"
        workdir.mkdir(parents=True, exist_ok=True)

        preparar_local_store(aprendiz_dir, dominio, local_store)
        bundle_zip = _bundle_para(dominio, repo_root, workdir)

        nb_path = repo_root / NOTEBOOK_NAME
        nb = nbformat.read(str(nb_path), as_version=4)
        for cell in nb.cells:
            if cell.cell_type == "code":
                cell.source = _patch_source(
                    cell.source, dominio,
                    local_store / "learning_log.jsonl",
                    local_store / "action_dictionary_state.json",
                    local_store / "soft_dictionary_state.json",
                    bundle_zip, workdir, outdir)

        client = NotebookClient(nb, timeout=900, kernel_name="python3",
                                resources={"metadata": {"path": str(run_dir)}})
        client.execute()

        # Localizar RUN_OUT producido (bimester_outputs/bimester_*/)
        runs = sorted([p for p in outdir.glob("bimester_*") if p.is_dir()],
                      key=lambda p: p.stat().st_mtime)
        run_out = runs[-1] if runs else None

        promovidos = []
        report = {}
        if run_out:
            adapter = run_out / "policy_adapter.pt"
            if adapter.exists():
                shutil.copy(adapter, aprendiz_dir / f"{dominio}_policy_adapter.pt")
                promovidos.append("policy_adapter.pt")
            for extra in ["allowed_actions_by_phase.json", "actions_added_this_bimester.json",
                          "soft_vocab.json", "action_vocab.json", "bimester_report.json"]:
                src = run_out / extra
                if src.exists():
                    shutil.copy(src, aprendiz_dir / f"{dominio}_{extra}")
                    promovidos.append(extra)
            rep = run_out / "bimester_report.json"
            if rep.exists():
                report = json.loads(rep.read_text(encoding="utf-8"))
            # Diccionario de acciones actualizado -> promover como estado activo
            allowed = run_out / "allowed_actions_by_phase.json"
            if allowed.exists():
                (aprendiz_dir / f"{dominio}_action_dictionary_state.json").write_text(
                    json.dumps({"actions_by_phase": json.loads(allowed.read_text()),
                                "updated_at": datetime.now(timezone.utc).isoformat()},
                               ensure_ascii=False, indent=2), encoding="utf-8")

        base.update({
            "estado": "completado",
            "modelo_reemplazado": "policy_adapter.pt" in promovidos,
            "artefactos_promovidos": promovidos,
            "report": report.get("counts", {}),
            "ultimo_run": datetime.now(timezone.utc).isoformat(),
            "finalizado_at": datetime.now(timezone.utc).isoformat(),
        })
        _guardar_estado(aprendiz_dir, dominio, base)
        logger.info(f"[AJUSTE] {dominio} completado · promovidos={promovidos}")
        return base

    except Exception as e:
        base.update({
            "estado": "error",
            "error": str(e),
            "ultimo_run": datetime.now(timezone.utc).isoformat(),
            "finalizado_at": datetime.now(timezone.utc).isoformat(),
        })
        _guardar_estado(aprendiz_dir, dominio, base)
        logger.error(f"[AJUSTE] {dominio} error: {e}")
        return base

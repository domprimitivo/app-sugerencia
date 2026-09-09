"""
Inferencia con el modelo ya ajustado (PolicyAdapter promovido por el ajuste
bimestral). Se usa para que la sugerencia del asistente mejore con cada
corrección, en vez de depender sólo del RAG.

Replica EXACTAMENTE la vectorización del notebook de ajuste
(`Mileforum_Aprendiz_Ajuste_Bimestral_v0_1.ipynb`, celda 9):

    v = [phase_probs[k] for k in phase_prob_keys]
        + [clarity.ok, clarity.pmax, clarity.gap, clarity.entropy]
        + [R_score]
        + one_hot(soft_tags sobre soft_vocab)

Las clases de salida son `action_vocab.json` (allow_action_ids ordenados).
Si el modelo no existe o el vector no cuadra con `in_dim`, devuelve None
(fallback a la sugerencia base del RAG). 100% local, sin internet.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

logger = logging.getLogger(__name__)

_CACHE: Dict[str, Any] = {}


def _cargar(dominio: str, aprendiz_dir: Path):
    """Carga (y cachea) adapter + vocabularios. Devuelve dict o None."""
    adapter_path = aprendiz_dir / f"{dominio}_policy_adapter.pt"
    vocab_path = aprendiz_dir / f"{dominio}_action_vocab.json"
    soft_path = aprendiz_dir / f"{dominio}_soft_vocab.json"
    ll_path = aprendiz_dir / f"{dominio}_learning_log.jsonl"
    if not (adapter_path.exists() and vocab_path.exists()):
        return None

    mtime = adapter_path.stat().st_mtime
    cached = _CACHE.get(dominio)
    if cached and cached["mtime"] == mtime:
        return cached

    try:
        import torch
        import torch.nn as nn

        state = torch.load(adapter_path, map_location="cpu")
        in_dim = state["net.0.weight"].shape[1]
        hidden = state["net.0.weight"].shape[0]
        out_dim = state["net.6.weight"].shape[0]

        class PolicyAdapter(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(in_dim, hidden), nn.ReLU(), nn.Dropout(0.1),
                    nn.Linear(hidden, hidden), nn.ReLU(), nn.Dropout(0.1),
                    nn.Linear(hidden, out_dim),
                )

            def forward(self, x):
                return self.net(x)

        model = PolicyAdapter()
        model.load_state_dict(state)
        model.eval()

        action_vocab: List[str] = json.loads(vocab_path.read_text(encoding="utf-8"))
        soft_vocab: List[str] = json.loads(soft_path.read_text(encoding="utf-8")) if soft_path.exists() else []

        # Reconstruir phase_prob_keys igual que el notebook (unión ordenada).
        phase_keys = set()
        if ll_path.exists():
            for line in ll_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                probs = (ev.get("backbone_inference") or {}).get("phase_probs") or {}
                phase_keys.update(probs.keys())
        phase_prob_keys = sorted(phase_keys)

        # Mapa action_id -> label desde el diccionario de acciones promovido.
        id2label = {}
        adict = aprendiz_dir / f"{dominio}_action_dictionary_state.json"
        if adict.exists():
            try:
                data = json.loads(adict.read_text(encoding="utf-8"))
                for ph, lst in (data.get("actions_by_phase") or {}).items():
                    for a in lst:
                        if isinstance(a, dict) and a.get("action_id"):
                            id2label[a["action_id"]] = a.get("label", a["action_id"])
            except Exception:
                pass

        entry = {
            "mtime": mtime, "model": model, "torch": torch,
            "action_vocab": action_vocab, "soft_vocab": soft_vocab,
            "phase_prob_keys": phase_prob_keys, "in_dim": in_dim,
            "id2label": id2label,
        }
        _CACHE[dominio] = entry
        return entry
    except Exception as e:
        logger.warning(f"[inferencia] no se pudo cargar adapter de {dominio}: {e}")
        return None


def sugerir_entrenada(dominio: str, sugerencia_base: Dict[str, Any],
                      aprendiz_dir: Path) -> Optional[Tuple[str, str]]:
    """
    Devuelve (action_id, action_label) según el modelo entrenado, o None si no
    hay modelo o el vector no cuadra (fallback a la sugerencia base del RAG).
    """
    ctx = _cargar(dominio, aprendiz_dir)
    if not ctx:
        return None

    torch = ctx["torch"]
    probs = sugerencia_base.get("phase_probs") or {}
    clarity = sugerencia_base.get("clarity") or {}
    soft_tags = sugerencia_base.get("soft_tags") or []
    soft_vocab = ctx["soft_vocab"]

    v: List[float] = [float(probs.get(k, 0.0)) for k in ctx["phase_prob_keys"]]
    v += [1.0 if clarity.get("ok") else 0.0,
          float(clarity.get("pmax", 0.0)),
          float(clarity.get("gap", 0.0)),
          float(clarity.get("entropy", 0.0))]
    v.append(float(sugerencia_base.get("R_score", 0.0)))
    st = [0.0] * len(soft_vocab)
    idx = {t: i for i, t in enumerate(soft_vocab)}
    for t in soft_tags:
        if t in idx:
            st[idx[t]] = 1.0
    v += st

    if len(v) != ctx["in_dim"]:
        logger.info(f"[inferencia] vector {len(v)} != in_dim {ctx['in_dim']} ({dominio}); fallback RAG")
        return None

    with torch.no_grad():
        x = torch.tensor([v], dtype=torch.float32)
        logits = ctx["model"](x)
        pred = int(torch.argmax(logits, dim=1).item())

    action_vocab = ctx["action_vocab"]
    if pred < 0 or pred >= len(action_vocab):
        return None
    action_id = action_vocab[pred]
    label = ctx["id2label"].get(action_id, action_id.replace("_", " "))
    return action_id, label

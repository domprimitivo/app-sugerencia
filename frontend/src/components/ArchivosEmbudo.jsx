import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, Upload, FileArchive, FileUp, Boxes, RefreshCw,
  CheckCircle2, AlertTriangle, Download, Filter,
} from 'lucide-react';
import { Watermark } from './Watermark';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Paleta arquitectónica (ladrillo / cielo / césped / arena)
const C = {
  sand: '#E9DFC9', panel: '#F4EEDF', border: '#D8C8A6',
  brick: '#A94E34', brickDark: '#7E3A26', sky: '#3E7CB1',
  grass: '#4E7A34', amber: '#E0A82E', red: '#C0392B',
  ink: '#3A2E28', muted: '#8A7A66',
};

const SEMAFORO = { VERDE: '#4E7A34', AMARILLO: '#E0A82E', ROJO: '#C0392B' };

// ─────────────────────────────────────────────────────────────
// MODO DEL LAZO — hardcodeado para esta versión (build/exe actual).
// Para otro repositorio/instalación cámbialo a 'AGENCIA' aquí:
export const MODO_LAZO = 'ASESORIA';   // <-- cambiar a 'AGENCIA' para el modo agencia
// ─────────────────────────────────────────────────────────────

const descargar = (nombre, bytesB64OrText, isB64 = false) => {
  const data = isB64
    ? Uint8Array.from(atob(bytesB64OrText), (c) => c.charCodeAt(0))
    : bytesB64OrText;
  const blob = new Blob([data], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = nombre; a.click();
  URL.revokeObjectURL(url);
};

export const ArchivosEmbudo = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(null); // 'embudo' | 'codec'
  const [report, setReport] = useState(null);
  const [reconstruidos, setReconstruidos] = useState(null);
  const [embudoOut, setEmbudoOut] = useState(null);
  const [msg, setMsg] = useState(null);
  const [domainId, setDomainId] = useState('');
  const [dominios, setDominios] = useState([]);
  const [flujo, setFlujo] = useState(null);
  const [loadingFlujo, setLoadingFlujo] = useState(false);

  useEffect(() => {
    axios.get(`${API}/flujo/dominios`).then((r) => {
      const emp = (r.data.empresariales || []).map((d) => ({ ...d, es_demo: false }));
      const demo = (r.data.demostracion || []).map((d) => ({ ...d, es_demo: true }));
      const all = [...emp, ...demo];
      setDominios(all);
      if (all.length) setDomainId(all[0].domain_id);
    }).catch(() => {});
  }, []);

  const ejecutarFlujo = async () => {
    if (!domainId) { setMsg('Selecciona un tipo de empresa.'); return; }
    setLoadingFlujo(true); setFlujo(null); setMsg(null);
    try {
      const fd = new FormData();
      fd.append('domain_id', domainId);
      fd.append('modo', MODO_LAZO);
      files.forEach((f) => fd.append('files', f));
      const r = await axios.post(`${API}/flujo/ejecutar-dominio`, fd);
      setFlujo(r.data);
    } catch (e) {
      setMsg('Flujo: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoadingFlujo(false);
    }
  };

  const onPick = (e) => {
    setFiles(Array.from(e.target.files || []));
    setReport(null); setReconstruidos(null); setEmbudoOut(null); setMsg(null);
  };

  const comprimirToggle = async () => {
    if (!files.length) { setMsg('Selecciona al menos un archivo.'); return; }
    setLoading('codec'); setMsg(null); setReport(null); setReconstruidos(null);
    try {
      const fd = new FormData();
      files.forEach((f) => fd.append('files', f));
      const r = await axios.post(`${API}/compresion/toggle`, fd);
      if (r.data.accion === 'comprimido') {
        setReport(r.data.shape_report);
        descargar('paquete.mocg.json', JSON.stringify(r.data.paquete));
        setMsg('Comprimido: descarga del paquete .mocg.json iniciada.');
      } else {
        setReconstruidos(r.data);
        setMsg(`Descomprimido: ${r.data.n_archivos} archivo(s), integridad ${r.data.integridad_ok ? 'OK' : 'FALLIDA'}.`);
      }
    } catch (e) {
      setMsg('Error en compresión geométrica: ' + (e.response?.data?.detail || e.message));
    } finally { setLoading(null); }
  };

  const procesarEmbudo = async () => {
    if (!files.length) { setMsg('Selecciona al menos un archivo.'); return; }
    setLoading('embudo'); setMsg(null); setEmbudoOut(null);
    try {
      const exp = await axios.post(`${API}/expedientes`, {
        nombre: `Embudo ${new Date().toISOString().slice(0, 16)}`,
        descripcion: 'Procesamiento con el embudo (RAG)',
      });
      const expId = exp.data.id;
      for (const f of files) {
        const fd = new FormData(); fd.append('file', f);
        await axios.post(`${API}/expedientes/${expId}/documentos`, fd);
      }
      const res = await axios.post(`${API}/expedientes/${expId}/procesar`, { tipo_consulta: 'analisis' });
      setEmbudoOut(res.data);
      setMsg('Procesado con el embudo (RAG) correctamente.');
    } catch (e) {
      setMsg('Embudo: ' + (e.response?.data?.detail || e.message));
    } finally { setLoading(null); }
  };

  const panel = { background: C.panel, border: `1px solid ${C.border}` };

  return (
    <div className="min-h-screen" style={{ background: `linear-gradient(180deg, #CBDDEC 0%, ${C.sand} 45%)`, color: C.ink }} data-testid="archivos-embudo">
      <Watermark />

      <header className="sticky top-0 z-20" style={{ background: C.brick }}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-3">
          <Link to="/" data-testid="archivos-back-link" style={{ color: '#F4EEDF' }}>
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Boxes className="w-5 h-5" style={{ color: '#F4EEDF' }} />
          <div>
            <h1 className="font-mono text-sm sm:text-base font-bold" style={{ color: '#F4EEDF' }}>ARCHIVOS · EMBUDO</h1>
            <p className="text-xs" style={{ color: '#F4EEDFbb' }}>Ingesta RAG · Compresión geométrica · Modo {MODO_LAZO === 'ASESORIA' ? 'Asesoría' : 'Agencia'}</p>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 relative z-[1]">
        <section className="rounded-2xl p-6" style={panel}>
          <h2 className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: C.brick }}>Seleccionar archivos</h2>
          <label
            className="flex flex-col items-center justify-center gap-3 rounded-xl py-10 cursor-pointer transition-colors"
            style={{ border: `1px dashed ${C.border}`, background: '#FFFFFF55' }}
            data-testid="file-dropzone"
          >
            <Upload className="w-8 h-8" style={{ color: C.brick }} />
            <span className="text-sm" style={{ color: C.muted }}>Haz clic para elegir archivos (usuario o del sistema)</span>
            <input type="file" multiple className="hidden" onChange={onPick} data-testid="file-input" />
          </label>
          {files.length > 0 && (
            <ul className="mt-4 space-y-1" data-testid="file-list">
              {files.map((f, i) => (
                <li key={i} className="text-sm flex items-center gap-2" style={{ color: C.ink }}>
                  <FileUp className="w-4 h-4" style={{ color: C.muted }} /> {f.name}
                  <span className="text-xs" style={{ color: C.muted }}>({Math.round(f.size / 1024)} KB)</span>
                </li>
              ))}
            </ul>
          )}

          <div className="flex flex-wrap gap-3 mt-6">
            <button
              onClick={procesarEmbudo} disabled={loading !== null}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full transition-transform active:scale-95 disabled:opacity-60"
              style={{ border: `1.5px solid ${C.brick}`, color: C.brick, background: 'transparent' }}
              data-testid="procesar-embudo-btn"
            >
              {loading === 'embudo' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Filter className="w-4 h-4" />}
              Procesar con el embudo
            </button>
            <button
              onClick={comprimirToggle} disabled={loading !== null}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full font-semibold transition-transform active:scale-95 disabled:opacity-60"
              style={{ background: C.brick, color: '#F4EEDF' }}
              data-testid="comprimir-btn"
            >
              {loading === 'codec' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileArchive className="w-4 h-4" />}
              Comprimir / Descomprimir
            </button>
          </div>

          {msg && <p className="mt-4 text-sm" style={{ color: C.ink }} data-testid="archivos-msg">{msg}</p>}
        </section>

        {/* ── Flujo de KPIs: Cucurucho → 7 KPIs limpios → Lazo ── */}
        <section className="rounded-2xl p-6" style={panel} data-testid="flujo-panel">
          <h2 className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: C.brick }}>
            Observación · Cucurucho → Métricas
          </h2>
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <select
              value={domainId}
              onChange={(e) => { setDomainId(e.target.value); setFlujo(null); }}
              className="rounded-full px-4 py-2 text-sm"
              style={{ background: '#FFFFFF88', border: `1px solid ${C.border}`, color: C.ink }}
              data-testid="flujo-dominio-select"
            >
              {dominios.map((d) => (
                <option key={d.domain_id} value={d.domain_id}>
                  {d.descriptor}{d.es_demo ? ' · (demostración)' : ''}
                </option>
              ))}
            </select>
            <button
              onClick={ejecutarFlujo}
              disabled={loadingFlujo}
              className="flex items-center gap-2 px-5 py-2 rounded-full font-semibold transition-transform active:scale-95 disabled:opacity-60"
              style={{ background: C.sky, color: '#F4EEDF' }}
              data-testid="ejecutar-flujo-btn"
            >
              {loadingFlujo ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Filter className="w-4 h-4" />}
              Preparar las métricas y ejecutar la observación
            </button>
          </div>
          <p className="text-xs" style={{ color: C.muted }}>
            El cucurucho y sus agentes (elemento de claridad, universal) separan las métricas
            de los datos tradicionales de la ingesta (o de la operación demo del palenque) y
            entregan la observación con el elemento de habitabilidad: semáforo y trayectoria.
          </p>

          {flujo && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mt-6 space-y-5" data-testid="flujo-resultado">
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
                <span style={{ color: C.ink }}><b>{flujo.cliente.client_name}</b></span>
                <span style={{ color: C.muted }}>{flujo.dominio.descriptor}</span>
                {flujo.dominio.es_demo && (
                  <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: C.amber, color: C.ink }}>DEMOSTRACIÓN</span>
                )}
                <span style={{ color: C.muted }} className="text-xs">
                  preparan: {flujo.cucurucho.agentes.filter((a) => a.prepara_kpis).map((a) => a.id).join(', ')}
                </span>
              </div>

              {/* Métricas: dato tradicional (discreto) ↔ contraparte geométrica */}
              <div>
                <p className="text-[11px] font-mono uppercase tracking-wider mb-2" style={{ color: C.muted }}>
                  Métricas · dato tradicional (discreto) ↔ contraparte geométrica
                </p>
                <div className="grid sm:grid-cols-2 gap-3">
                  {Object.entries(flujo.lazo.kpis).map(([nombre, ev]) => (
                    <div key={nombre} className="rounded-lg px-3 py-3"
                      style={{ border: `1px solid ${C.border}` }} data-testid={`flujo-kpi-${nombre}`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="w-3.5 h-3.5 rounded-full shrink-0"
                          style={{ background: SEMAFORO[ev.estado] || C.muted }} />
                        <span className="text-sm flex-1 truncate font-medium" style={{ color: C.ink }}>{nombre}</span>
                        <span className="font-mono text-sm" style={{ color: C.ink }}>{ev.valor.toFixed(2)}</span>
                      </div>
                      <div className="space-y-0.5" style={{ borderTop: `1px dashed ${C.border}`, paddingTop: 6 }}>
                        {(flujo.metricas_discretas?.[nombre] || []).map((d, i) => (
                          <div key={i} className="flex justify-between text-xs" style={{ color: C.muted }}>
                            <span>{d.campo}</span>
                            <span className="font-mono">
                              {d.valor ?? '—'}{d.norm != null ? ` → ${d.norm}` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Features de control */}
              <div className="flex flex-wrap gap-2" data-testid="flujo-control">
                <Flag ok={flujo.features_control.viable} label={`viabilidad ${flujo.features_control.c_viabilidad}`} />
                <Flag ok={flujo.features_control.suelo_firme} label={`suelo R ${flujo.features_control.firmeza_suelo_R}`} />
                <Flag ok={flujo.features_control.coherente} label={`Δ coherencia ${flujo.features_control.delta_coherencia}`} />
              </div>

              {/* Salida del lazo */}
              <div className="rounded-xl px-5 py-4" style={{ background: flujo.lazo.requiere_cenit ? C.brick : '#FFFFFF66', border: `1px solid ${C.border}` }} data-testid="flujo-lazo">
                <p className="text-[11px] font-mono uppercase tracking-wider mb-1"
                  style={{ color: flujo.lazo.requiere_cenit ? '#F4EEDFbb' : C.muted }}>
                  {flujo.lazo.requiere_cenit ? 'Cénit · Trayectoria' : 'Trayectoria · Estado ' + flujo.lazo.estado_general}
                </p>
                <p className="text-lg font-semibold" style={{ color: flujo.lazo.requiere_cenit ? '#F4EEDF' : C.ink }}>
                  {flujo.lazo.geodesica_sugerida.nombre}
                </p>
              </div>
            </motion.div>
          )}
        </section>

        {report && (
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl p-6" style={panel} data-testid="shape-report">
            <h2 className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: C.brick }}>Reporte de forma</h2>
            <div className="grid sm:grid-cols-3 gap-4 mb-4">
              <Metric label="Eventos" value={report.n_events_total} />
              <Metric label="En la forma" value={`${report.n_in_form} (${report.pct_in_form}%)`} color={C.grass} />
              <Metric label="Fuera de la forma" value={report.n_out_form} color={C.red} />
              <Metric label="Entidades" value={report.manifold?.n_entities} />
              <Metric label="Ratio compresión" value={`${report.compression?.ratio}x`} />
              <Metric label="Archivos" value={report.n_files} />
            </div>
            {report.top_anomalous?.length > 0 && (
              <div>
                <h3 className="text-xs font-mono uppercase mb-2" style={{ color: C.muted }}>Top anomalías (lo que no entró)</h3>
                <div className="space-y-1">
                  {report.top_anomalous.map((a, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm" data-testid={`anomaly-${i}`}>
                      <AlertTriangle className="w-4 h-4" style={{ color: C.red }} />
                      <span style={{ color: C.ink }}>{a.entity}</span>
                      <span style={{ color: C.muted }}>dis={a.dis}</span>
                      <span className="text-xs" style={{ color: C.muted }}>{a.hot_dims.join(', ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.section>
        )}

        {reconstruidos && (
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl p-6" style={panel} data-testid="reconstruidos">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-5 h-5" style={{ color: reconstruidos.integridad_ok ? C.grass : C.red }} />
              <h2 className="font-mono text-xs uppercase tracking-wider" style={{ color: C.brick }}>
                Archivos reconstruidos {reconstruidos.integridad_ok ? '(íntegros)' : '(¡integridad fallida!)'}
              </h2>
            </div>
            <div className="space-y-2">
              {reconstruidos.archivos.map((a, i) => (
                <div key={i} className="flex items-center gap-3 text-sm" data-testid={`reconstruido-${i}`}>
                  <span className="flex-1" style={{ color: C.ink }}>{a.nombre}</span>
                  <span className="text-xs" style={{ color: a.sha256_ok ? C.grass : C.red }}>
                    {a.sha256_ok ? 'sha256 OK' : 'sha256 ✗'}
                  </span>
                  <button onClick={() => descargar(a.nombre, a.datos_b64, true)}
                    className="flex items-center gap-1 text-xs" style={{ color: C.brick }}
                    data-testid={`descargar-${i}`}>
                    <Download className="w-4 h-4" /> Descargar
                  </button>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {embudoOut && (
          <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl p-6" style={panel} data-testid="embudo-out">
            <h2 className="font-mono text-xs uppercase tracking-wider mb-3" style={{ color: C.brick }}>Salida del embudo (RAG)</h2>
            <pre className="text-xs overflow-x-auto whitespace-pre-wrap" style={{ color: C.ink }}>
              {JSON.stringify(embudoOut, null, 2)}
            </pre>
          </motion.section>
        )}
      </div>
    </div>
  );
};

const Metric = ({ label, value, color }) => (
  <div className="rounded-lg px-4 py-3" style={{ border: '1px solid #D8C8A6' }}>
    <p className="text-[11px] font-mono uppercase tracking-wider" style={{ color: '#8A7A66' }}>{label}</p>
    <p className="font-mono text-lg font-bold" style={{ color: color || '#3A2E28' }}>{value ?? '—'}</p>
  </div>
);

const Flag = ({ ok, label }) => (
  <span className="text-xs px-3 py-1 rounded-full font-mono" data-testid="control-flag"
    style={{ background: ok ? '#4E7A3422' : '#C0392B22', color: ok ? '#4E7A34' : '#C0392B', border: `1px solid ${ok ? '#4E7A34' : '#C0392B'}55` }}>
    {ok ? '✓' : '✕'} {label}
  </span>
);

export default ArchivosEmbudo;

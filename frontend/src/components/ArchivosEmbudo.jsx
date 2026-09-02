import { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, Upload, FileArchive, FileUp, Boxes, RefreshCw,
  CheckCircle2, AlertTriangle, Download, Filter,
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
  a.href = url;
  a.download = nombre;
  a.click();
  URL.revokeObjectURL(url);
};

export const ArchivosEmbudo = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(null); // 'embudo' | 'codec'
  const [report, setReport] = useState(null);
  const [reconstruidos, setReconstruidos] = useState(null);
  const [embudoOut, setEmbudoOut] = useState(null);
  const [msg, setMsg] = useState(null);

  const onPick = (e) => {
    setFiles(Array.from(e.target.files || []));
    setReport(null); setReconstruidos(null); setEmbudoOut(null); setMsg(null);
  };

  // ── Compresión geométrica (alterna comprimir/descomprimir) ──
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
    } finally {
      setLoading(null);
    }
  };

  // ── Procesar con el embudo (RAG) ──
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
        const fd = new FormData();
        fd.append('file', f);
        await axios.post(`${API}/expedientes/${expId}/documentos`, fd);
      }
      const res = await axios.post(`${API}/expedientes/${expId}/procesar`, { tipo_consulta: 'analisis' });
      setEmbudoOut(res.data);
      setMsg('Procesado con el embudo (RAG) correctamente.');
    } catch (e) {
      setMsg('Embudo: ' + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-200" data-testid="archivos-embudo">
      <header className="border-b border-zinc-800 sticky top-0 z-20 bg-[#09090B]/90 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-3">
          <Link to="/" className="text-zinc-500 hover:text-white" data-testid="archivos-back-link">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Boxes className="w-5 h-5 text-[#FACC15]" />
          <div>
            <h1 className="font-mono text-sm sm:text-base font-bold text-white">ARCHIVOS · EMBUDO</h1>
            <p className="text-xs text-zinc-500">Ingesta RAG · Compresión geométrica · Modo {MODO_LAZO === 'ASESORIA' ? 'Asesoría' : 'Agencia'}</p>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Selección de archivos */}
        <section className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/50">
          <h2 className="font-mono text-xs uppercase tracking-wider text-[#FACC15] mb-4">Seleccionar archivos</h2>
          <label
            className="flex flex-col items-center justify-center gap-3 border border-dashed border-zinc-700 rounded-lg py-10 cursor-pointer hover:border-zinc-500 transition-colors"
            data-testid="file-dropzone"
          >
            <Upload className="w-8 h-8 text-zinc-500" />
            <span className="text-zinc-400 text-sm">Haz clic para elegir archivos (usuario o del sistema)</span>
            <input type="file" multiple className="hidden" onChange={onPick} data-testid="file-input" />
          </label>
          {files.length > 0 && (
            <ul className="mt-4 space-y-1" data-testid="file-list">
              {files.map((f, i) => (
                <li key={i} className="text-sm text-zinc-300 flex items-center gap-2">
                  <FileUp className="w-4 h-4 text-zinc-500" /> {f.name}
                  <span className="text-zinc-600 text-xs">({Math.round(f.size / 1024)} KB)</span>
                </li>
              ))}
            </ul>
          )}

          <div className="flex flex-wrap gap-3 mt-6">
            <button
              onClick={procesarEmbudo}
              disabled={loading !== null}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-zinc-700 text-zinc-200 hover:bg-zinc-800 transition-colors disabled:opacity-60"
              data-testid="procesar-embudo-btn"
            >
              {loading === 'embudo' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Filter className="w-4 h-4" />}
              Procesar con el embudo
            </button>
            <button
              onClick={comprimirToggle}
              disabled={loading !== null}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#FACC15] text-black font-semibold hover:bg-[#FDE047] transition-colors disabled:opacity-60"
              data-testid="comprimir-btn"
            >
              {loading === 'codec' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileArchive className="w-4 h-4" />}
              Comprimir / Descomprimir
            </button>
          </div>

          {msg && (
            <p className="mt-4 text-sm text-zinc-300" data-testid="archivos-msg">{msg}</p>
          )}
        </section>

        {/* Reporte de forma (compresión) */}
        {report && (
          <motion.section
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/50" data-testid="shape-report"
          >
            <h2 className="font-mono text-xs uppercase tracking-wider text-[#FACC15] mb-4">Reporte de forma</h2>
            <div className="grid sm:grid-cols-3 gap-4 mb-4">
              <Metric label="Eventos" value={report.n_events_total} />
              <Metric label="En la forma" value={`${report.n_in_form} (${report.pct_in_form}%)`} color="#22C55E" />
              <Metric label="Fuera de la forma" value={report.n_out_form} color="#EF4444" />
              <Metric label="Entidades" value={report.manifold?.n_entities} />
              <Metric label="Ratio compresión" value={`${report.compression?.ratio}x`} />
              <Metric label="Archivos" value={report.n_files} />
            </div>
            {report.top_anomalous?.length > 0 && (
              <div>
                <h3 className="text-xs font-mono uppercase text-zinc-400 mb-2">Top anomalías (lo que no entró)</h3>
                <div className="space-y-1">
                  {report.top_anomalous.map((a, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm" data-testid={`anomaly-${i}`}>
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <span className="text-zinc-300">{a.entity}</span>
                      <span className="text-zinc-500">dis={a.dis}</span>
                      <span className="text-zinc-600 text-xs">{a.hot_dims.join(', ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.section>
        )}

        {/* Reconstruidos (descompresión) */}
        {reconstruidos && (
          <motion.section
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/50" data-testid="reconstruidos"
          >
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className={`w-5 h-5 ${reconstruidos.integridad_ok ? 'text-green-400' : 'text-red-400'}`} />
              <h2 className="font-mono text-xs uppercase tracking-wider text-[#FACC15]">
                Archivos reconstruidos {reconstruidos.integridad_ok ? '(íntegros)' : '(¡integridad fallida!)'}
              </h2>
            </div>
            <div className="space-y-2">
              {reconstruidos.archivos.map((a, i) => (
                <div key={i} className="flex items-center gap-3 text-sm" data-testid={`reconstruido-${i}`}>
                  <span className="text-zinc-300 flex-1">{a.nombre}</span>
                  <span className={a.sha256_ok ? 'text-green-400 text-xs' : 'text-red-400 text-xs'}>
                    {a.sha256_ok ? 'sha256 OK' : 'sha256 ✗'}
                  </span>
                  <button
                    onClick={() => descargar(a.nombre, a.datos_b64, true)}
                    className="flex items-center gap-1 text-[#FACC15] hover:text-[#FDE047] text-xs"
                    data-testid={`descargar-${i}`}
                  >
                    <Download className="w-4 h-4" /> Descargar
                  </button>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Salida del embudo (RAG) */}
        {embudoOut && (
          <motion.section
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/50" data-testid="embudo-out"
          >
            <h2 className="font-mono text-xs uppercase tracking-wider text-[#FACC15] mb-3">Salida del embudo (RAG)</h2>
            <pre className="text-xs text-zinc-300 overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(embudoOut, null, 2)}
            </pre>
          </motion.section>
        )}
      </div>
    </div>
  );
};

const Metric = ({ label, value, color }) => (
  <div className="border border-zinc-800 rounded-lg px-4 py-3">
    <p className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">{label}</p>
    <p className="font-mono text-lg font-bold" style={{ color: color || '#FFFFFF' }}>{value ?? '—'}</p>
  </div>
);

export default ArchivosEmbudo;

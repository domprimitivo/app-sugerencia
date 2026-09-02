import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft, Compass, ShieldCheck, Gauge, AlertTriangle,
  CheckCircle2, Bot, Hand, RefreshCw,
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Presets de ejemplo (del notebook unificado)
const PRESET_NOMINAL = {
  'Permeabilidad': 0.65, 'Tensión TR': 0.25, 'Sutura': 0.20,
  'Retorno al Suelo': 0.75, 'Estancamiento': 0.15, 'Ruptura de Fase': 0.20,
  'Resonancia': 0.25,
};
const PRESET_AUTOENGANO = {
  'Permeabilidad': 0.55, 'Tensión TR': 0.60, 'Sutura': 0.65,
  'Retorno al Suelo': 0.45, 'Estancamiento': 0.50, 'Ruptura de Fase': 0.55,
  'Resonancia': 0.25,
};

const ESTADO_COLOR = {
  VERDE: '#22C55E', AMARILLO: '#FACC15', ROJO: '#EF4444',
  FIRME: '#22C55E', OK: '#22C55E', TRANSICION: '#FACC15',
  INESTABLE: '#EF4444', FALLO: '#EF4444', ACTIVO: '#A855F7', INACTIVO: '#52525B',
};

const ESTADO_GENERAL_COLOR = {
  NOMINAL: '#22C55E', MONITOREO: '#FACC15', TENSION: '#F97316',
  FRACTURA: '#EF4444', 'AUTOENGAÑO': '#A855F7',
};

const Dot = ({ estado, size = 12 }) => (
  <span
    style={{ width: size, height: size, backgroundColor: ESTADO_COLOR[estado] || '#52525B' }}
    className="inline-block rounded-full shrink-0"
    data-testid="estado-dot"
  />
);

export const PantallaClaridad = () => {
  const [dominio, setDominio] = useState(null);
  const [modo, setModo] = useState('ASESORIA');
  const [kpis, setKpis] = useState(PRESET_NOMINAL);
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API}/lazo/dominio`)
      .then((r) => setDominio(r.data))
      .catch(() => setError('No se pudo cargar la configuración del dominio.'));
  }, []);

  const setKpi = (nombre, valor) => {
    setKpis((prev) => ({ ...prev, [nombre]: valor }));
  };

  const evaluar = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await axios.post(`${API}/lazo/evaluar`, { modo, kpis });
      setResultado(r.data);
    } catch (e) {
      setError('Error al ejecutar el lazo.');
    } finally {
      setLoading(false);
    }
  };

  const nombres = dominio?.kpis_nombres || Object.keys(PRESET_NOMINAL);

  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-200" data-testid="pantalla-claridad">
      {/* Header */}
      <header className="border-b border-zinc-800 sticky top-0 z-20 bg-[#09090B]/90 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Link
              to="/"
              className="text-zinc-500 hover:text-white transition-colors"
              data-testid="claridad-back-link"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <Compass className="w-5 h-5 text-[#FACC15]" />
            <div className="min-w-0">
              <h1 className="font-mono text-sm sm:text-base font-bold text-white truncate">
                PANTALLA DE CLARIDAD
              </h1>
              <p className="text-xs text-zinc-500 truncate">
                Navegación Prudencial · {dominio?.nombre || '—'}
              </p>
            </div>
          </div>

          {/* Toggle de modo */}
          <div className="flex items-center gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1">
            {['ASESORIA', 'AGENCIA'].map((m) => (
              <button
                key={m}
                onClick={() => { setModo(m); setResultado(null); }}
                className={`px-3 py-1.5 rounded-md text-xs font-mono font-semibold transition-colors ${
                  modo === m ? 'bg-[#FACC15] text-black' : 'text-zinc-400 hover:text-white'
                }`}
                data-testid={`modo-toggle-${m.toLowerCase()}`}
              >
                {m === 'ASESORIA' ? 'ASESORÍA' : 'AGENCIA'}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid lg:grid-cols-[380px_1fr] gap-8">
        {/* ── Panel de entrada: KPIs ── */}
        <section data-testid="kpis-input-panel">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-mono text-xs uppercase tracking-wider text-[#FACC15]">
              KPIs de Cantor Inverso
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => { setKpis(PRESET_NOMINAL); setResultado(null); }}
                className="text-[11px] font-mono px-2 py-1 rounded border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500 transition-colors"
                data-testid="preset-nominal-btn"
              >
                Nominal
              </button>
              <button
                onClick={() => { setKpis(PRESET_AUTOENGANO); setResultado(null); }}
                className="text-[11px] font-mono px-2 py-1 rounded border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500 transition-colors"
                data-testid="preset-autoengano-btn"
              >
                Autoengaño
              </button>
            </div>
          </div>

          <div className="space-y-5 bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
            {nombres.map((nombre) => (
              <div key={nombre} data-testid={`kpi-input-${nombre}`}>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm text-zinc-300">{nombre}</label>
                  <span className="font-mono text-sm text-[#FACC15] tabular-nums">
                    {(kpis[nombre] ?? 0).toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min="0" max="1" step="0.01"
                  value={kpis[nombre] ?? 0}
                  onChange={(e) => setKpi(nombre, parseFloat(e.target.value))}
                  className="w-full accent-[#FACC15]"
                  data-testid={`kpi-slider-${nombre}`}
                />
              </div>
            ))}

            <button
              onClick={evaluar}
              disabled={loading}
              className="w-full mt-2 bg-[#FACC15] text-black font-semibold py-2.5 rounded-lg hover:bg-[#FDE047] transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
              data-testid="evaluar-btn"
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Gauge className="w-4 h-4" />}
              Ejecutar lazo
            </button>
            {error && (
              <p className="text-sm text-red-400" data-testid="claridad-error">{error}</p>
            )}
          </div>
        </section>

        {/* ── Panel de salida: resultado del lazo ── */}
        <section data-testid="resultado-panel">
          {!resultado ? (
            <div
              className="h-full min-h-[300px] flex flex-col items-center justify-center text-center border border-dashed border-zinc-800 rounded-xl p-10"
              data-testid="resultado-vacio"
            >
              <Compass className="w-10 h-10 text-zinc-700 mb-4" />
              <p className="text-zinc-500 max-w-sm">
                Ajusta los KPIs y ejecuta el lazo. La pantalla de claridad mostrará
                exactamente lo que el sistema produce.
              </p>
            </div>
          ) : (
            <motion.div
              key={resultado.modo + resultado.estado_general}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <ResultadoLazo resultado={resultado} />
            </motion.div>
          )}
        </section>
      </div>
    </div>
  );
};

const ResultadoLazo = ({ resultado }) => {
  const {
    modo, kpis, estado_general, geodesica_sugerida, autoengano,
    fallo_pegado, ejecutar_autonomamente,
  } = resultado;

  return (
    <>
      {/* Estado general */}
      <div
        className="flex items-center gap-3 border border-zinc-800 rounded-xl px-5 py-4 bg-zinc-900/50"
        data-testid="estado-general"
      >
        <span
          style={{ backgroundColor: ESTADO_GENERAL_COLOR[estado_general] || '#52525B' }}
          className="w-3 h-3 rounded-full"
        />
        <div>
          <p className="text-xs text-zinc-500 font-mono uppercase tracking-wider">Estado general</p>
          <p className="font-mono text-lg font-bold text-white" data-testid="estado-general-valor">
            {estado_general}
          </p>
        </div>
        <span className="ml-auto text-xs font-mono px-2.5 py-1 rounded border border-zinc-700 text-zinc-400">
          {modo === 'ASESORIA' ? 'ASESORÍA' : 'AGENCIA'}
        </span>
      </div>

      {/* KPIs evaluados */}
      <div className="border border-zinc-800 rounded-xl p-5 bg-zinc-900/50">
        <h3 className="font-mono text-xs uppercase tracking-wider text-zinc-400 mb-4">KPIs evaluados</h3>
        <div className="grid sm:grid-cols-2 gap-x-6 gap-y-3">
          {Object.entries(kpis).map(([nombre, ev]) => (
            <div key={nombre} className="flex items-center gap-3" data-testid={`kpi-result-${nombre}`}>
              <Dot estado={ev.estado} />
              <span className="text-sm text-zinc-300 flex-1 truncate">{nombre}</span>
              <span className="font-mono text-sm text-zinc-100 tabular-nums">{ev.valor.toFixed(3)}</span>
              <span className="font-mono text-[11px] w-20 text-right" style={{ color: ESTADO_COLOR[ev.estado] }}>
                {ev.estado}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Barra de estado (solo AGENCIA) */}
      {modo === 'AGENCIA' && (
        <div className="border border-zinc-800 rounded-xl p-5 bg-zinc-900/50" data-testid="barra-hermanos">
          <h3 className="font-mono text-xs uppercase tracking-wider text-zinc-400 mb-4">
            Barra de estado · Tres Hermanos
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <HermanoCard titulo="Corto" hermano={resultado.hermano_corto} />
            <HermanoCard titulo="Mediano" hermano={resultado.hermano_mediano} />
            <HermanoCard titulo="Largo" hermano={resultado.hermano_largo} />
          </div>
        </div>
      )}

      {/* Diagnóstico */}
      {(autoengano || fallo_pegado) && (
        <div className="space-y-2" data-testid="diagnostico">
          {autoengano && (
            <div className="flex items-start gap-3 border border-purple-500/40 bg-purple-500/10 rounded-xl px-5 py-3">
              <AlertTriangle className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
              <p className="text-sm text-purple-200">
                <b>Autoengaño detectado:</b> el sistema se está mintiendo a sí mismo.
              </p>
            </div>
          )}
          {fallo_pegado && (
            <div className="flex items-start gap-3 border border-red-500/40 bg-red-500/10 rounded-xl px-5 py-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <p className="text-sm text-red-200">
                <b>Fallo de pegado:</b> forma y ritmo divergen.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Geodésica sugerida */}
      <div className="border border-zinc-800 rounded-xl p-5 bg-zinc-900/50" data-testid="geodesica-sugerida">
        <div className="flex items-center gap-2 mb-2">
          <Compass className="w-4 h-4 text-[#FACC15]" />
          <h3 className="font-mono text-xs uppercase tracking-wider text-zinc-400">Geodésica sugerida</h3>
        </div>
        <p className="text-white font-medium">{geodesica_sugerida.nombre}</p>
        <p className="text-sm text-zinc-500 mt-1">Condición: {geodesica_sugerida.condicion}</p>
      </div>

      {/* Acción */}
      <div className="border border-zinc-800 rounded-xl p-5 bg-zinc-900/50" data-testid="accion-panel">
        {modo === 'ASESORIA' ? (
          <>
            <div className="flex items-center gap-2 mb-4">
              <Hand className="w-4 h-4 text-[#FACC15]" />
              <h3 className="font-mono text-xs uppercase tracking-wider text-zinc-400">
                Acción requerida · El humano autoriza
              </h3>
            </div>
            <div className="flex flex-wrap gap-3">
              <button className="px-5 py-2 rounded-lg bg-[#FACC15] text-black font-semibold hover:bg-[#FDE047] transition-colors" data-testid="btn-autorizar">
                Autorizar
              </button>
              <button className="px-5 py-2 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors" data-testid="btn-rechazar">
                Rechazar
              </button>
              <button className="px-5 py-2 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors" data-testid="btn-modificar">
                Modificar
              </button>
            </div>
          </>
        ) : ejecutar_autonomamente ? (
          <div className="flex items-start gap-3" data-testid="accion-autonoma">
            <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-green-300 font-medium">Acción ejecutada autónomamente</p>
              <p className="text-sm text-zinc-400 mt-1">{geodesica_sugerida.nombre} aplicada.</p>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-4">
              <Bot className="w-4 h-4 text-purple-400" />
              <h3 className="font-mono text-xs uppercase tracking-wider text-zinc-400">
                Cénit requerido · Caso crítico
              </h3>
            </div>
            <div className="flex flex-wrap gap-3">
              <button className="px-5 py-2 rounded-lg bg-purple-500 text-white font-semibold hover:bg-purple-400 transition-colors" data-testid="btn-validar">
                Validar
              </button>
              <button className="px-5 py-2 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors" data-testid="btn-revisar">
                Revisar
              </button>
              <button className="px-5 py-2 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition-colors" data-testid="btn-escalar">
                Escalar
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
};

const HermanoCard = ({ titulo, hermano }) => (
  <div className="text-center border border-zinc-800 rounded-lg py-4 px-2" data-testid={`hermano-${titulo.toLowerCase()}`}>
    <p className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 mb-2">{titulo}</p>
    <span
      style={{ backgroundColor: ESTADO_COLOR[hermano.estado] || '#52525B' }}
      className="w-4 h-4 rounded-full inline-block mb-2"
    />
    <p className="font-mono text-sm font-semibold" style={{ color: ESTADO_COLOR[hermano.estado] }}>
      {hermano.estado}
    </p>
  </div>
);

export default PantallaClaridad;

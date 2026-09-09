import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowLeft, Compass, Import, Check } from 'lucide-react';
import { Watermark } from './Watermark';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Paleta arquitectónica (ladrillo / cielo / césped / arena)
const C = {
  sand: '#E9DFC9', panel: '#F4EEDF', border: '#D8C8A6',
  brick: '#A94E34', brickDark: '#7E3A26', sky: '#3E7CB1',
  grass: '#4E7A34', amber: '#E0A82E', red: '#C0392B',
  ink: '#3A2E28', muted: '#8A7A66',
};

// Semáforo: estado del KPI → color
const SEMAFORO = { VERDE: C.grass, AMARILLO: C.amber, ROJO: C.red };
// Hermanos → color
const HERMANO_COLOR = {
  FIRME: C.grass, OK: C.grass, TRANSICION: C.amber,
  INESTABLE: C.red, FALLO: C.red, ACTIVO: C.brick, INACTIVO: '#C9BCA2',
};

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

export const PantallaClaridad = () => {
  const [dominio, setDominio] = useState(null);
  const [modo, setModo] = useState('ASESORIA');
  const [kpis, setKpis] = useState(PRESET_NOMINAL);
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [convocada, setConvocada] = useState(false); // trayectoria convocada por el usuario
  const [registrando, setRegistrando] = useState(false);
  const [registroMsg, setRegistroMsg] = useState(null);

  useEffect(() => {
    axios.get(`${API}/lazo/dominio`).then((r) => setDominio(r.data)).catch(() => {});
  }, []);

  useEffect(() => { setConvocada(false); setRegistroMsg(null); }, [resultado, modo]);

  const setKpi = (nombre, valor) => setKpis((p) => ({ ...p, [nombre]: valor }));

  const evaluar = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${API}/lazo/evaluar`, { modo, kpis });
      setResultado(r.data);
    } catch (e) {
      /* silencio: interfaz gráfica */
    } finally {
      setLoading(false);
    }
  };

  const registrarEmbudo = async () => {
    if (!resultado) return;
    setRegistrando(true); setRegistroMsg(null);
    try {
      await axios.post(`${API}/embudo/registrar-resultado`, { modo, kpis, resultado });
      setRegistroMsg('ok');
    } catch (e) {
      setRegistroMsg('error');
    } finally {
      setRegistrando(false);
    }
  };

  const nombres = dominio?.kpis_nombres || Object.keys(PRESET_NOMINAL);
  const cenit = resultado?.requiere_cenit === true;          // el backend pide cénit
  const mostrarTrayectoria = !!resultado && (cenit || convocada);

  return (
    <div className="min-h-screen" style={{ background: `linear-gradient(180deg, #CBDDEC 0%, ${C.sand} 45%)` }} data-testid="pantalla-claridad">
      <Watermark />
      {/* Header mínimo */}
      <header className="sticky top-0 z-20" style={{ background: C.brick }}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" data-testid="claridad-back-link" style={{ color: '#F4EEDF' }}>
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <Compass className="w-5 h-5" style={{ color: '#F4EEDF' }} />
          </div>
          {/* Toggle de modo (gráfico) */}
          <div className="flex items-center gap-1 rounded-full p-1" style={{ background: '#00000022' }}>
            {['ASESORIA', 'AGENCIA'].map((m) => (
              <button
                key={m}
                onClick={() => { setModo(m); setResultado(null); }}
                className="w-3.5 h-3.5 rounded-full transition-transform"
                style={{
                  background: modo === m ? '#F4EEDF' : '#F4EEDF55',
                  transform: modo === m ? 'scale(1.15)' : 'scale(1)',
                }}
                data-testid={`modo-toggle-${m.toLowerCase()}`}
                aria-label={m}
              />
            ))}
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid lg:grid-cols-[320px_1fr] gap-10 relative z-[1]">
        {/* ── Entrada (controles gráficos) ── */}
        <section data-testid="kpis-input-panel">
          <div className="flex gap-2 mb-5">
            <button onClick={() => { setKpis(PRESET_NOMINAL); setResultado(null); }}
              className="w-3 h-3 rounded-full" style={{ background: C.grass }}
              data-testid="preset-nominal-btn" aria-label="preset nominal" />
            <button onClick={() => { setKpis(PRESET_AUTOENGANO); setResultado(null); }}
              className="w-3 h-3 rounded-full" style={{ background: C.red }}
              data-testid="preset-autoengano-btn" aria-label="preset autoengaño" />
          </div>

          <div className="space-y-4 rounded-2xl p-5" style={{ background: C.panel, border: `1px solid ${C.border}` }}>
            {nombres.map((nombre) => (
              <div key={nombre} data-testid={`kpi-input-${nombre}`}>
                <input
                  type="range" min="0" max="1" step="0.01"
                  value={kpis[nombre] ?? 0}
                  onChange={(e) => setKpi(nombre, parseFloat(e.target.value))}
                  className="w-full claridad-range"
                  data-testid={`kpi-slider-${nombre}`}
                  aria-label={nombre}
                />
              </div>
            ))}
            <button
              onClick={evaluar}
              disabled={loading}
              className="w-full mt-2 rounded-full py-3 font-semibold transition-transform active:scale-95 disabled:opacity-60"
              style={{ background: C.brick, color: '#F4EEDF' }}
              data-testid="evaluar-btn"
              aria-label="Ejecutar lazo"
            >
              <span className="inline-block w-2.5 h-2.5 rounded-full mr-2 align-middle"
                style={{ background: loading ? C.amber : '#F4EEDF' }} />
            </button>
          </div>
        </section>

        {/* ── Salida (100% gráfica; único texto = Trayectoria) ── */}
        <section data-testid="resultado-panel">
          {!resultado ? (
            <div className="h-full min-h-[320px] flex items-center justify-center rounded-2xl"
              style={{ border: `1px dashed ${C.border}` }} data-testid="resultado-vacio">
              <Compass className="w-10 h-10" style={{ color: C.muted }} />
            </div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-10">
              {/* Estado general: disco ambiental grande (sin texto) */}
              <div className="flex justify-center" data-testid="estado-general">
                <motion.div
                  initial={{ scale: 0.8 }} animate={{ scale: 1 }}
                  className="rounded-full"
                  style={{
                    width: 120, height: 120,
                    background: estadoColor(resultado.estado_general),
                    boxShadow: `0 0 0 10px ${estadoColor(resultado.estado_general)}22`,
                  }}
                  data-testid="estado-general-disc"
                />
              </div>

              {/* Semáforo de KPIs (sin nombres ni números) */}
              <div className="flex flex-wrap justify-center gap-6" data-testid="kpis-semaforo">
                {Object.entries(resultado.kpis).map(([nombre, ev], i) => (
                  <motion.div
                    key={nombre}
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className="rounded-full"
                    style={{
                      width: 44, height: 44,
                      background: SEMAFORO[ev.estado] || C.muted,
                      boxShadow: `0 0 0 6px ${(SEMAFORO[ev.estado] || C.muted)}22`,
                    }}
                    data-testid={`kpi-dot-${nombre}`}
                    aria-label={ev.estado}
                  />
                ))}
              </div>

              {/* Barra de Tres Hermanos (solo AGENCIA) — gráfica */}
              {modo === 'AGENCIA' && (
                <div className="flex justify-center gap-10" data-testid="barra-hermanos">
                  {[['Corto', resultado.hermano_corto], ['Mediano', resultado.hermano_mediano], ['Largo', resultado.hermano_largo]].map(([t, h]) => (
                    <div key={t}
                      className="rounded-md"
                      style={{ width: 26, height: 60, background: HERMANO_COLOR[h.estado] || C.muted }}
                      data-testid={`hermano-${t.toLowerCase()}`}
                      aria-label={`${t}: ${h.estado}`}
                    />
                  ))}
                </div>
              )}

              {/* Vínculo al lazo de control: ingesta en tiempo real (solo AGENCIA, opcional) */}
              {modo === 'AGENCIA' && resultado.ingesta_tiempo_real && (
                <div className="flex justify-center" data-testid="vinculo-lazo-control">
                  <span className="text-[11px] font-mono uppercase tracking-wider"
                    style={{ color: resultado.ingesta_tiempo_real.disponible ? C.grass : C.muted }}>
                    {resultado.ingesta_tiempo_real.disponible
                      ? `Lazo de control · tiempo real: ${resultado.ingesta_tiempo_real.total} evento(s)`
                      : 'Lazo de control · sin ingesta en tiempo real'}
                  </span>
                </div>
              )}

              {/* Trayectoria — ÚNICO texto. Convocada por el usuario, o auto si CÉNIT */}
              <div className="flex flex-col items-center pt-2" data-testid="trayectoria">
                <AnimatePresence mode="wait">
                  {!mostrarTrayectoria ? (
                    <motion.button
                      key="convocar"
                      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      onClick={() => setConvocada(true)}
                      className="rounded-full flex items-center justify-center"
                      data-testid="convocar-trayectoria-btn"
                      aria-label="Convocar trayectoria"
                      style={{ width: 22, height: 22, background: 'transparent' }}
                    >
                      <motion.span
                        className="block rounded-full"
                        style={{ width: 18, height: 18, background: C.sky }}
                        animate={{ scale: [1, 1.6, 1], opacity: [0.9, 0.25, 0.9] }}
                        transition={{ repeat: Infinity, duration: 2 }}
                      />
                    </motion.button>
                  ) : (
                    <motion.div
                      key="texto"
                      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                      className="text-center max-w-lg rounded-2xl px-8 py-6"
                      style={{
                        background: cenit ? C.brick : 'transparent',
                        border: cenit ? 'none' : `1px solid ${C.border}`,
                        color: cenit ? '#F4EEDF' : C.ink,
                      }}
                      data-testid="trayectoria-texto"
                    >
                      <p className="font-mono text-[11px] uppercase tracking-[0.2em] mb-2"
                        style={{ color: cenit ? '#F4EEDFaa' : C.muted }}>
                        {cenit ? 'Cénit · Trayectoria' : 'Trayectoria'}
                      </p>
                      <p className="text-xl font-semibold leading-snug" data-testid="trayectoria-nombre">
                        {resultado.geodesica_sugerida.nombre}
                      </p>
                      <p className="text-sm mt-2" style={{ color: cenit ? '#F4EEDFcc' : C.muted }}>
                        {resultado.geodesica_sugerida.condicion}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Procesar resultados con el embudo (ambos modos) */}
              <div className="flex flex-col items-center gap-2 pt-2" data-testid="embudo-registro">
                <button
                  onClick={registrarEmbudo}
                  disabled={registrando}
                  className="flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold transition-transform active:scale-95 disabled:opacity-60"
                  style={{ border: `1.5px solid ${C.sky}`, color: C.sky, background: '#FFFFFF88' }}
                  data-testid="procesar-embudo-nav-btn"
                >
                  {registroMsg === 'ok'
                    ? <><Check className="w-4 h-4" style={{ color: C.grass }} /> Registrado</>
                    : <><Import className="w-4 h-4" /> {registrando ? 'Procesando…' : 'Procesar con el embudo'}</>}
                </button>
                {registroMsg === 'error' && (
                  <span className="text-xs" style={{ color: C.red }} data-testid="embudo-registro-error">
                    No se pudo registrar
                  </span>
                )}
              </div>
            </motion.div>
          )}
        </section>
      </div>
    </div>
  );
};

function estadoColor(estado) {
  switch (estado) {
    case 'NOMINAL': return C.grass;
    case 'MONITOREO': return C.amber;
    case 'TENSION': return C.red;
    case 'FRACTURA': return C.red;
    case 'AUTOENGAÑO': return C.brick;
    default: return C.muted;
  }
}

export default PantallaClaridad;

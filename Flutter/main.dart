import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

void main() {
  runApp(const MileforumApp());
}

const String baseUrl = 'http://localhost:8001';
const Color azulPrincipal = Color(0xFF1D4E89);
const Color azulMedio = Color(0xFF2E86C1);
const Color fondoClaro = Color(0xFFF4F7FB);

class MileforumApp extends StatefulWidget {
  const MileforumApp({super.key});
  @override
  State<MileforumApp> createState() => _MileforumAppState();
}

class _MileforumAppState extends State<MileforumApp> {
  // null = verificando, false = no configurado, true = ya configurado
  bool? _yaConfigurado;
  String? _dominioActivo;
  String? _nombreDominio;
  String? _tipoDominio;

  @override
  void initState() {
    super.initState();
    _verificarConfiguracion();
  }

  Future<void> _verificarConfiguracion() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/config'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final configurado = data['configurado'] == true;
        setState(() {
          _yaConfigurado = configurado;
          if (configurado) {
            _dominioActivo = data['dominio_id'] as String?;
            _nombreDominio = data['dominio_nombre'] as String?;
            _tipoDominio   = data['tipo_dominio'] as String?;
          }
        });
        return;
      }
    } catch (_) {}
    setState(() { _yaConfigurado = false; });
  }

  @override
  Widget build(BuildContext context) {
    final theme = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: azulPrincipal),
      useMaterial3: true,
      scaffoldBackgroundColor: fondoClaro,
      appBarTheme: const AppBarTheme(
        backgroundColor: azulPrincipal,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
    );

    // Mientras verifica, mostrar splash minimo
    if (_yaConfigurado == null) {
      return MaterialApp(
        title: 'Mileforum',
        debugShowCheckedModeBanner: false,
        theme: theme,
        home: const Scaffold(
          body: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(color: azulPrincipal),
                SizedBox(height: 16),
                Text('Iniciando Mileforum...', style: TextStyle(color: azulPrincipal, fontSize: 14)),
              ],
            ),
          ),
        ),
      );
    }

    return MaterialApp(
      title: 'Mileforum',
      debugShowCheckedModeBanner: false,
      theme: theme,
      // Si ya esta configurado, ir directo a expedientes sin pasar por configuracion
      home: _yaConfigurado == true
          ? PantallaExpedientes(
              dominio: _dominioActivo ?? '',
              esEmpresa: _tipoDominio == 'empresa',
            )
          : const PantallaConfiguracion(),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANTALLA 1 — Configuracion (sin cambios F-05)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaConfiguracion extends StatefulWidget {
  const PantallaConfiguracion({super.key});
  @override
  State<PantallaConfiguracion> createState() => _PantallaConfiguracionState();
}

class _PantallaConfiguracionState extends State<PantallaConfiguracion> {
  String dominioSeleccionado = '';
  String modoSeleccionado = 'local';
  bool cargando = false;
  bool cargandoDominios = true;
  String mensaje = '';
  List<Map<String, dynamic>> dominios = [];

  // Mapeo visual por id de dominio. El backend solo conoce id/nombre/tipo/
  // descripcion (ver DOMINIOS_UNIPERSONALES y DOMINIOS_EMPRESAS en server.py);
  // los detalles puramente visuales (IconData, Color) viven aqui, en Flutter,
  // para no acoplar el backend a tipos de UI. Si se agrega un dominio nuevo
  // en server.py y no aparece aqui, cae en el fallback al final del mapa.
  static const Map<String, IconData> _iconosPorId = {
    'abogado': Icons.gavel,
    'arquitecto': Icons.architecture,
    'contador': Icons.calculate,
    'consultor_pyme': Icons.business_center,
    'diseno_producto': Icons.design_services,
    'operaciones': Icons.settings,
    'hotel': Icons.business,
    'clinica': Icons.local_hospital,
    'restaurante': Icons.restaurant,
    'retail': Icons.shopping_bag,
    'fabrica': Icons.factory,
    'logistica': Icons.local_shipping,
  };

  static const Map<String, Color> _coloresPorId = {
    'abogado': Color(0xFFD1FAE5),
    'arquitecto': Color(0xFFEDE9FE),
    'contador': Color(0xFFFEE2E2),
    'consultor_pyme': Color(0xFFE0F2FE),
    'diseno_producto': Color(0xFFFCE7F3),
    'operaciones': Color(0xFFF3E8FF),
    'hotel': Color(0xFFDBEAFE),
    'clinica': Color(0xFFFCE7F3),
    'restaurante': Color(0xFFFEF3C7),
    'retail': Color(0xFFE0E7FF),
    'fabrica': Color(0xFFFFE4E6),
    'logistica': Color(0xFFD1FAE5),
  };

  static const Map<String, Color> _iconColoresPorId = {
    'abogado': Color(0xFF065f46),
    'arquitecto': Color(0xFF5b21b6),
    'contador': Color(0xFF991b1b),
    'consultor_pyme': Color(0xFF0369a1),
    'diseno_producto': Color(0xFF9d174d),
    'operaciones': Color(0xFF6b21a8),
    'hotel': Color(0xFF1e40af),
    'clinica': Color(0xFF9d174d),
    'restaurante': Color(0xFF92400e),
    'retail': Color(0xFF3730a3),
    'fabrica': Color(0xFF9f1239),
    'logistica': Color(0xFF065f46),
  };

  @override
  void initState() {
    super.initState();
    cargarDominios();
  }

  Future<void> cargarDominios() async {
    setState(() { cargandoDominios = true; mensaje = ''; });
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/dominios'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final List<dynamic> unipersonales = data['unipersonales'] ?? [];
        final List<dynamic> empresas = data['empresas'] ?? [];

        final List<Map<String, dynamic>> cargados = [];
        for (final d in unipersonales) {
          cargados.add(_enriquecerDominio(d as Map<String, dynamic>, 'unipersonal'));
        }
        for (final d in empresas) {
          cargados.add(_enriquecerDominio(d as Map<String, dynamic>, 'empresa'));
        }

        setState(() {
          dominios = cargados;
          if (dominios.isNotEmpty) {
            dominioSeleccionado = dominios.first['id'] as String;
          }
          cargandoDominios = false;
        });
      } else {
        setState(() {
          mensaje = 'No se pudieron cargar los dominios del servidor.';
          cargandoDominios = false;
        });
      }
    } catch (e) {
      setState(() {
        mensaje = 'Sin conexion al servidor. Verifica que el backend este corriendo.';
        cargandoDominios = false;
      });
    }
  }

  // Combina los datos del backend (id, nombre, tipo, descripcion) con el
  // icono y los colores definidos localmente para ese id.
  Map<String, dynamic> _enriquecerDominio(Map<String, dynamic> d, String tipo) {
    final String id = d['id'] as String;
    return {
      'id': id,
      'nombre': d['nombre'] ?? id,
      'tipo': tipo,
      'subtipo': tipo == 'empresa' ? 'Motor RAG empresarial' : 'Motor Aprendiz',
      'icon': _iconosPorId[id] ?? Icons.apps,
      'color': _coloresPorId[id] ?? const Color(0xFFE5E7EB),
      'iconColor': _iconColoresPorId[id] ?? const Color(0xFF374151),
    };
  }

  // Se deriva de los datos reales cargados del backend, no de una lista fija
  // de nombres — asi nunca queda desincronizado si se agregan/quitan dominios.
  bool get esEmpresa {
    final match = dominios.where((d) => d['id'] == dominioSeleccionado);
    if (match.isEmpty) return false;
    return match.first['tipo'] == 'empresa';
  }

  Future<void> inicializar() async {
    if (dominioSeleccionado.isEmpty) {
      setState(() { mensaje = 'Selecciona un dominio antes de continuar.'; });
      return;
    }
    setState(() { cargando = true; mensaje = ''; });
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/config/inicializar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'dominio_id': dominioSeleccionado, 'modo': modoSeleccionado}),
      );
      if (response.statusCode == 200) {
        if (mounted) {
          Navigator.pushReplacement(context, PageRouteBuilder(
            pageBuilder: (_, a, __) => PantallaExpedientes(dominio: dominioSeleccionado, esEmpresa: esEmpresa),
            transitionsBuilder: (_, a, __, child) => SlideTransition(
              position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)),
              child: child,
            ),
          ));
        }
      } else {
        setState(() { mensaje = 'Error al inicializar.'; });
      }
    } catch (e) {
      setState(() { mensaje = 'Sin conexion al servidor. Verifica que el backend este corriendo.'; });
    }
    setState(() { cargando = false; });
  }

  @override
  Widget build(BuildContext context) {
    final empresas = dominios.where((d) => d['tipo'] == 'empresa').toList();
    final unipersonales = dominios.where((d) => d['tipo'] == 'unipersonal').toList();
    return Scaffold(
      appBar: AppBar(
        title: Row(children: [
          Container(width: 30, height: 30, decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
            child: const Icon(Icons.psychology, size: 18, color: Colors.white)),
          const SizedBox(width: 10),
          const Text('Mileforum'),
        ]),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(gradient: const LinearGradient(colors: [azulPrincipal, azulMedio], begin: Alignment.topLeft, end: Alignment.bottomRight), borderRadius: BorderRadius.circular(16)),
            child: Row(children: [
              Container(width: 52, height: 52, decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(14)),
                child: const Icon(Icons.settings, size: 26, color: Colors.white)),
              const SizedBox(width: 14),
              const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Modulo Maestro de Ingesta', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                SizedBox(height: 4),
                Text('Selecciona el dominio y configura el modo', style: TextStyle(color: Colors.white70, fontSize: 11)),
              ])),
            ]),
          ),
          const SizedBox(height: 16),
          if (cargandoDominios)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 40),
              child: Center(child: Column(children: [
                CircularProgressIndicator(color: azulPrincipal),
                SizedBox(height: 12),
                Text('Cargando dominios disponibles...', style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 12)),
              ])),
            )
          else if (dominios.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Column(children: [
                const Icon(Icons.cloud_off, size: 36, color: Color(0xFF7B8FA1)),
                const SizedBox(height: 8),
                const Text('No se pudieron cargar los dominios.', style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 13)),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: cargarDominios,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Reintentar'),
                ),
              ]),
            )
          else ...[
            _secLabel('Empresas'),
            ...empresas.map((d) => _domainCard(d)),
            _secLabel('Unipersonales'),
            ...unipersonales.map((d) => _domainCard(d)),
          ],
          _secLabel('Modo de operacion'),
          Container(
            decoration: BoxDecoration(color: const Color(0xFFE4EAF2), borderRadius: BorderRadius.circular(10)),
            padding: const EdgeInsets.all(3),
            child: Row(children: [
              Expanded(child: _modeBtn('local', Icons.storage, 'Local')),
              Expanded(child: _modeBtn('api', Icons.cloud, 'Cloud')),
            ]),
          ),
          const SizedBox(height: 16),
          if (mensaje.isNotEmpty)
            Container(margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(10)),
              child: Text(mensaje, style: const TextStyle(color: Colors.red, fontSize: 13))),
          SizedBox(width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: (cargando || dominios.isEmpty) ? null : inicializar,
              icon: cargando ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.play_arrow),
              label: Text(cargando ? 'Iniciando...' : 'Inicializar sistema'),
              style: ElevatedButton.styleFrom(
                backgroundColor: azulPrincipal, foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 15),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 4, shadowColor: azulPrincipal.withOpacity(0.4),
              ),
            ),
          ),
          const SizedBox(height: 16),
        ]),
      ),
    );
  }

  Widget _secLabel(String t) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 10),
    child: Text(t.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
  );

  Widget _domainCard(Map<String, dynamic> d) {
    final sel = dominioSeleccionado == d['id'];
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.only(bottom: 7),
      decoration: BoxDecoration(
        color: sel ? const Color(0xFFEBF5FF) : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: sel ? azulPrincipal : Colors.transparent, width: sel ? 2 : 0),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 1))],
      ),
      child: Material(color: Colors.transparent, borderRadius: BorderRadius.circular(14),
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: () => setState(() => dominioSeleccionado = d['id']),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
            child: Row(children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 40, height: 40,
                decoration: BoxDecoration(color: d['color'] as Color, borderRadius: BorderRadius.circular(10)),
                child: Icon(d['icon'] as IconData, size: 20, color: d['iconColor'] as Color),
              ),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(d['nombre'], style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
                Text(d['subtipo'], style: const TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
              ])),
              AnimatedOpacity(
                duration: const Duration(milliseconds: 200),
                opacity: sel ? 1 : 0,
                child: const Icon(Icons.check_circle, color: azulPrincipal, size: 20),
              ),
            ]),
          ),
        ),
      ),
    );
  }

  Widget _modeBtn(String id, IconData icon, String label) {
    final sel = modoSeleccionado == id;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: sel ? Colors.white : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        boxShadow: sel ? [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 4, offset: const Offset(0, 1))] : [],
      ),
      child: Material(color: Colors.transparent, borderRadius: BorderRadius.circular(8),
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () => setState(() => modoSeleccionado = id),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 9),
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              Icon(icon, size: 16, color: sel ? azulPrincipal : const Color(0xFF7B8FA1)),
              const SizedBox(width: 6),
              Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: sel ? azulPrincipal : const Color(0xFF7B8FA1))),
            ]),
          ),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANTALLA 2 — Expedientes (F-05: menu con Cierre Bimestral y Embudo Aprendiz)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaExpedientes extends StatefulWidget {
  final String dominio;
  final bool esEmpresa;
  const PantallaExpedientes({super.key, required this.dominio, required this.esEmpresa});
  @override
  State<PantallaExpedientes> createState() => _PantallaExpedientesState();
}

class _PantallaExpedientesState extends State<PantallaExpedientes> {
  List expedientes = [];
  bool cargando = true;

  @override
  void initState() { super.initState(); cargarExpedientes(); }

  Future<void> cargarExpedientes() async {
    setState(() => cargando = true);
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/expedientes'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final lista = (data is List) ? data : (data['expedientes'] ?? []);
        final filtrada = lista.where((e) => e['dominio_id'] == widget.dominio).toList();
        filtrada.sort((a, b) {
          final fechaA = a['created_at']?.toString() ?? '';
          final fechaB = b['created_at']?.toString() ?? '';
          return fechaB.compareTo(fechaA);
        });
        setState(() { expedientes = filtrada; });
      }
    } catch (e) { setState(() { expedientes = []; }); }
    setState(() => cargando = false);
  }

  Future<void> crearExpediente() async {
    String texto = '';
    await showDialog(context: context, builder: (ctx) => AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Text('Nuevo expediente', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
      content: TextField(
        autofocus: true,
        decoration: InputDecoration(hintText: 'Nombre del expediente', border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)), focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: azulPrincipal))),
        onChanged: (v) => texto = v,
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
        ElevatedButton(onPressed: () => Navigator.pop(ctx), style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: const Text('Crear')),
      ],
    ));
    if (texto.isNotEmpty) {
      try {
        await http.post(Uri.parse('$baseUrl/api/expedientes'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'nombre': texto, 'dominio_id': widget.dominio}));
        cargarExpedientes();
      } catch (e) {}
    }
  }

  Future<void> eliminarExpediente(Map exp) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Eliminar expediente', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
        content: Text('Eliminar "${exp['nombre'] ?? 'este expediente'}"? Esta accion no se puede deshacer.', style: const TextStyle(fontSize: 13, color: Color(0xFF5a6a7a))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF991b1b), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: const Text('Eliminar')),
        ],
      ),
    );
    if (confirmar == true) {
      try { await http.delete(Uri.parse('$baseUrl/api/expedientes/${exp['id']}')); } catch (e) {}
      cargarExpedientes();
    }
  }

  void navegar(Map exp) {
    Navigator.push(context, PageRouteBuilder(
      pageBuilder: (_, a, __) => PantallaIngesta(expedienteId: exp['id'], nombre: exp['nombre'] ?? 'Expediente', esEmpresa: widget.esEmpresa),
      transitionsBuilder: (_, a, __, child) => SlideTransition(position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)), child: child),
    ));
  }

  // F-05: navegar a Cierre Bimestral
  void _abrirCierreBimestral() {
    Navigator.push(context, PageRouteBuilder(
      pageBuilder: (_, a, __) => PantallaCierreBimestral(dominio: widget.dominio),
      transitionsBuilder: (_, a, __, child) => SlideTransition(position: Tween<Offset>(begin: const Offset(0, 1), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)), child: child),
    ));
  }

  // F-05: navegar a Embudo Aprendiz
  void _abrirEmbudoAprendiz() {
    Navigator.push(context, PageRouteBuilder(
      pageBuilder: (_, a, __) => PantallaEmbudoAprendiz(dominio: widget.dominio),
      transitionsBuilder: (_, a, __, child) => SlideTransition(position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)), child: child),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final completados = expedientes.where((e) => e['estado'] == 'completado').length;
    return Scaffold(
      appBar: AppBar(
        automaticallyImplyLeading: false,
        leading: IconButton(
          icon: const Icon(Icons.info_outline),
          tooltip: 'Información del sistema',
          onPressed: () async {
            // Consultar cliente_id desde el backend (viene del hardware, no de config.json)
            String clienteId = 'Consultando...';
            try {
              final r = await http.get(Uri.parse('$baseUrl/api/activacion/estado'))
                  .timeout(const Duration(seconds: 3));
              if (r.statusCode == 200) {
                final d = jsonDecode(r.body) as Map<String, dynamic>;
                clienteId = d['cliente_id']?.toString() ?? 'No disponible';
              }
            } catch (_) {
              clienteId = 'No disponible (backend sin conexion)';
            }
            if (!context.mounted) return;
            showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                title: const Text('Sistema configurado'),
                content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Dominio activo: ${widget.dominio}'),
                    const SizedBox(height: 12),
                    const Text('ID de instalación (para renovar suscripción):',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 4),
                    SelectableText(clienteId,
                      style: const TextStyle(fontFamily: 'monospace', fontSize: 11,
                        color: Color(0xFF1e40af))),
                    const SizedBox(height: 12),
                    const Text(
                      'Comparte este ID con el operador al renovar tu suscripción. '
                      'El sistema ya está inicializado — para cambiar el dominio, '
                      'reinstala la aplicación.',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6B7280)),
                    ),
                  ],
                ),
                actions: [
                  ElevatedButton(
                    onPressed: () => Navigator.pop(ctx),
                    style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white),
                    child: const Text('Entendido'),
                  ),
                ],
              ),
            );
          },
        ),
        title: Text('Expedientes · ${widget.dominio}'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: cargarExpedientes),
          // F-05: Menu con accesos especiales
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Colors.white),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            onSelected: (v) {
              if (v == 'bimestral') _abrirCierreBimestral();
              if (v == 'aprendiz') _abrirEmbudoAprendiz();
            },
            itemBuilder: (_) => [
              PopupMenuItem(value: 'bimestral', child: Row(children: [
                Container(width: 30, height: 30, decoration: BoxDecoration(color: const Color(0xFFEDE9FE), borderRadius: BorderRadius.circular(8)),
                  child: const Icon(Icons.calendar_month, size: 15, color: Color(0xFF5b21b6))),
                const SizedBox(width: 10),
                const Text('Cierre Bimestral', style: TextStyle(fontSize: 13)),
              ])),
              if (!widget.esEmpresa) PopupMenuItem(value: 'aprendiz', child: Row(children: [
                Container(width: 30, height: 30, decoration: BoxDecoration(color: const Color(0xFFD1FAE5), borderRadius: BorderRadius.circular(8)),
                  child: const Icon(Icons.school, size: 15, color: Color(0xFF065f46))),
                const SizedBox(width: 10),
                const Text('Embudo Aprendiz', style: TextStyle(fontSize: 13)),
              ])),
            ],
          ),
        ],
      ),
      body: cargando
        ? const Center(child: CircularProgressIndicator(color: azulPrincipal))
        : Column(children: [
          // F-05: Banner rapido si no es empresa
          if (!widget.esEmpresa)
            GestureDetector(
              onTap: _abrirEmbudoAprendiz,
              child: Container(
                margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFFD1FAE5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF6EE7B7)),
                ),
                child: Row(children: [
                  const Icon(Icons.school, size: 18, color: Color(0xFF065f46)),
                  const SizedBox(width: 10),
                  const Expanded(child: Text('Embudo del Aprendiz disponible', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF065f46)))),
                  const Icon(Icons.chevron_right, size: 16, color: Color(0xFF065f46)),
                ]),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(children: [
              Expanded(child: _statCard('${expedientes.length}', 'expedientes')),
              const SizedBox(width: 10),
              Expanded(child: _statCard('$completados', 'completados')),
            ]),
          ),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: _secLabel('Recientes')),
          Expanded(
            child: expedientes.isEmpty
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.folder_open, size: 64, color: Colors.grey.shade300),
                  const SizedBox(height: 16),
                  const Text('Sin expedientes', style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 16)),
                  const SizedBox(height: 8),
                  const Text('Crea el primero con el boton +', style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 12)),
                ]))
              : ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: expedientes.length,
                itemBuilder: (ctx, i) {
                  final exp = expedientes[i];
                  final ok = exp['estado'] == 'completado';
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 1))]),
                    child: Material(color: Colors.transparent, borderRadius: BorderRadius.circular(14),
                      child: InkWell(borderRadius: BorderRadius.circular(14), onTap: () => navegar(exp),
                        child: Padding(padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12), child: Row(children: [
                          Container(width: 42, height: 42, decoration: BoxDecoration(color: ok ? const Color(0xFFD1FAE5) : const Color(0xFFDBEAFE), borderRadius: BorderRadius.circular(12)),
                            child: Icon(ok ? Icons.folder_special : Icons.folder, size: 20, color: ok ? const Color(0xFF065f46) : const Color(0xFF1e40af))),
                          const SizedBox(width: 12),
                          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(exp['nombre'] ?? 'Sin nombre', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
                            const SizedBox(height: 4),
                            Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2), decoration: BoxDecoration(color: ok ? const Color(0xFFD1FAE5) : const Color(0xFFFEF3C7), borderRadius: BorderRadius.circular(20)),
                              child: Text(exp['estado'] ?? 'pendiente', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: ok ? const Color(0xFF065f46) : const Color(0xFF92400e)))),
                          ])),
                          GestureDetector(
                            onTap: () => eliminarExpediente(exp),
                            child: Container(width: 30, height: 30, decoration: BoxDecoration(color: const Color(0xFFFEE2E2), borderRadius: BorderRadius.circular(8)),
                              child: const Icon(Icons.delete_outline, size: 15, color: Color(0xFF991b1b))),
                          ),
                          const SizedBox(width: 6),
                          const Icon(Icons.chevron_right, color: Color(0xFFB8C9DC)),
                        ])),
                      ),
                    ),
                  );
                },
              ),
          ),
        ]),
      floatingActionButton: FloatingActionButton(
        onPressed: crearExpediente,
        backgroundColor: azulPrincipal,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        elevation: 6,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _statCard(String n, String l) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 1))]),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(n, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w500, color: azulPrincipal)),
      Text(l, style: const TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
    ]),
  );

  Widget _secLabel(String t) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Text(t.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANTALLA 3 — Ingesta (sin cambios F-05)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaIngesta extends StatefulWidget {
  final String expedienteId;
  final String nombre;
  final bool esEmpresa;
  const PantallaIngesta({super.key, required this.expedienteId, required this.nombre, required this.esEmpresa});
  @override
  State<PantallaIngesta> createState() => _PantallaIngestaState();
}

class _PantallaIngestaState extends State<PantallaIngesta> {
  List documentos = [];
  String textoLibre = '';
  String etiqueta = '';
  bool procesando = false;
  String mensaje = '';
  final TextEditingController _ctrl = TextEditingController();
  final TextEditingController _etiquetaCtrl = TextEditingController();

  @override
  void initState() { super.initState(); cargarDocumentos(); }
  @override
  void dispose() { _ctrl.dispose(); _etiquetaCtrl.dispose(); super.dispose(); }

  Future<void> cargarDocumentos() async {
    try {
      final r = await http.get(Uri.parse('$baseUrl/api/expedientes/${widget.expedienteId}/documentos'));
      if (r.statusCode == 200) {
        final d = jsonDecode(r.body);
        setState(() { documentos = d['documentos'] ?? []; });
      }
    } catch (e) {}
  }

  Future<void> abrirSelector() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.any,
        withData: true,
      );
      if (result != null && result.files.isNotEmpty) {
        final archivo = result.files.first;
        final bytes = archivo.bytes;
        if (bytes != null) {
          // Subir archivo al backend
          final request = http.MultipartRequest(
            'POST',
            Uri.parse('$baseUrl/api/expedientes/${widget.expedienteId}/documentos'),
          );
          request.files.add(http.MultipartFile.fromBytes(
            'file',
            bytes,
            filename: archivo.name,
          ));
          await request.send();
        }
        setState(() {
          documentos.add({
            'nombre_archivo': archivo.name,
            'timestamp': DateTime.now().toString().substring(0, 16),
            'tipo': 'archivo',
          });
        });
      }
    } catch (e) {
      setState(() {
        documentos.add({
          'nombre_archivo': 'documento_${documentos.length + 1}.pdf',
          'timestamp': DateTime.now().toString().substring(0, 16),
          'tipo': 'archivo',
        });
      });
    }
  }

  void agregarTexto() {
    if (_ctrl.text.isNotEmpty) {
      final tieneEtiqueta = etiqueta.trim().isNotEmpty;
      setState(() {
        documentos.add({
          'nombre_archivo': tieneEtiqueta ? '[${etiqueta.trim()}] ${DateTime.now().toString().substring(0, 16)}' : 'Nota - ${DateTime.now().toString().substring(0, 16)}',
          'tipo': tieneEtiqueta ? 'evento' : 'acompanante',
          'etiqueta': etiqueta.trim(),
          'contenido': _ctrl.text,
          'timestamp': DateTime.now().toString().substring(0, 16),
          'ingestado': tieneEtiqueta,
        });
        _ctrl.clear(); _etiquetaCtrl.clear(); textoLibre = ''; etiqueta = '';
      });
    }
  }

  Future<void> procesar() async {
    setState(() { procesando = true; mensaje = ''; });
    try {
      final r = await http.post(
        Uri.parse('$baseUrl/api/expedientes/${widget.expedienteId}/procesar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'tipo_consulta': 'analisis'}),
      );
      if (r.statusCode == 200) {
        final resultado = jsonDecode(r.body);
        if (mounted) {
          Navigator.push(context, PageRouteBuilder(
            pageBuilder: (_, a, __) => PantallaReporteClaridad(resultado: resultado, expedienteId: widget.expedienteId, esEmpresa: widget.esEmpresa),
            transitionsBuilder: (_, a, __, child) => SlideTransition(position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)), child: child),
          ));
        }
      } else { setState(() { mensaje = 'Error al procesar.'; }); }
    } catch (e) { setState(() { mensaje = 'Sin conexion al servidor.'; }); }
    setState(() => procesando = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        title: Text(widget.nombre, style: const TextStyle(fontSize: 15)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          GestureDetector(
            onTap: abrirSelector,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: double.infinity, padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(color: Colors.white, border: Border.all(color: const Color(0xFFB8CFDF), width: 1.5), borderRadius: BorderRadius.circular(16), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 4, offset: const Offset(0, 1))]),
              child: Column(children: [
                Icon(Icons.cloud_upload, size: 40, color: azulMedio),
                const SizedBox(height: 10),
                const Text('Embudo de ingesta', style: TextStyle(fontWeight: FontWeight.w500, fontSize: 14, color: Color(0xFF1a2332))),
                const SizedBox(height: 4),
                const Text('Toca para agregar documento al embudo', textAlign: TextAlign.center, style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 11)),
              ]),
            ),
          ),
          const SizedBox(height: 14),
          if (documentos.isNotEmpty) ...[
            _secLabel('Archivos cargados'),
            ...documentos.asMap().entries.map((entry) {
              final idx = entry.key;
              final doc = entry.value;
              final esEvento = doc['tipo'] == 'evento';
              final esAcompanante = doc['tipo'] == 'acompanante';
              final iconColor = esEvento ? const Color(0xFF1e40af) : esAcompanante ? const Color(0xFF92400e) : const Color(0xFF065f46);
              final iconBg = esEvento ? const Color(0xFFDBEAFE) : esAcompanante ? const Color(0xFFFEF3C7) : const Color(0xFFD1FAE5);
              final icono = esEvento ? Icons.bolt : esAcompanante ? Icons.notes : Icons.description;
              return Container(
                margin: const EdgeInsets.only(bottom: 7),
                padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 11),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 3, offset: const Offset(0, 1))]),
                child: Row(children: [
                  Container(width: 34, height: 34, decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(9)), child: Icon(icono, size: 16, color: iconColor)),
                  const SizedBox(width: 10),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(doc['nombre_archivo'] ?? doc['nombre'] ?? 'documento', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
                    if (doc['tipo'] == 'evento') const Text('Evento - ingestado', style: TextStyle(fontSize: 10, color: Color(0xFF1e40af)))
                    else if (doc['tipo'] == 'acompanante') const Text('Acompana con timestamp', style: TextStyle(fontSize: 10, color: Color(0xFF92400e))),
                  ])),
                  GestureDetector(
                    onTap: () => setState(() => documentos.removeAt(idx)),
                    child: Container(width: 28, height: 28, decoration: BoxDecoration(color: const Color(0xFFFEE2E2), borderRadius: BorderRadius.circular(7)), child: const Icon(Icons.close, size: 14, color: Color(0xFF991b1b))),
                  ),
                ]),
              );
            }),
            const SizedBox(height: 8),
          ],
          _secLabel('Escritura libre'),
          TextField(
            controller: _ctrl, maxLines: 4,
            decoration: InputDecoration(
              hintText: 'Escribe o pega notas, observaciones...',
              hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E8F0))),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: azulPrincipal)),
              filled: true, fillColor: Colors.white,
            ),
            onChanged: (v) => setState(() => textoLibre = v),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _etiquetaCtrl,
            decoration: InputDecoration(
              hintText: 'Etiqueta (opcional)',
              hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)),
              helperText: 'Con etiqueta se ingesta como evento. Sin etiqueta solo acompana.',
              helperStyle: const TextStyle(fontSize: 10, color: Color(0xFF9BAAB8)),
              prefixIcon: const Icon(Icons.label_outline, size: 16, color: Color(0xFF7B8FA1)),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E8F0))),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: azulPrincipal)),
              filled: true, fillColor: Colors.white,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
            onChanged: (v) => setState(() => etiqueta = v),
          ),
          const SizedBox(height: 8),
          Align(alignment: Alignment.centerRight,
            child: OutlinedButton.icon(
              onPressed: textoLibre.isNotEmpty ? agregarTexto : null,
              icon: const Icon(Icons.add, size: 16),
              label: const Text('Agregar al embudo', style: TextStyle(fontSize: 12)),
              style: OutlinedButton.styleFrom(foregroundColor: azulMedio, side: const BorderSide(color: Color(0xFFB8CFDF)), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9))),
            ),
          ),
          const SizedBox(height: 16),
          if (mensaje.isNotEmpty)
            Container(margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(10)),
              child: Text(mensaje, style: const TextStyle(color: Colors.red, fontSize: 12))),
          SizedBox(width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: documentos.isEmpty ? null : (procesando ? null : procesar),
              icon: procesando ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.psychology),
              label: Text(procesando ? 'Procesando...' : 'Procesar con motor IA'),
              style: ElevatedButton.styleFrom(
                backgroundColor: azulPrincipal, foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 15),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                elevation: 4, shadowColor: azulPrincipal.withOpacity(0.4),
              ),
            ),
          ),
          const SizedBox(height: 16),
        ]),
      ),
    );
  }

  Widget _secLabel(String t) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Text(t.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANTALLA 4 — Reporte de Claridad (F-05: seccion anomalias)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaReporteClaridad extends StatelessWidget {
  final Map resultado;
  final String expedienteId;
  final bool esEmpresa;
  const PantallaReporteClaridad({super.key, required this.resultado, required this.expedienteId, required this.esEmpresa});

  @override
  Widget build(BuildContext context) {
    final tieneConector = resultado.containsKey('overall_reading');
    final overallReading = (resultado['overall_reading'] as Map?) ?? {};
    final estado = (overallReading['overall_state'] ?? resultado['fase'] ?? 'Estabilidad').toString();
    final afinidad = overallReading['overall_affinity'];
    final nodos = (resultado['prioritized_nodes'] as List?) ?? [];
    final acciones = (resultado['recommended_actions'] as List?) ?? [];
    final bloqueos = (resultado['blocked_actions'] as List?) ?? [];
    final rrhh = (resultado['rrhh_decision_reading'] as Map?) ?? {};
    final tensionHumana = rrhh['level']?.toString() ?? '';
    final narrativaEjecutiva = resultado['executive_summary_md']?.toString();
    final narrativaOperativa = resultado['operator_report_md']?.toString();
    final resumenFallback = resultado['resumen']?.toString() ?? resultado['sugerencia_tcl']?.toString() ?? 'Analisis completado.';
    final afinidadStr = afinidad != null ? afinidad.toStringAsFixed(2) : '';

    // F-05: anomalias del quality_report (si el backend las incluye en el resultado)
    final anomalias = (resultado['anomaly_hints'] as List?) ?? [];

    Color estadoColor = Colors.amber;
    if (estado.toUpperCase().contains('ESTABILIDAD')) estadoColor = const Color(0xFF34D399);
    if (estado.toUpperCase().contains('TENSION')) estadoColor = Colors.amber;
    if (estado.toUpperCase().contains('FRICCION')) estadoColor = Colors.orange;
    if (estado.toUpperCase().contains('CRISIS')) estadoColor = Colors.red;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        title: const Text('Reporte de claridad', style: TextStyle(fontSize: 15)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [azulPrincipal, azulMedio], begin: Alignment.topLeft, end: Alignment.bottomRight),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [BoxShadow(color: azulPrincipal.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 4))],
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('RESULTADO DEL ANALISIS', style: TextStyle(fontSize: 10, color: Colors.white54, letterSpacing: 1.2)),
              const SizedBox(height: 6),
              Text(estado, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w500, color: Colors.white)),
              if (afinidadStr.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text('Afinidad: $afinidadStr${tensionHumana.isNotEmpty ? "  ·  Tension humana: $tensionHumana" : ""}',
                  style: const TextStyle(fontSize: 11, color: Colors.white60)),
              ],
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: estadoColor.withOpacity(0.2), borderRadius: BorderRadius.circular(20)),
                child: Text(estado, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w500, color: estadoColor)),
              ),
            ]),
          ),
          const SizedBox(height: 14),

          // F-05 PUNTO 3: Seccion de anomalias incidentes_mantenimiento y R
          if (anomalias.isNotEmpty) ...[
            _secLabel('Anomalias detectadas'),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: const Border(left: BorderSide(color: Color(0xFFF59E0B), width: 3)),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 4, offset: const Offset(0, 1))],
              ),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Container(width: 30, height: 30, decoration: BoxDecoration(color: const Color(0xFFFEF3C7), borderRadius: BorderRadius.circular(8)),
                    child: const Icon(Icons.warning_amber, size: 15, color: Color(0xFF92400e))),
                  const SizedBox(width: 8),
                  const Text('Quality Report · Outliers', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
                ]),
                const SizedBox(height: 10),
                const Divider(height: 1, color: Color(0xFFEEF2F7)),
                const SizedBox(height: 10),
                ...anomalias.map((a) {
                  final col = a['column']?.toString() ?? '';
                  final pct = ((a['outlier_pct'] as num?) ?? 0) * 100;
                  final lo = (a['lo'] as num?)?.toStringAsFixed(2) ?? '';
                  final hi = (a['hi'] as num?)?.toStringAsFixed(2) ?? '';
                  final esMantenimiento = col == 'incidentes_mantenimiento';
                  final esR = col == 'R';
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFFBF0),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFFFDE68A)),
                    ),
                    child: Row(children: [
                      Container(width: 36, height: 36, decoration: BoxDecoration(
                        color: esMantenimiento ? const Color(0xFFFEE2E2) : const Color(0xFFEDE9FE),
                        borderRadius: BorderRadius.circular(9)),
                        child: Icon(esMantenimiento ? Icons.build_circle : Icons.show_chart, size: 17,
                          color: esMantenimiento ? const Color(0xFF991b1b) : const Color(0xFF5b21b6))),
                      const SizedBox(width: 10),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(esMantenimiento ? 'incidentes_mantenimiento' : esR ? 'Indice R' : col,
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF1a2332))),
                        Text('${pct.toStringAsFixed(1)}% de valores fuera de rango normal [$lo – $hi]',
                          style: const TextStyle(fontSize: 11, color: Color(0xFF5a6a7a), height: 1.4)),
                      ])),
                    ]),
                  );
                }),
                const SizedBox(height: 4),
                const Text('Fuente: quality_report del ultimo cierre bimestral', style: TextStyle(fontSize: 10, color: Color(0xFF9BAAB8))),
              ]),
            ),
            const SizedBox(height: 8),
          ],

          _nivelCard(titulo: 'Nivel 1 - Ejecutivo', icon: Icons.bar_chart, iconColor: const Color(0xFF1e40af), iconBg: const Color(0xFFDBEAFE), contenido: narrativaEjecutiva, fallbackItems: tieneConector ? null : [resumenFallback]),
          const SizedBox(height: 8),
          if (nodos.isNotEmpty) ...[
            _secLabel('Nodos criticos'),
            ...nodos.map((nodo) {
              final nombreNodo = nodo['item_name']?.toString() ?? nodo['item_id']?.toString() ?? 'Nodo';
              final estadoNodo = nodo['state']?.toString() ?? '';
              final afinidadNodo = nodo['affinity'];
              final razon = nodo['reason']?.toString() ?? '';
              return Container(
                margin: const EdgeInsets.only(bottom: 7),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 3, offset: const Offset(0, 1))]),
                child: Row(children: [
                  Container(width: 8, height: 8, decoration: BoxDecoration(color: estadoNodo.toUpperCase().contains('FRICCION') ? Colors.orange : Colors.amber, shape: BoxShape.circle)),
                  const SizedBox(width: 8),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(nombreNodo, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
                    if (razon.isNotEmpty) Text(razon, style: const TextStyle(fontSize: 10, color: Color(0xFF9BAAB8))),
                  ])),
                  if (afinidadNodo != null) Text(afinidadNodo.toStringAsFixed(2), style: const TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
                ]),
              );
            }),
            const SizedBox(height: 8),
          ],
          _nivelCard(titulo: 'Nivel 2 - Operativo', icon: Icons.search, iconColor: const Color(0xFF92400e), iconBg: const Color(0xFFFEF3C7), contenido: narrativaOperativa, fallbackItems: tieneConector ? null : [resumenFallback]),
          const SizedBox(height: 8),
          if (acciones.isNotEmpty) ...[
            _secLabel('Acciones recomendadas'),
            ...acciones.asMap().entries.map((entry) {
              final i = entry.key + 1;
              final accion = entry.value;
              final desc = accion['description']?.toString() ?? '';
              return Container(
                margin: const EdgeInsets.only(bottom: 7),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: const Border(left: BorderSide(color: Color(0xFF34D399), width: 3))),
                child: Row(children: [
                  Container(width: 20, height: 20, decoration: BoxDecoration(color: const Color(0xFFD1FAE5), borderRadius: BorderRadius.circular(6)),
                    child: Center(child: Text('$i', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF065f46))))),
                  const SizedBox(width: 8),
                  Expanded(child: Text(desc, style: const TextStyle(fontSize: 12, color: Color(0xFF1a2332), height: 1.4))),
                ]),
              );
            }),
            const SizedBox(height: 8),
          ],
          if (bloqueos.isNotEmpty) ...[
            _secLabel('No hacer por ahora'),
            ...bloqueos.map((bloqueo) {
              final desc = bloqueo['description']?.toString() ?? '';
              final razon = bloqueo['reason']?.toString() ?? '';
              return Container(
                margin: const EdgeInsets.only(bottom: 7),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: const Border(left: BorderSide(color: Color(0xFFFCA5A5), width: 3))),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    const Icon(Icons.block, size: 14, color: Color(0xFF991b1b)),
                    const SizedBox(width: 6),
                    Expanded(child: Text(desc, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF991b1b)))),
                  ]),
                  if (razon.isNotEmpty) ...[const SizedBox(height: 4), Text(razon, style: const TextStyle(fontSize: 11, color: Color(0xFF5a6a7a), height: 1.4))],
                ]),
              );
            }),
            const SizedBox(height: 8),
          ],
          if (!tieneConector) ...[
            Container(
              decoration: BoxDecoration(color: const Color(0xFFEBF5FB), border: const Border(left: BorderSide(color: azulPrincipal, width: 3)), borderRadius: const BorderRadius.only(topRight: Radius.circular(12), bottomRight: Radius.circular(12))),
              padding: const EdgeInsets.all(14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('SUGERENCIA DEL SISTEMA', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: azulPrincipal, letterSpacing: 1)),
                const SizedBox(height: 6),
                Text(resumenFallback, style: const TextStyle(fontSize: 12, color: Color(0xFF0C447C), height: 1.6)),
              ]),
            ),
            const SizedBox(height: 14),
          ],
          if (esEmpresa) ...[
            _secLabel('Fase 2'),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: const Color(0xFFF0F4F8), borderRadius: BorderRadius.circular(14), border: Border.all(color: const Color(0xFFDDE4ED))),
              child: const Row(children: [
                Icon(Icons.account_tree_outlined, size: 18, color: Color(0xFF9BAAB8)),
                SizedBox(width: 12),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Visualizacion de nodos y conectores', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Color(0xFF9BAAB8))),
                  SizedBox(height: 3),
                  Text('Disponible en fase 2', style: TextStyle(fontSize: 10, color: Color(0xFFB8C9DC))),
                ])),
              ]),
            ),
            const SizedBox(height: 14),
          ],
          SizedBox(width: double.infinity,
            child: esEmpresa
              ? Container(padding: const EdgeInsets.symmetric(vertical: 14), decoration: BoxDecoration(color: const Color(0xFFEEF2F7), borderRadius: BorderRadius.circular(12)),
                  child: const Text('Decision - disponible en fase 2', textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: Color(0xFF9BAAB8))))
              : ElevatedButton.icon(
                  onPressed: () => Navigator.push(context, PageRouteBuilder(
                    pageBuilder: (_, a, __) => PantallaDecision(expedienteId: expedienteId),
                    transitionsBuilder: (_, a, __, child) => SlideTransition(position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)), child: child),
                  )),
                  icon: const Icon(Icons.check_circle_outline),
                  label: const Text('Registrar decision'),
                  style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 15), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)), elevation: 4),
                ),
          ),
          if (esEmpresa) const Padding(padding: EdgeInsets.only(top: 8), child: Center(child: Text('La pantalla de decision se activa en la segunda fase.', style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 11)))),
          const SizedBox(height: 16),
        ]),
      ),
    );
  }

  Widget _secLabel(String t) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Text(t.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
  );

  Widget _nivelCard({required String titulo, required IconData icon, required Color iconColor, required Color iconBg, String? contenido, List<String>? fallbackItems}) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, 1))]),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Container(width: 30, height: 30, decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(8)), child: Icon(icon, size: 15, color: iconColor)),
          const SizedBox(width: 8),
          Text(titulo, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
        ]),
        const SizedBox(height: 10),
        const Divider(height: 1, color: Color(0xFFEEF2F7)),
        const SizedBox(height: 10),
        if (contenido != null && contenido.isNotEmpty)
          Text(contenido.replaceAll(RegExp(r'#+\s'), '').replaceAll('**', '').replaceAll('- ', '- '), style: const TextStyle(fontSize: 11, color: Color(0xFF5a6a7a), height: 1.6))
        else if (fallbackItems != null)
          ...fallbackItems.map((item) => Padding(padding: const EdgeInsets.only(bottom: 5), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(width: 5, height: 5, margin: const EdgeInsets.only(top: 5, right: 8), decoration: const BoxDecoration(color: Color(0xFFB8CFDF), shape: BoxShape.circle)),
            Expanded(child: Text(item, style: const TextStyle(fontSize: 11, color: Color(0xFF5a6a7a), height: 1.5))),
          ]))),
      ]),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// PANTALLA 5 — Decision (sin cambios F-05)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaDecision extends StatefulWidget {
  final String expedienteId;
  const PantallaDecision({super.key, required this.expedienteId});
  @override
  State<PantallaDecision> createState() => _PantallaDecisionState();
}

class _PantallaDecisionState extends State<PantallaDecision> {
  String correccion = '';
  String observaciones = '';
  bool enviando = false;

  Future<void> registrar(String tipo) async {
    setState(() => enviando = true);
    try {
      await http.post(Uri.parse('$baseUrl/api/sincronizaciones/${widget.expedienteId}/decision'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'expediente_id': widget.expedienteId, 'sugerencia_tcl': 'Analisis completado. Accion recomendada basada en el reporte de claridad.', 'decision': tipo, 'accion_ejecutada': tipo, 'observaciones': observaciones.isNotEmpty ? observaciones : null}));
    } catch (e) {}
    if (mounted) {
      showDialog(context: context, builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(children: [Container(width: 32, height: 32, decoration: BoxDecoration(color: const Color(0xFFD1FAE5), borderRadius: BorderRadius.circular(8)), child: const Icon(Icons.check, color: Color(0xFF065f46), size: 18)), const SizedBox(width: 10), const Text('Decision registrada', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500))]),
        content: Text('Tu decision "$tipo" quedo guardada y mejorara el modelo en el proximo ajuste bimestral.', style: const TextStyle(fontSize: 13, color: Color(0xFF5a6a7a))),
        actions: [ElevatedButton(onPressed: () { Navigator.pop(ctx); Navigator.popUntil(context, (r) => r.isFirst); }, style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: const Text('Aceptar'))],
      ));
    }
    setState(() => enviando = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)), title: const Text('Decision', style: TextStyle(fontSize: 15))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            decoration: BoxDecoration(color: const Color(0xFFEBF5FB), border: const Border(left: BorderSide(color: azulPrincipal, width: 3)), borderRadius: const BorderRadius.only(topRight: Radius.circular(12), bottomRight: Radius.circular(12))),
            padding: const EdgeInsets.all(14),
            child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('SUGERENCIA DEL SISTEMA', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: azulPrincipal, letterSpacing: 1)),
              SizedBox(height: 6),
              Text('Accion recomendada basada en el reporte de claridad.', style: TextStyle(fontSize: 12, color: Color(0xFF0C447C), height: 1.6)),
            ]),
          ),
          const SizedBox(height: 24),
          const Text('QUE DECIDES?', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
          const SizedBox(height: 12),
          _opcionCard(icon: Icons.check_circle, iconColor: const Color(0xFF065f46), iconBg: const Color(0xFFD1FAE5), titulo: 'Aceptar sugerencia', sub: 'El sistema acerto', borderColor: const Color(0xFFD1FAE5), bgColor: const Color(0xFFF0FFF4), onTap: enviando ? null : () => registrar('confirmar')),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: const Color(0xFFFFFBF0), border: Border.all(color: const Color(0xFFFEF3C7)), borderRadius: BorderRadius.circular(14)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Row(children: [
                Icon(Icons.edit, color: Color(0xFF92400e), size: 18),
                SizedBox(width: 12),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Corregir', style: TextStyle(fontWeight: FontWeight.w500, color: Color(0xFF92400e), fontSize: 14)),
                  Text('Anota tu accion real', style: TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
                ]),
              ]),
              const SizedBox(height: 12),
              TextField(maxLines: 2, onChanged: (v) => setState(() => correccion = v),
                decoration: InputDecoration(hintText: 'Describe tu accion real...', hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)), labelText: 'Accion', border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)), focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF92400e))), filled: true, fillColor: Colors.white)),
              const SizedBox(height: 8),
              TextField(maxLines: 2, onChanged: (v) => setState(() => observaciones = v),
                decoration: InputDecoration(hintText: 'Observaciones adicionales...', hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)), labelText: 'Observaciones', border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)), focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF92400e))), filled: true, fillColor: Colors.white)),
              const SizedBox(height: 10),
              ElevatedButton(
                onPressed: correccion.isNotEmpty && !enviando ? () => registrar('corregir') : null,
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF92400e), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9))),
                child: const Text('Enviar correccion', style: TextStyle(fontSize: 12)),
              ),
            ]),
          ),
          const SizedBox(height: 24),
          const Center(child: Text('Tu decision mejora el modelo en el siguiente ajuste bimestral.', textAlign: TextAlign.center, style: TextStyle(color: Color(0xFF7B8FA1), fontSize: 11))),
          const SizedBox(height: 16),
        ]),
      ),
    );
  }

  Widget _opcionCard({required IconData icon, required Color iconColor, required Color iconBg, required String titulo, required String sub, required Color borderColor, required Color bgColor, VoidCallback? onTap}) {
    return Container(
      decoration: BoxDecoration(color: bgColor, border: Border.all(color: borderColor), borderRadius: BorderRadius.circular(14)),
      child: Material(color: Colors.transparent, borderRadius: BorderRadius.circular(14),
        child: InkWell(borderRadius: BorderRadius.circular(14), onTap: onTap,
          child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [
            Container(width: 38, height: 38, decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: iconColor, size: 20)),
            const SizedBox(width: 12),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(titulo, style: TextStyle(fontWeight: FontWeight.w500, color: iconColor, fontSize: 14)),
              Text(sub, style: const TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
            ]),
            const Spacer(),
            Icon(Icons.chevron_right, color: iconColor.withOpacity(0.5)),
          ])),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// F-05 PANTALLA 6 — Cierre Bimestral (puntos 1, 2, 4, 5)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaCierreBimestral extends StatefulWidget {
  final String dominio;
  const PantallaCierreBimestral({super.key, required this.dominio});
  @override
  State<PantallaCierreBimestral> createState() => _PantallaCierreBimestralState();
}

class _PantallaCierreBimestralState extends State<PantallaCierreBimestral> {
  // Pasos: 0=preparando, 1=schema question, 2=anomalias, 3=validador
  int paso = 0;
  bool cargando = false;
  String mensaje = '';

  // Datos del run
  String runId = '';
  String profile = '';
  String createdUtc = '';
  String retentionPolicy = '';
  List anomalias = [];
  List preguntas = [];
  Map validadorData = {};

  // Respuesta del schema
  final TextEditingController _respuestaCtrl = TextEditingController();

  // true cuando los datos mostrados NO vienen del backend (fallback demo)
  bool modoSimulado = false;
  // Archivos reales incluidos en el paquete bimestral (del backend)
  List archivosIncluidos = [];

  @override
  void initState() {
    super.initState();
    _prepararPaqueteAutomatico();
  }

  @override
  void dispose() { _respuestaCtrl.dispose(); super.dispose(); }

  // F-06: Preparacion automatica — el usuario no necesita hacer nada.
  // 1) POST preparar-paquete  → genera el ZIP y devuelve archivos reales.
  // 2) GET  ultimo-run        → anomalías y preguntas reales del Notebook.
  // Solo si el backend no responde se cae a datos simulados (con aviso).
  Future<void> _prepararPaqueteAutomatico() async {
    setState(() { cargando = true; mensaje = ''; modoSimulado = false; });
    try {
      final r = await http.post(
        Uri.parse('$baseUrl/api/bimestral/${widget.dominio}/preparar-paquete'),
      ).timeout(const Duration(seconds: 15));

      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        archivosIncluidos = data['archivos_incluidos'] ?? [];
        profile = data['dominio']?.toString() ?? widget.dominio;
        createdUtc = data['generado_at']?.toString() ?? DateTime.now().toUtc().toIso8601String();

        // Datos reales del último export_package del Notebook (si existe)
        try {
          final rRun = await http.get(
            Uri.parse('$baseUrl/api/bimestral/${widget.dominio}/ultimo-run'),
          ).timeout(const Duration(seconds: 10));
          if (rRun.statusCode == 200) {
            final run = jsonDecode(rRun.body);
            setState(() {
              runId = run['run_id']?.toString() ?? '';
              retentionPolicy = run['retention_policy']?.toString() ?? 'delete_after_export';
              anomalias = run['anomaly_hints'] ?? [];
              preguntas = run['minimal_questions'] ?? [];
              // Si el Notebook no dejó preguntas pendientes, saltar al paso 2
              paso = preguntas.isEmpty ? 2 : 1;
            });
          } else {
            // Backend vivo pero sin run registrado: paquete real, sin
            // anomalías/preguntas que revisar. Avanzar honestamente.
            setState(() {
              runId = '';
              retentionPolicy = 'delete_after_export';
              anomalias = [];
              preguntas = [];
              paso = 2;
              mensaje = 'Paquete real generado (${archivosIncluidos.length} archivos). Aún no hay export_package del Notebook para este dominio, por eso no se muestran anomalías ni preguntas.';
            });
          }
        } catch (e) {
          setState(() {
            runId = '';
            anomalias = [];
            preguntas = [];
            paso = 2;
            mensaje = 'Paquete real generado, pero no se pudo consultar el último run: $e';
          });
        }
      } else {
        _usarDatosSimulados('El backend respondió ${r.statusCode} al preparar el paquete.');
      }
    } catch (e) {
      _usarDatosSimulados('Sin conexión con el backend: $e');
    }
    setState(() => cargando = false);
  }

  void _usarDatosSimulados(String motivo) {
    setState(() {
      modoSimulado = true;
      mensaje = motivo;
      runId = 'f3d0866c-75cd-45e6-875f-c38c6e8a1d9c';
      profile = widget.dominio;
      createdUtc = DateTime.now().toUtc().toIso8601String();
      retentionPolicy = 'delete_after_export';
      anomalias = [
        {"column": "incidentes_mantenimiento", "outlier_pct": 0.099, "lo": -1.5, "hi": 2.5},
        {"column": "R", "outlier_pct": 0.073, "lo": 0.53, "hi": 1.22},
      ];
      preguntas = ["¿Existe alguna columna que sea un identificador estable (ID) para unir tablas?"];
      paso = 1;
    });
  }

  Future<void> _guardarRespuestaSchema() async {
    if (_respuestaCtrl.text.trim().isEmpty) {
      setState(() { mensaje = 'Por favor escribe una respuesta.'; });
      return;
    }
    setState(() { cargando = true; mensaje = ''; });
    try {
      await http.post(
        Uri.parse('$baseUrl/api/export-package/$runId/schema-answer'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'answer': _respuestaCtrl.text.trim()}),
      );
      setState(() => paso = 2);
    } catch (e) {
      // Si falla el endpoint, igual avanzamos (modo offline)
      setState(() => paso = 2);
    }
    setState(() => cargando = false);
  }

  Future<void> _generarValidador() async {
    setState(() { cargando = true; mensaje = ''; });
    try {
      final r = await http.post(
        Uri.parse('$baseUrl/api/bimestral/$profile/preparar-paquete'),
      ).timeout(const Duration(seconds: 5));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        setState(() {
          modoSimulado = false;
          validadorData = {
            "validador_id": "VAL-${runId.isNotEmpty ? runId.substring(0, 8).toUpperCase() : 'SINRUN00'}-${DateTime.now().toUtc().toIso8601String().substring(0, 10).replaceAll('-', '')}",
            "dominio": profile,
            "generado_at": DateTime.now().toUtc().toIso8601String(),
            "archivos_incluidos": data['archivos_incluidos'] ?? [],
            "total": data['total'] ?? 0,
            "listo_para_notebook": true,
            "mensaje": (data['total'] ?? 0) > 0
                ? "Paquete bimestral generado correctamente. Listo para ser procesado por el Notebook de ajuste."
                : "Paquete generado pero VACÍO: el servidor no encontró archivos del Aprendiz para '$profile'. Verifica que existan {dominio}_learning_log.jsonl, {dominio}_soft_dictionary_state.json y {dominio}_action_dictionary_state.json en la carpeta aprendiz_data/ junto al ejecutable.",
          };
          paso = 3;
        });
      } else {
        _usarValidadorSimulado('El backend respondió ${r.statusCode}.');
      }
    } catch (e) {
      _usarValidadorSimulado('Sin conexión con el backend: $e');
    }
    setState(() => cargando = false);
  }

  void _usarValidadorSimulado(String motivo) {
    final ahora = DateTime.now().toUtc().toIso8601String();
    final safeId = runId.isNotEmpty ? runId.substring(0, runId.length >= 8 ? 8 : runId.length).toUpperCase() : 'DEMO0000';
    final fechaCorta = ahora.substring(0, 10).replaceAll('-', '');
    setState(() {
      modoSimulado = true;
      mensaje = motivo;
      validadorData = {
        "validador_id": "VAL-$safeId-$fechaCorta",
        "dominio": profile,
        "generado_at": ahora,
        "archivos_incluidos": [
          "${profile}_learning_log.jsonl",
          "${profile}_soft_dictionary_state.json",
          "${profile}_action_dictionary_state.json",
        ],
        "total": 3,
        "listo_para_notebook": true,
        "mensaje": "Paquete bimestral generado correctamente. Listo para ser procesado por el Notebook de ajuste.",
      };
      paso = 3;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        title: const Text('Cierre Bimestral', style: TextStyle(fontSize: 15)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Indicador de pasos
          _indicadorPasos(),
          const SizedBox(height: 20),

          // Banner de modo simulado — visible en todos los pasos
          if (modoSimulado) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF7ED),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFF97316), width: 1.5),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.science_outlined, size: 18, color: Color(0xFFC2410C)),
                const SizedBox(width: 10),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('MODO SIMULADO', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFFC2410C), letterSpacing: 1)),
                  const SizedBox(height: 3),
                  Text(
                    mensaje.isNotEmpty ? mensaje : 'No se pudo contactar al backend; los datos mostrados son de demostración.',
                    style: const TextStyle(fontSize: 11, color: Color(0xFF9A3412), height: 1.4),
                  ),
                ])),
              ]),
            ),
          ],

          // Aviso informativo (backend real, pero con algo que saber)
          if (!modoSimulado && mensaje.isNotEmpty && paso == 2) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: const Color(0xFFEFF6FF),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFBFDBFE)),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.info_outline, size: 18, color: Color(0xFF1e40af)),
                const SizedBox(width: 10),
                Expanded(child: Text(mensaje, style: const TextStyle(fontSize: 11, color: Color(0xFF1e40af), height: 1.4))),
              ]),
            ),
          ],

          // PASO 0: Preparacion automatica del paquete bimestral
          if (paso == 0) ...[
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF5b21b6), Color(0xFF7C3AED)], begin: Alignment.topLeft, end: Alignment.bottomRight),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(children: [
                Container(width: 48, height: 48, decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                  child: const Icon(Icons.calendar_month, size: 24, color: Colors.white)),
                const SizedBox(width: 14),
                const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Cierre Bimestral', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                  SizedBox(height: 4),
                  Text('Preparando archivos para el Notebook...', style: TextStyle(color: Colors.white70, fontSize: 11)),
                ])),
              ]),
            ),
            const SizedBox(height: 40),
            Center(child: Column(children: [
              const CircularProgressIndicator(color: Color(0xFF5b21b6)),
              const SizedBox(height: 20),
              const Text('El sistema está preparando automáticamente', style: TextStyle(fontSize: 13, color: Color(0xFF1a2332))),
              const SizedBox(height: 4),
              const Text('los archivos del período bimestral.', style: TextStyle(fontSize: 13, color: Color(0xFF1a2332))),
              const SizedBox(height: 8),
              const Text('No es necesario hacer nada.', style: TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
            ])),
            if (mensaje.isNotEmpty) ...[
              const SizedBox(height: 20),
              Container(padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(10)),
                child: Text(mensaje, style: const TextStyle(color: Colors.red, fontSize: 12))),
            ],
          ],

          // PASO 1: Pregunta SchemaDraft
          if (paso == 1) ...[
            _encabezadoPaso(Icons.help_outline, const Color(0xFF1e40af), const Color(0xFFDBEAFE), 'Revision del esquema', 'El Notebook encontro una pregunta minima que requiere tu atencion antes del cierre.'),
            const SizedBox(height: 16),
            ...preguntas.asMap().entries.map((entry) {
              final i = entry.key + 1;
              final q = entry.value.toString();
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFEFF6FF),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFBFDBFE)),
                ),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Container(width: 22, height: 22, decoration: BoxDecoration(color: azulPrincipal, borderRadius: BorderRadius.circular(6)),
                    child: Center(child: Text('$i', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.white)))),
                  const SizedBox(width: 10),
                  Expanded(child: Text(q, style: const TextStyle(fontSize: 13, color: Color(0xFF1a2332), height: 1.5))),
                ]),
              );
            }),
            const SizedBox(height: 8),
            TextField(
              controller: _respuestaCtrl,
              maxLines: 3,
              decoration: InputDecoration(
                hintText: 'Escribe tu respuesta aqui...',
                hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E8F0))),
                focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: azulPrincipal)),
                filled: true, fillColor: Colors.white,
              ),
            ),
            const SizedBox(height: 8),
            if (mensaje.isNotEmpty) Padding(padding: const EdgeInsets.only(bottom: 8), child: Text(mensaje, style: const TextStyle(color: Colors.red, fontSize: 12))),
            SizedBox(width: double.infinity, child: ElevatedButton.icon(
              onPressed: cargando ? null : _guardarRespuestaSchema,
              icon: cargando ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.arrow_forward),
              label: const Text('Guardar y continuar'),
              style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
            )),
          ],

          // PASO 2: Anomalias + Destruccion
          if (paso == 2) ...[
            _encabezadoPaso(Icons.warning_amber, const Color(0xFF92400e), const Color(0xFFFEF3C7), 'Anomalias detectadas', 'El quality_report encontro valores atipicos en las siguientes columnas del periodo bimestral.'),
            const SizedBox(height: 16),
            ...anomalias.map((a) {
              final col = a['column']?.toString() ?? '';
              final pct = ((a['outlier_pct'] as num?) ?? 0) * 100;
              final lo = (a['lo'] as num?)?.toStringAsFixed(2) ?? '';
              final hi = (a['hi'] as num?)?.toStringAsFixed(2) ?? '';
              final esMantenimiento = col == 'incidentes_mantenimiento';
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFFDE68A)),
                  boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 3)],
                ),
                child: Row(children: [
                  Container(width: 40, height: 40, decoration: BoxDecoration(
                    color: esMantenimiento ? const Color(0xFFFEE2E2) : const Color(0xFFEDE9FE),
                    borderRadius: BorderRadius.circular(10)),
                    child: Icon(esMantenimiento ? Icons.build_circle : Icons.show_chart, size: 20,
                      color: esMantenimiento ? const Color(0xFF991b1b) : const Color(0xFF5b21b6))),
                  const SizedBox(width: 12),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(col, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF1a2332))),
                    const SizedBox(height: 2),
                    Text('${pct.toStringAsFixed(1)}% de valores fuera de rango', style: const TextStyle(fontSize: 11, color: Color(0xFF5a6a7a))),
                    Text('Rango normal: [$lo – $hi]', style: const TextStyle(fontSize: 10, color: Color(0xFF9BAAB8))),
                  ])),
                ]),
              );
            }),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFFFF7ED),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFFED7AA)),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.info_outline, size: 18, color: Color(0xFF92400e)),
                const SizedBox(width: 10),
                Expanded(child: Text('El sistema preparara automaticamente el paquete bimestral con todos los archivos del periodo para el Notebook de ajuste.', style: const TextStyle(fontSize: 12, color: Color(0xFF92400e), height: 1.5))),
              ]),
            ),
            const SizedBox(height: 16),
            SizedBox(width: double.infinity, child: ElevatedButton.icon(
              onPressed: cargando ? null : _generarValidador,
              icon: cargando ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.verified),
              label: const Text('Generar validador bimestral'),
              style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
            )),
          ],

          // PASO 3: Validador bimestral
          if (paso == 3) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFFDBEAFE),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: azulPrincipal, width: 2),
              ),
              child: Column(children: [
                Container(width: 56, height: 56, decoration: BoxDecoration(color: azulPrincipal, borderRadius: BorderRadius.circular(16)),
                  child: const Icon(Icons.task_alt, size: 30, color: Colors.white)),
                const SizedBox(height: 12),
                const Text('VALIDADOR BIMESTRAL', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF1e40af), letterSpacing: 1.2)),
                const SizedBox(height: 4),
                Text(validadorData['validador_id']?.toString() ?? '', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF1a2332))),
              ]),
            ),
            const SizedBox(height: 16),
            _reciboRow('Dominio', validadorData['dominio']?.toString() ?? ''),
            _reciboRow('Generado', _formatFecha(validadorData['generado_at']?.toString() ?? '')),
            _reciboRow('Para Notebook', validadorData['listo_para_notebook'] == true ? 'Listo ✓' : 'Pendiente'),
            const SizedBox(height: 12),
            if ((validadorData['archivos_incluidos'] as List?)?.isNotEmpty == true) ...[
              const Text('ARCHIVOS INCLUIDOS', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
              const SizedBox(height: 8),
              ...(validadorData['archivos_incluidos'] as List).map((f) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(children: [
                  const Icon(Icons.check_circle, size: 13, color: Color(0xFF34D399)),
                  const SizedBox(width: 6),
                  Text(f.toString(), style: const TextStyle(fontSize: 11, color: Color(0xFF5a6a7a))),
                ]),
              )),
              const SizedBox(height: 12),
            ],
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: const Color(0xFFEBF5FB), borderRadius: BorderRadius.circular(10), border: const Border(left: BorderSide(color: azulPrincipal, width: 3))),
              child: Text(validadorData['mensaje']?.toString() ?? '', style: const TextStyle(fontSize: 11, color: Color(0xFF0C447C), height: 1.5)),
            ),
            const SizedBox(height: 20),
            SizedBox(width: double.infinity, child: ElevatedButton.icon(
              onPressed: () => Navigator.pop(context),
              icon: const Icon(Icons.home),
              label: const Text('Volver al inicio'),
              style: ElevatedButton.styleFrom(backgroundColor: azulPrincipal, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 14), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
            )),
          ],
          const SizedBox(height: 24),
        ]),
      ),
    );
  }

  Widget _indicadorPasos() {
    final pasos = ['Prep.', 'Esquema', 'Anomalias', 'Validador'];
    return Row(children: pasos.asMap().entries.map((entry) {
      final i = entry.key;
      final label = entry.value;
      final activo = i == paso;
      final completado = i < paso;
      return Expanded(child: Row(children: [
        Expanded(child: Column(children: [
          Container(
            height: 3,
            color: completado ? const Color(0xFF34D399) : activo ? azulPrincipal : const Color(0xFFE0E8F0),
          ),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(fontSize: 9, fontWeight: activo ? FontWeight.w700 : FontWeight.w400, color: activo ? azulPrincipal : completado ? const Color(0xFF34D399) : const Color(0xFFB8C9DC))),
        ])),
      ]));
    }).toList());
  }

  Widget _encabezadoPaso(IconData icon, Color iconColor, Color iconBg, String titulo, String sub) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 4, offset: const Offset(0, 1))]),
      child: Row(children: [
        Container(width: 44, height: 44, decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(12)),
          child: Icon(icon, size: 22, color: iconColor)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(titulo, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xFF1a2332))),
          const SizedBox(height: 2),
          Text(sub, style: const TextStyle(fontSize: 11, color: Color(0xFF7B8FA1), height: 1.4)),
        ])),
      ]),
    );
  }

  Widget _reciboRow(String label, String valor) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Row(children: [
      SizedBox(width: 80, child: Text(label, style: const TextStyle(fontSize: 11, color: Color(0xFF7B8FA1)))),
      Expanded(child: Text(valor, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF1a2332)))),
    ]),
  );

  String _formatFecha(String iso) {
    if (iso.isEmpty) return '';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2,'0')}:${dt.minute.toString().padLeft(2,'0')}';
    } catch (_) { return iso.substring(0, 10); }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// F-05 PANTALLA 7 — Embudo del Aprendiz (punto 6)
// ═══════════════════════════════════════════════════════════════════════════════
class PantallaEmbudoAprendiz extends StatefulWidget {
  final String dominio;
  const PantallaEmbudoAprendiz({super.key, required this.dominio});
  @override
  State<PantallaEmbudoAprendiz> createState() => _PantallaEmbudoAprendizState();
}

class _PantallaEmbudoAprendizState extends State<PantallaEmbudoAprendiz> {
  List entradas = [];
  bool procesando = false;
  String mensaje = '';
  final TextEditingController _ctrl = TextEditingController();
  final TextEditingController _etiquetaCtrl = TextEditingController();
  String etiqueta = '';

  @override
  void dispose() { _ctrl.dispose(); _etiquetaCtrl.dispose(); super.dispose(); }

  // F-05: Lectura de QR (opcional)
  void _leerQR() {
    showDialog(context: context, builder: (ctx) => AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: Row(children: [
        Container(width: 32, height: 32, decoration: BoxDecoration(color: const Color(0xFFD1FAE5), borderRadius: BorderRadius.circular(8)),
          child: const Icon(Icons.qr_code_scanner, size: 18, color: Color(0xFF065f46))),
        const SizedBox(width: 10),
        const Text('Lector QR', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
      ]),
      content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('El equipo Mileforum esta definiendo si el QR es generado por el sistema o por fuente externa.', style: TextStyle(fontSize: 13, color: Color(0xFF5a6a7a), height: 1.5)),
        const SizedBox(height: 12),
        const Text('Por ahora puedes ingresar el contenido del QR manualmente:', style: TextStyle(fontSize: 12, color: Color(0xFF7B8FA1))),
        const SizedBox(height: 8),
        TextField(
          autofocus: true,
          decoration: InputDecoration(
            hintText: 'Pega aqui el contenido del QR...',
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF065f46))),
          ),
          onSubmitted: (v) {
            if (v.isNotEmpty) {
              Navigator.pop(ctx);
              setState(() {
                entradas.add({
                  'tipo': 'qr',
                  'label': 'QR · ${DateTime.now().toString().substring(0, 16)}',
                  'contenido': v,
                  'timestamp': DateTime.now().toString().substring(0, 16),
                });
              });
            }
          },
        ),
      ]),
      actions: [
        TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
      ],
    ));
  }

  void _agregarTexto() {
    if (_ctrl.text.trim().isEmpty) return;
    final tieneEtiqueta = etiqueta.trim().isNotEmpty;
    setState(() {
      entradas.add({
        'tipo': tieneEtiqueta ? 'evento' : 'nota',
        'label': tieneEtiqueta ? '[${etiqueta.trim()}] ${DateTime.now().toString().substring(0, 16)}' : 'Nota · ${DateTime.now().toString().substring(0, 16)}',
        'contenido': _ctrl.text.trim(),
        'etiqueta': etiqueta.trim(),
        'timestamp': DateTime.now().toString().substring(0, 16),
      });
      _ctrl.clear(); _etiquetaCtrl.clear(); etiqueta = '';
    });
  }

  Future<void> _procesar() async {
    if (entradas.isEmpty) return;
    setState(() { procesando = true; mensaje = ''; });
    try {
      // 1. Crear expediente para este embudo
      final rExp = await http.post(
        Uri.parse('$baseUrl/api/expedientes'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'nombre': 'Embudo ${widget.dominio} · ${DateTime.now().toString().substring(0, 16)}',
          'descripcion': 'Embudo Aprendiz unipersonal (${entradas.length} entradas)',
        }),
      ).timeout(const Duration(seconds: 10));
      if (rExp.statusCode != 200) {
        String detalle = 'HTTP ${rExp.statusCode}';
        try { detalle = jsonDecode(rExp.body)['detail']?.toString() ?? detalle; } catch (_) {}
        setState(() { mensaje = 'No se pudo crear el expediente: $detalle'; procesando = false; });
        return;
      }
      final expedienteId = jsonDecode(rExp.body)['id'].toString();

      // 2. Subir las entradas del embudo como documento de texto
      final contenido = entradas.map((e) =>
          '--- ${e['label']} ---\n${e['contenido']}').join('\n\n');
      final req = http.MultipartRequest('POST',
          Uri.parse('$baseUrl/api/expedientes/$expedienteId/documentos'));
      req.files.add(http.MultipartFile.fromBytes(
          'file', utf8.encode(contenido),
          filename: 'embudo_${DateTime.now().millisecondsSinceEpoch}.txt'));
      final up = await req.send().timeout(const Duration(seconds: 20));
      if (up.statusCode != 200) {
        setState(() { mensaje = 'No se pudieron subir las entradas (HTTP ${up.statusCode}).'; procesando = false; });
        return;
      }

      // 3. Procesar con el Motor Aprendiz (unipersonal → ejecutar_episodio)
      final rProc = await http.post(
        Uri.parse('$baseUrl/api/expedientes/$expedienteId/procesar'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'tipo_consulta': 'analisis'}),
      ).timeout(const Duration(seconds: 120));

      if (rProc.statusCode == 200) {
        final resultado = jsonDecode(rProc.body);
        setState(() { mensaje = 'Embudo procesado por el Motor Aprendiz.'; entradas = []; });
        if (mounted) {
          Navigator.push(context, PageRouteBuilder(
            pageBuilder: (_, a, __) => PantallaReporteClaridad(resultado: resultado, expedienteId: expedienteId, esEmpresa: false),
            transitionsBuilder: (_, a, __, child) => SlideTransition(position: Tween<Offset>(begin: const Offset(1, 0), end: Offset.zero).animate(CurvedAnimation(parent: a, curve: Curves.easeInOut)), child: child),
          ));
        }
      } else {
        // Mostrar el error REAL del backend: si aprendiz_motor no está
        // disponible (p. ej. no quedó empaquetado en el .exe, o no encuentra
        // sus modelos), aquí aparecerá el ImportError o traceback resumido.
        String detalle = 'HTTP ${rProc.statusCode}';
        try { detalle = jsonDecode(rProc.body)['detail']?.toString() ?? rProc.body; } catch (_) { detalle = rProc.body; }
        setState(() { mensaje = 'El motor no pudo procesar: $detalle'; });
      }
    } on TimeoutException {
      setState(() { mensaje = 'El motor tardó demasiado en responder (timeout). Puede estar cargando los modelos; reintenta.'; });
    } catch (e) {
      setState(() { mensaje = 'Sin conexion al servidor: $e'; });
    }
    setState(() => procesando = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        title: Text('Embudo Aprendiz · ${widget.dominio}', style: const TextStyle(fontSize: 14)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Header verde (unipersonal)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF065f46), Color(0xFF059669)], begin: Alignment.topLeft, end: Alignment.bottomRight),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(children: [
              Container(width: 48, height: 48, decoration: BoxDecoration(color: Colors.white.withOpacity(0.15), borderRadius: BorderRadius.circular(12)),
                child: const Icon(Icons.school, size: 24, color: Colors.white)),
              const SizedBox(width: 14),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Motor Aprendiz', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500)),
                const SizedBox(height: 4),
                Text('Embudo para profesional unipersonal · ${widget.dominio}', style: const TextStyle(color: Colors.white70, fontSize: 11)),
              ])),
            ]),
          ),
          const SizedBox(height: 16),

          // Boton QR
          GestureDetector(
            onTap: _leerQR,
            child: Container(
              width: double.infinity, padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF6EE7B7), width: 1.5),
                boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 3)],
              ),
              child: Row(children: [
                Container(width: 36, height: 36, decoration: BoxDecoration(color: const Color(0xFFD1FAE5), borderRadius: BorderRadius.circular(9)),
                  child: const Icon(Icons.qr_code_scanner, size: 18, color: Color(0xFF065f46))),
                const SizedBox(width: 12),
                const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Leer QR', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Color(0xFF1a2332))),
                  Text('Ingesta rapida desde codigo QR (opcional)', style: TextStyle(fontSize: 11, color: Color(0xFF7B8FA1))),
                ])),
                const Icon(Icons.chevron_right, color: Color(0xFF6EE7B7)),
              ]),
            ),
          ),
          const SizedBox(height: 14),

          // Lista de entradas
          if (entradas.isNotEmpty) ...[
            _secLabel('En el embudo (${entradas.length})'),
            ...entradas.asMap().entries.map((entry) {
              final idx = entry.key;
              final e = entry.value;
              final esQR = e['tipo'] == 'qr';
              final esEvento = e['tipo'] == 'evento';
              final iconData = esQR ? Icons.qr_code : esEvento ? Icons.bolt : Icons.notes;
              final iconColor = esQR ? const Color(0xFF065f46) : esEvento ? const Color(0xFF1e40af) : const Color(0xFF92400e);
              final iconBg = esQR ? const Color(0xFFD1FAE5) : esEvento ? const Color(0xFFDBEAFE) : const Color(0xFFFEF3C7);
              return Container(
                margin: const EdgeInsets.only(bottom: 7),
                padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 10),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 3)]),
                child: Row(children: [
                  Container(width: 32, height: 32, decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(8)), child: Icon(iconData, size: 15, color: iconColor)),
                  const SizedBox(width: 10),
                  Expanded(child: Text(e['label']?.toString() ?? '', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF1a2332)))),
                  GestureDetector(
                    onTap: () => setState(() => entradas.removeAt(idx)),
                    child: Container(width: 26, height: 26, decoration: BoxDecoration(color: const Color(0xFFFEE2E2), borderRadius: BorderRadius.circular(6)), child: const Icon(Icons.close, size: 13, color: Color(0xFF991b1b))),
                  ),
                ]),
              );
            }),
            const SizedBox(height: 8),
          ],

          _secLabel('Escritura libre'),
          TextField(
            controller: _ctrl, maxLines: 3,
            decoration: InputDecoration(
              hintText: 'Notas, observaciones, registros...',
              hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E8F0))),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF065f46))),
              filled: true, fillColor: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _etiquetaCtrl,
            decoration: InputDecoration(
              hintText: 'Etiqueta (opcional)',
              hintStyle: const TextStyle(fontSize: 12, color: Color(0xFF7B8FA1)),
              helperText: 'Con etiqueta se ingesta como evento.',
              helperStyle: const TextStyle(fontSize: 10, color: Color(0xFF9BAAB8)),
              prefixIcon: const Icon(Icons.label_outline, size: 16, color: Color(0xFF7B8FA1)),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E8F0))),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF065f46))),
              filled: true, fillColor: Colors.white,
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            ),
            onChanged: (v) => setState(() => etiqueta = v),
          ),
          const SizedBox(height: 8),
          Align(alignment: Alignment.centerRight,
            child: OutlinedButton.icon(
              onPressed: _ctrl.text.isNotEmpty ? _agregarTexto : null,
              icon: const Icon(Icons.add, size: 16),
              label: const Text('Agregar', style: TextStyle(fontSize: 12)),
              style: OutlinedButton.styleFrom(foregroundColor: const Color(0xFF065f46), side: const BorderSide(color: Color(0xFF6EE7B7)), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9))),
            ),
          ),
          const SizedBox(height: 16),
          if (mensaje.isNotEmpty)
            Container(margin: const EdgeInsets.only(bottom: 12), padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: const Color(0xFFD1FAE5), borderRadius: BorderRadius.circular(10)),
              child: Row(children: [
                const Icon(Icons.check_circle, size: 16, color: Color(0xFF065f46)),
                const SizedBox(width: 8),
                Expanded(child: Text(mensaje, style: const TextStyle(color: Color(0xFF065f46), fontSize: 12))),
              ])),
          SizedBox(width: double.infinity, child: ElevatedButton.icon(
            onPressed: entradas.isEmpty ? null : (procesando ? null : _procesar),
            icon: procesando ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.psychology),
            label: Text(procesando ? 'Procesando...' : 'Procesar con Motor Aprendiz'),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF065f46), foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 15),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 4,
            ),
          )),
          const SizedBox(height: 16),
        ]),
      ),
    );
  }

  Widget _secLabel(String t) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Text(t.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: Color(0xFF8896A5), letterSpacing: 1.2)),
  );
}

import 'package:flutter/material.dart';

import '../features/venues/data/services/venue_api_client.dart';
import '../features/venues/presentation/screens/venue_list_screen.dart';
import 'theme/app_theme.dart';

/// Widget principal de ClubMatiasMegiasNavarro.
///
/// Este widget centraliza la configuracion global de MaterialApp,
/// incluyendo el nombre, los temas visuales y la pantalla inicial.
class ClubApp extends StatelessWidget {
  const ClubApp({super.key, this.venueApiClient});

  /// Cliente opcional utilizado por la pantalla de sedes.
  ///
  /// Durante la ejecucion normal se utiliza el cliente real. Las pruebas
  /// pueden inyectar un cliente simulado para evitar solicitudes reales.
  final VenueApiClient? venueApiClient;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      // Oculta la etiqueta DEBUG que Flutter muestra durante el desarrollo.
      debugShowCheckedModeBanner: false,

      // Nombre utilizado por el sistema operativo y algunas herramientas.
      title: 'ClubMatiasMegiasNavarro',

      // Configuraciones visuales para los modos claro y oscuro.
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,

      // Utiliza automaticamente el tema configurado en el dispositivo.
      themeMode: ThemeMode.system,

      // Muestra el listado de sedes como flujo inicial de la aplicacion.
      home: VenueListScreen(apiClient: venueApiClient),
    );
  }
}

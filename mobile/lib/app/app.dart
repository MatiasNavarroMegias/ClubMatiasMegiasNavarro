import 'package:flutter/material.dart';

import '../features/auth/data/services/auth_api_client.dart';
import '../features/auth/data/services/session_storage.dart';
import '../features/auth/presentation/controllers/auth_controller.dart';
import '../features/auth/presentation/screens/session_gate.dart';
import '../features/venues/data/services/venue_api_client.dart';
import 'theme/app_theme.dart';

/// Widget principal de ClubMatiasMegiasNavarro.
///
/// Este widget centraliza el tema y construye las dependencias que
/// administran la autenticacion durante toda la aplicacion.
class ClubApp extends StatefulWidget {
  const ClubApp({super.key, this.authController, this.venueApiClient});

  /// Controlador opcional utilizado durante las pruebas.
  ///
  /// En una ejecucion normal, ClubApp construye un controlador con el
  /// cliente HTTP real y el almacenamiento seguro del dispositivo.
  final AuthController? authController;

  /// Cliente opcional utilizado por la pantalla de sedes.
  final VenueApiClient? venueApiClient;

  @override
  State<ClubApp> createState() => _ClubAppState();
}

class _ClubAppState extends State<ClubApp> {
  late final AuthController _authController;
  late final bool _ownsAuthController;

  @override
  void initState() {
    super.initState();

    _ownsAuthController = widget.authController == null;
    _authController =
        widget.authController ??
        AuthController(
          apiClient: AuthApiClient(),
          sessionStorage: SecureSessionStorage(),
        );
  }

  @override
  void dispose() {
    if (_ownsAuthController) {
      _authController.dispose();
    }

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'ClubMatiasMegiasNavarro',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      home: SessionGate(
        authController: _authController,
        venueApiClient: widget.venueApiClient,
      ),
    );
  }
}

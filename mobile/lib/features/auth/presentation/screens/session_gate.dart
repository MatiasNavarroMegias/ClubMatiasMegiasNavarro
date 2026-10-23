import 'package:flutter/material.dart';

import '../../../venues/data/services/venue_api_client.dart';
import '../controllers/auth_controller.dart';
import 'home_screen.dart';
import 'login_screen.dart';
import 'registration_screen.dart';

/// Decide que pantalla debe mostrarse segun el estado de la sesion.
///
/// Al iniciar la aplicacion, AuthController comprueba si existe un JWT
/// almacenado y consulta el perfil para validar la sesion.
class SessionGate extends StatefulWidget {
  const SessionGate({
    required this.authController,
    this.venueApiClient,
    super.key,
  });

  final AuthController authController;
  final VenueApiClient? venueApiClient;

  @override
  State<SessionGate> createState() => _SessionGateState();
}

class _SessionGateState extends State<SessionGate> {
  bool _showRegistration = false;

  @override
  void initState() {
    super.initState();

    widget.authController.addListener(_handleControllerChange);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      widget.authController.initialize();
    });
  }

  @override
  void didUpdateWidget(covariant SessionGate oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.authController == widget.authController) {
      return;
    }

    oldWidget.authController.removeListener(_handleControllerChange);
    widget.authController.addListener(_handleControllerChange);
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleControllerChange);

    super.dispose();
  }

  void _handleControllerChange() {
    if (!mounted) {
      return;
    }

    setState(() {
      if (widget.authController.status == AuthStatus.authenticated) {
        _showRegistration = false;
      }
    });
  }

  void _openRegistration() {
    widget.authController.clearError();

    setState(() {
      _showRegistration = true;
    });
  }

  void _openLogin() {
    widget.authController.clearError();

    setState(() {
      _showRegistration = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return switch (widget.authController.status) {
      AuthStatus.initializing => const _SessionLoadingView(),
      AuthStatus.authenticated => HomeScreen(
        authController: widget.authController,
        venueApiClient: widget.venueApiClient,
      ),
      AuthStatus.unauthenticated || AuthStatus.loading =>
        _showRegistration
            ? RegistrationScreen(
                authController: widget.authController,
                onShowLogin: _openLogin,
              )
            : LoginScreen(
                authController: widget.authController,
                onShowRegistration: _openRegistration,
              ),
    };
  }
}

/// Muestra un estado neutro mientras se restaura la sesion.
class _SessionLoadingView extends StatelessWidget {
  const _SessionLoadingView();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        key: Key('session-initializing'),
        child: CircularProgressIndicator(),
      ),
    );
  }
}

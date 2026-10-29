import 'package:flutter/material.dart';

import '../../../reservations/data/services/reservation_api_client.dart';
import '../../../reservations/presentation/screens/upcoming_reservations_screen.dart';
import '../../../venues/data/services/venue_api_client.dart';
import '../../../venues/presentation/screens/venue_list_screen.dart';
import '../controllers/auth_controller.dart';
import 'home_screen.dart';
import 'profile_screen.dart';

/// Secciones principales disponibles para el usuario autenticado.
enum AuthenticatedSection { home, venues, reservations, profile }

/// Mantiene la navegacion principal visible durante toda la sesion.
///
/// IndexedStack conserva el estado interno de cada pantalla cuando
/// el usuario cambia entre Inicio, Sedes, Reservas y Perfil.
class AuthenticatedShell extends StatefulWidget {
  const AuthenticatedShell({
    required this.authController,
    this.venueApiClient,
    this.reservationApiClient,
    super.key,
  });

  /// Controlador que contiene la sesion y el usuario autenticado.
  final AuthController authController;

  /// Cliente opcional utilizado para consultar las sedes.
  ///
  /// Durante las pruebas puede reemplazarse por un cliente simulado.
  final VenueApiClient? venueApiClient;

  /// Cliente opcional utilizado por el flujo de reservas.
  ///
  /// Permite utilizar un cliente HTTP simulado durante las pruebas.
  final ReservationApiClient? reservationApiClient;

  @override
  State<AuthenticatedShell> createState() => _AuthenticatedShellState();
}

class _AuthenticatedShellState extends State<AuthenticatedShell> {
  AuthenticatedSection _selectedSection = AuthenticatedSection.home;

  /// Cambia la seccion visible sin crear una ruta nueva.
  void _selectSection(AuthenticatedSection section) {
    if (_selectedSection == section) {
      return;
    }

    setState(() {
      _selectedSection = section;
    });
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final selectedIndex = _selectedSection.index;

    return Scaffold(
      // Define un fondo uniforme para evitar contornos o colores
      // residuales alrededor del contenido principal.
      backgroundColor: colorScheme.surface,

      // IndexedStack conserva el estado de las pantallas.
      body: IndexedStack(
        index: selectedIndex,
        children: [
          HomeScreen(
            authController: widget.authController,
            onOpenVenues: () {
              _selectSection(AuthenticatedSection.venues);
            },
            onOpenReservations: () {
              _selectSection(AuthenticatedSection.reservations);
            },
            onOpenProfile: () {
              _selectSection(AuthenticatedSection.profile);
            },
          ),
          VenueListScreen(
            apiClient: widget.venueApiClient,
            accessToken: widget.authController.accessToken,
          ),
          _BuildReservationsSection(
            accessToken: widget.authController.accessToken,
            apiClient: widget.reservationApiClient,
          ),
          ProfileScreen(authController: widget.authController),
        ],
      ),

      // La barra se separa de los bordes para producir un efecto
      // flotante similar al diseño definido en Figma.
      bottomNavigationBar: SafeArea(
        top: false,
        minimum: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: colorScheme.surfaceContainer,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.30),
                blurRadius: 22,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: NavigationBar(
              key: const Key('authenticated-bottom-navigation'),

              // El fondo transparente permite utilizar el color del
              // contenedor exterior sin agregar bordes adicionales.
              backgroundColor: Colors.transparent,
              surfaceTintColor: Colors.transparent,
              shadowColor: Colors.transparent,
              elevation: 0,
              height: 70,

              // El verde queda reservado para el destino seleccionado,
              // evitando utilizarlo como borde de toda la pantalla.
              indicatorColor: colorScheme.primary.withValues(alpha: 0.22),

              selectedIndex: selectedIndex,
              onDestinationSelected: (index) {
                _selectSection(AuthenticatedSection.values[index]);
              },
              destinations: const [
                NavigationDestination(
                  key: Key('navigation-home'),
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home),
                  label: 'Inicio',
                ),
                NavigationDestination(
                  key: Key('navigation-venues'),
                  icon: Icon(Icons.location_city_outlined),
                  selectedIcon: Icon(Icons.location_city),
                  label: 'Sedes',
                ),
                NavigationDestination(
                  key: Key('navigation-reservations'),
                  icon: Icon(Icons.calendar_month_outlined),
                  selectedIcon: Icon(Icons.calendar_month),
                  label: 'Reservas',
                ),
                NavigationDestination(
                  key: Key('navigation-profile'),
                  icon: Icon(Icons.person_outline),
                  selectedIcon: Icon(Icons.person),
                  label: 'Perfil',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Construye la seccion de reservas utilizando la sesion actual.
class _BuildReservationsSection extends StatelessWidget {
  const _BuildReservationsSection({
    required this.accessToken,
    required this.apiClient,
  });

  final String? accessToken;
  final ReservationApiClient? apiClient;

  @override
  Widget build(BuildContext context) {
    final token = accessToken;

    if (token == null || token.trim().isEmpty) {
      return const _ReservationsSessionUnavailableView();
    }

    return UpcomingReservationsScreen(accessToken: token, apiClient: apiClient);
  }
}

/// Muestra un estado seguro cuando la sesion no contiene un token.
class _ReservationsSessionUnavailableView extends StatelessWidget {
  const _ReservationsSessionUnavailableView();

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Mis reservas'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: Center(
        key: const Key('reservations-session-unavailable'),
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.lock_outline, size: 64, color: colorScheme.error),
              const SizedBox(height: 16),
              Text(
                'La sesion no se encuentra disponible',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'Cerra la sesion e inicia nuevamente '
                'para consultar tus reservas.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

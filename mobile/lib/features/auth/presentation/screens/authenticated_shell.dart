import 'package:flutter/material.dart';

import '../../../venues/data/services/venue_api_client.dart';
import '../../../venues/presentation/screens/venue_list_screen.dart';
import '../controllers/auth_controller.dart';
import 'home_screen.dart';

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
    super.key,
  });

  /// Controlador que contiene la sesion y el usuario autenticado.
  final AuthController authController;

  /// Cliente opcional utilizado para consultar las sedes.
  ///
  /// Durante las pruebas puede reemplazarse por un cliente simulado.
  final VenueApiClient? venueApiClient;

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
          VenueListScreen(apiClient: widget.venueApiClient),
          const _ReservationsPlaceholder(),
          _ProfilePlaceholder(authController: widget.authController),
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

/// Pantalla temporal hasta implementar la gestion de reservas.
class _ReservationsPlaceholder extends StatelessWidget {
  const _ReservationsPlaceholder();

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
        key: const Key('reservations-placeholder'),
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              elevation: 0,
              color: colorScheme.surfaceContainer,
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DecoratedBox(
                      decoration: BoxDecoration(
                        color: colorScheme.primary.withValues(alpha: 0.14),
                        shape: BoxShape.circle,
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(18),
                        child: Icon(
                          Icons.calendar_month_outlined,
                          size: 42,
                          color: colorScheme.primary,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'Todavia no tenes reservas',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleLarge
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Tus proximas reservas apareceran '
                      'en esta seccion.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Pantalla temporal del perfil.
///
/// En el siguiente bloque sera reemplazada por el formulario real
/// conectado con GET y PATCH /users/me.
class _ProfilePlaceholder extends StatelessWidget {
  const _ProfilePlaceholder({required this.authController});

  final AuthController authController;

  @override
  Widget build(BuildContext context) {
    final user = authController.currentUser;
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Mi perfil'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: ListView(
        key: const Key('profile-placeholder'),
        padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
        children: [
          Center(
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: colorScheme.primary.withValues(alpha: 0.18),
                shape: BoxShape.circle,
              ),
              child: SizedBox.square(
                dimension: 94,
                child: Center(
                  child: Text(
                    _profileInitials(user?.firstName, user?.lastName),
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: colorScheme.primary,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            user?.fullName ?? 'Usuario',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Text(
            user?.email ?? '',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge
                ?.copyWith(color: colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 32),
          Card(
            elevation: 0,
            color: colorScheme.surfaceContainer,
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: [
                  _ProfileInformationRow(
                    icon: Icons.badge_outlined,
                    label: 'Nombre completo',
                    value: user?.fullName ?? '-',
                  ),
                  const Divider(height: 28),
                  _ProfileInformationRow(
                    icon: Icons.email_outlined,
                    label: 'Correo electronico',
                    value: user?.email ?? '-',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          FilledButton.icon(
            key: const Key('profile-edit-pending'),
            onPressed: null,
            icon: const Icon(Icons.edit_outlined),
            label: const Text('Editar perfil'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            key: const Key('profile-logout'),
            onPressed: authController.isLoading ? null : authController.logout,
            icon: const Icon(Icons.logout),
            label: const Text('Cerrar sesion'),
          ),
        ],
      ),
    );
  }

  /// Genera las iniciales visibles en el avatar.
  String _profileInitials(String? firstName, String? lastName) {
    final firstInitial = firstName == null || firstName.isEmpty
        ? ''
        : firstName[0];

    final lastInitial = lastName == null || lastName.isEmpty ? '' : lastName[0];

    final initials = '$firstInitial$lastInitial'.toUpperCase();

    return initials.isEmpty ? '?' : initials;
  }
}

/// Muestra un dato publico del perfil.
class _ProfileInformationRow extends StatelessWidget {
  const _ProfileInformationRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: colorScheme.primary),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.labelMedium
                    ?.copyWith(color: colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: Theme.of(context).textTheme.bodyLarge
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

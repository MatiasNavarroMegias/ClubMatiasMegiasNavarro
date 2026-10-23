import 'package:flutter/material.dart';

import '../../../venues/data/services/venue_api_client.dart';
import '../../../venues/presentation/screens/venue_list_screen.dart';
import '../controllers/auth_controller.dart';

/// Muestra la pagina principal del usuario autenticado.
///
/// La pantalla funciona como punto de entrada hacia sedes, reservas,
/// historial y perfil. Los modulos pendientes se habilitaran durante
/// las siguientes etapas del proyecto.
class HomeScreen extends StatelessWidget {
  const HomeScreen({
    required this.authController,
    this.venueApiClient,
    super.key,
  });

  /// Controlador que contiene el usuario y administra el cierre de sesion.
  final AuthController authController;

  /// Cliente opcional utilizado por la pantalla de sedes.
  final VenueApiClient? venueApiClient;

  /// Abre el listado de sedes disponibles.
  void _openVenues(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) {
          return VenueListScreen(apiClient: venueApiClient);
        },
      ),
    );
  }

  /// Muestra temporalmente un mensaje para un modulo pendiente.
  void _showPendingFeature(BuildContext context, String featureName) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text('$featureName se agregara en la siguiente etapa.'),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final user = authController.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inicio'),
        actions: [
          IconButton(
            key: const Key('home-logout'),
            onPressed: authController.isLoading ? null : authController.logout,
            tooltip: 'Cerrar sesion',
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          key: const Key('authenticated-home'),
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              user == null ? 'Bienvenido' : 'Hola, ${user.firstName}',
              style: Theme.of(context).textTheme.headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Text(
              'Selecciona una opcion para continuar.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            _HomeOptionCard(
              key: const Key('home-venues'),
              icon: Icons.location_city_outlined,
              title: 'Seleccionar sede',
              description: 'Consulta las sedes disponibles del club.',
              onTap: () => _openVenues(context),
            ),
            const SizedBox(height: 12),
            _HomeOptionCard(
              key: const Key('home-reservations'),
              icon: Icons.calendar_month_outlined,
              title: 'Mis reservas',
              description: 'Consulta y administra tus proximas reservas.',
              onTap: () {
                _showPendingFeature(context, 'Mis reservas');
              },
            ),
            const SizedBox(height: 12),
            _HomeOptionCard(
              key: const Key('home-history'),
              icon: Icons.history,
              title: 'Historial',
              description: 'Consulta las reservas anteriores y canceladas.',
              onTap: () {
                _showPendingFeature(context, 'Historial');
              },
            ),
            const SizedBox(height: 12),
            _HomeOptionCard(
              key: const Key('home-profile'),
              icon: Icons.person_outline,
              title: 'Mi perfil',
              description: 'Consulta y modifica tus datos personales.',
              onTap: () {
                _showPendingFeature(context, 'Mi perfil');
              },
            ),
          ],
        ),
      ),
    );
  }
}

/// Representa una opcion disponible dentro de la pagina principal.
class _HomeOptionCard extends StatelessWidget {
  const _HomeOptionCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.onTap,
    super.key,
  });

  final IconData icon;
  final String title;
  final String description;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  color: colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Icon(icon, color: colorScheme.onPrimaryContainer),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      description,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(Icons.chevron_right, color: colorScheme.primary),
            ],
          ),
        ),
      ),
    );
  }
}

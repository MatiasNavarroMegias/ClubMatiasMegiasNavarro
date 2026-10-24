import 'package:flutter/material.dart';

import '../controllers/auth_controller.dart';

/// Muestra la pagina inicial del usuario autenticado.
///
/// La pantalla presenta un encabezado deportivo, el estado de la
/// proxima reserva, filtros visuales y accesos a las secciones
/// principales de la aplicacion.
///
/// La navegacion se delega a AuthenticatedShell para mantener visible
/// la barra inferior y conservar el estado de cada seccion.
class HomeScreen extends StatelessWidget {
  const HomeScreen({
    required this.authController,
    required this.onOpenVenues,
    required this.onOpenReservations,
    required this.onOpenProfile,
    super.key,
  });

  /// Controlador que contiene la informacion del usuario autenticado.
  final AuthController authController;

  /// Accion utilizada para seleccionar la seccion de sedes.
  final VoidCallback onOpenVenues;

  /// Accion utilizada para seleccionar la seccion de reservas.
  final VoidCallback onOpenReservations;

  /// Accion utilizada para seleccionar la seccion de perfil.
  final VoidCallback onOpenProfile;

  /// Muestra temporalmente el estado pendiente del historial.
  void _showHistoryPending(BuildContext context) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        const SnackBar(
          content: Text(
            'El historial se habilitara con el modulo de reservas.',
          ),
        ),
      );
  }

  /// Informa que las notificaciones se agregaran posteriormente.
  void _showNotificationsPending(BuildContext context) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        const SnackBar(
          content: Text('Las notificaciones se habilitaran proximamente.'),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final user = authController.currentUser;
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      body: SafeArea(
        child: CustomScrollView(
          key: const Key('authenticated-home'),
          slivers: [
            SliverAppBar(
              floating: true,
              snap: true,
              backgroundColor: colorScheme.surface,
              surfaceTintColor: Colors.transparent,
              title: const Text('Club Deportivo'),
              actions: [
                IconButton(
                  key: const Key('home-notifications'),
                  onPressed: () {
                    _showNotificationsPending(context);
                  },
                  tooltip: 'Notificaciones',
                  icon: const Icon(Icons.notifications_none_outlined),
                ),
                const SizedBox(width: 8),
              ],
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              sliver: SliverList(
                delegate: SliverChildListDelegate([
                  _SportsHeader(firstName: user?.firstName),
                  const SizedBox(height: 26),
                  _SectionHeader(title: 'Proxima reserva'),
                  const SizedBox(height: 12),
                  _EmptyNextReservationCard(onExploreVenues: onOpenVenues),
                  const SizedBox(height: 30),
                  _SectionHeader(
                    title: 'Explora el club',
                    actionLabel: 'Ver sedes',
                    onActionPressed: onOpenVenues,
                  ),
                  const SizedBox(height: 14),
                  const _SportFilterChips(),
                  const SizedBox(height: 22),
                  _HomeOptionCard(
                    key: const Key('home-venues'),
                    icon: Icons.location_city_outlined,
                    title: 'Seleccionar sede',
                    description: 'Consulta las sedes disponibles del club.',
                    accentColor: colorScheme.primary,
                    onTap: onOpenVenues,
                  ),
                  const SizedBox(height: 12),
                  _HomeOptionCard(
                    key: const Key('home-reservations'),
                    icon: Icons.calendar_month_outlined,
                    title: 'Mis reservas',
                    description: 'Consulta y administra tus proximas reservas.',
                    accentColor: colorScheme.secondary,
                    onTap: onOpenReservations,
                  ),
                  const SizedBox(height: 12),
                  _HomeOptionCard(
                    key: const Key('home-history'),
                    icon: Icons.history,
                    title: 'Historial',
                    description: 'Consulta reservas anteriores y canceladas.',
                    accentColor: colorScheme.tertiary,
                    onTap: () {
                      _showHistoryPending(context);
                    },
                  ),
                  const SizedBox(height: 12),
                  _HomeOptionCard(
                    key: const Key('home-profile'),
                    icon: Icons.person_outline,
                    title: 'Mi perfil',
                    description: 'Consulta y modifica tus datos personales.',
                    accentColor: colorScheme.primary,
                    onTap: onOpenProfile,
                  ),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Encabezado principal con una imagen deportiva configurable.
///
/// La imagen se carga desde:
///
/// assets/images/home_banner.jpg
///
/// Si Flutter no puede encontrar o decodificar la imagen, se muestra
/// automaticamente un fondo de respaldo con degradado.
class _SportsHeader extends StatelessWidget {
  const _SportsHeader({required this.firstName});

  final String? firstName;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('home-sports-header'),
      height: 210,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(26),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.32),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.asset(
            'assets/images/home_banner.jpg',
            fit: BoxFit.cover,
            alignment: Alignment.center,
            errorBuilder: (context, error, stackTrace) {
              return _SportsHeaderFallback();
            },
          ),

          // El degradado mantiene legible el texto incluso cuando la
          // imagen contiene sectores muy claros.
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0x28000000),
                  Color(0x70000000),
                  Color(0xF2000000),
                ],
                stops: [0, 0.48, 1],
              ),
            ),
          ),

          // Agrega una leve sombra lateral para mejorar la lectura del
          // titulo sin ocultar completamente la fotografia.
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [
                  Color(0xB8000000),
                  Color(0x30000000),
                  Color(0x00000000),
                ],
              ),
            ),
          ),

          Positioned(
            left: 22,
            right: 22,
            top: 22,
            bottom: 22,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  firstName == null || firstName!.trim().isEmpty
                      ? 'Bienvenido al club'
                      : 'Hola, $firstName',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                    shadows: const [
                      Shadow(color: Colors.black, blurRadius: 10),
                    ],
                  ),
                ),
                const Spacer(),
                Text(
                  'ZONA\nDEPORTIVA',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    height: 0.92,
                    letterSpacing: 0.7,
                    shadows: const [
                      Shadow(color: Colors.black, blurRadius: 14),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  'Sedes, espacios y reservas en un solo lugar.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white.withValues(alpha: 0.92),
                    fontWeight: FontWeight.w500,
                    shadows: const [
                      Shadow(color: Colors.black, blurRadius: 10),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Fondo utilizado cuando no se encuentra home_banner.jpg.
///
/// Este estado tambien facilita ejecutar pruebas sin depender de un
/// archivo de imagen real.
class _SportsHeaderFallback extends StatelessWidget {
  const _SportsHeaderFallback();

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [colorScheme.primaryContainer, colorScheme.primary],
        ),
      ),
      child: Align(
        alignment: Alignment.centerRight,
        child: Transform.translate(
          offset: const Offset(28, 10),
          child: Icon(
            Icons.sports_soccer,
            size: 170,
            color: Colors.black.withValues(alpha: 0.12),
          ),
        ),
      ),
    );
  }
}

/// Encabezado reutilizable para las secciones del Home.
class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.title,
    this.actionLabel,
    this.onActionPressed,
  });

  final String title;
  final String? actionLabel;
  final VoidCallback? onActionPressed;

  @override
  Widget build(BuildContext context) {
    final actionText = actionLabel;
    final action = onActionPressed;

    return Row(
      children: [
        Expanded(
          child: Text(
            title,
            style: Theme.of(context).textTheme.titleLarge
                ?.copyWith(fontWeight: FontWeight.w800),
          ),
        ),
        if (actionText != null && action != null)
          TextButton(onPressed: action, child: Text(actionText)),
      ],
    );
  }
}

/// Estado real mientras el usuario no tiene una reserva proxima.
class _EmptyNextReservationCard extends StatelessWidget {
  const _EmptyNextReservationCard({required this.onExploreVenues});

  final VoidCallback onExploreVenues;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      key: const Key('home-empty-next-reservation'),
      elevation: 0,
      color: colorScheme.surfaceContainer,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onExploreVenues,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  color: colorScheme.primary.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Icon(
                    Icons.event_available_outlined,
                    size: 30,
                    color: colorScheme.primary,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Todavia no tenes una reserva proxima',
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      'Explora las sedes para comenzar.',
                      style: Theme.of(context).textTheme.bodyMedium
                          ?.copyWith(color: colorScheme.onSurfaceVariant),
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

/// Filtros visuales que se conectaran posteriormente con SportsSpace.
///
/// Mientras el backend no incluya espacios deportivos, los chips
/// comunican las categorias previstas sin simular resultados.
class _SportFilterChips extends StatefulWidget {
  const _SportFilterChips();

  @override
  State<_SportFilterChips> createState() => _SportFilterChipsState();
}

class _SportFilterChipsState extends State<_SportFilterChips> {
  static const List<String> _sports = [
    'Todos',
    'Futbol',
    'Tenis',
    'Golf',
    'Hockey',
    'Voley',
  ];

  String _selectedSport = 'Todos';

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: _sports.map((sport) {
        return ChoiceChip(
          key: ValueKey('home-sport-$sport'),
          label: Text(sport),
          selected: _selectedSport == sport,
          onSelected: (_) {
            setState(() {
              _selectedSport = sport;
            });

            if (sport != 'Todos') {
              ScaffoldMessenger.of(context)
                ..hideCurrentSnackBar()
                ..showSnackBar(
                  SnackBar(
                    content: Text(
                      'El filtro $sport se conectara con los '
                      'espacios deportivos.',
                    ),
                  ),
                );
            }
          },
        );
      }).toList(),
    );
  }
}

/// Tarjeta de acceso rapido utilizada dentro del Home.
class _HomeOptionCard extends StatelessWidget {
  const _HomeOptionCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.accentColor,
    required this.onTap,
    super.key,
  });

  final IconData icon;
  final String title;
  final String description;
  final Color accentColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      elevation: 0,
      color: colorScheme.surfaceContainer,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            children: [
              DecoratedBox(
                decoration: BoxDecoration(
                  color: accentColor.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Icon(icon, color: accentColor),
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
                    const SizedBox(height: 5),
                    Text(
                      description,
                      style: Theme.of(context).textTheme.bodyMedium
                          ?.copyWith(color: colorScheme.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(Icons.chevron_right, color: accentColor),
            ],
          ),
        ),
      ),
    );
  }
}

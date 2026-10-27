import 'package:flutter/material.dart';

import '../../../sports_spaces/data/services/sports_space_api_client.dart';
import '../../../sports_spaces/presentation/screens/sports_space_list_screen.dart';
import '../../data/models/venue.dart';
import '../../data/services/venue_api_client.dart';

/// Muestra las sedes obtenidas desde FastAPI.
///
/// La pantalla administra los estados de carga, contenido, lista vacia
/// y error. Al seleccionar una sede, muestra sus espacios deportivos.
class VenueListScreen extends StatefulWidget {
  const VenueListScreen({super.key, this.apiClient, this.sportsSpaceApiClient});

  /// Cliente opcional utilizado para obtener las sedes.
  ///
  /// Permite reemplazar el cliente real durante las pruebas.
  final VenueApiClient? apiClient;

  /// Cliente opcional utilizado para obtener espacios deportivos.
  ///
  /// Si no se recibe, SportsSpaceListScreen construye su propio
  /// cliente cuando se abre una sede.
  final SportsSpaceApiClient? sportsSpaceApiClient;

  @override
  State<VenueListScreen> createState() => _VenueListScreenState();
}

class _VenueListScreenState extends State<VenueListScreen> {
  late final VenueApiClient _apiClient;
  late final bool _ownsApiClient;

  List<Venue> _venues = const [];
  String? _errorMessage;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();

    _ownsApiClient = widget.apiClient == null;
    _apiClient = widget.apiClient ?? VenueApiClient();

    _loadVenues();
  }

  @override
  void dispose() {
    if (_ownsApiClient) {
      _apiClient.close();
    }

    super.dispose();
  }

  /// Consulta las sedes y actualiza el estado visible.
  Future<void> _loadVenues() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final venues = await _apiClient.getVenues();

      if (!mounted) {
        return;
      }

      setState(() {
        _venues = venues;
        _isLoading = false;
      });
    } on VenueApiException catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = error.message;
        _isLoading = false;
      });
    } on Exception {
      if (!mounted) {
        return;
      }

      setState(() {
        _errorMessage = 'Ocurrio un error inesperado.';
        _isLoading = false;
      });
    }
  }

  /// Abre los espacios deportivos activos de una sede.
  void _openSportsSpaces(Venue venue) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) {
          return SportsSpaceListScreen(
            venue: venue,
            apiClient: widget.sportsSpaceApiClient,
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Seleccionar sede'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        key: Key('venue-list-loading'),
        child: CircularProgressIndicator(),
      );
    }

    final errorMessage = _errorMessage;

    if (errorMessage != null) {
      return _VenueErrorView(message: errorMessage, onRetry: _loadVenues);
    }

    if (_venues.isEmpty) {
      return const _VenueEmptyView();
    }

    return RefreshIndicator(
      onRefresh: _loadVenues,
      child: ListView.separated(
        key: const Key('venue-list'),
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        itemCount: _venues.length,
        separatorBuilder: (context, index) {
          return const SizedBox(height: 12);
        },
        itemBuilder: (context, index) {
          final venue = _venues[index];

          return _VenueCard(
            venue: venue,
            onTap: venue.isActive
                ? () {
                    _openSportsSpaces(venue);
                  }
                : null,
          );
        },
      ),
    );
  }
}

/// Muestra una sede dentro del listado.
class _VenueCard extends StatelessWidget {
  const _VenueCard({required this.venue, required this.onTap});

  final Venue venue;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      key: ValueKey('venue-card-${venue.id}'),
      elevation: 0,
      color: colorScheme.surfaceContainer,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  DecoratedBox(
                    decoration: BoxDecoration(
                      color: colorScheme.primary.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: SizedBox.square(
                      dimension: 54,
                      child: Icon(
                        Icons.location_city_outlined,
                        color: colorScheme.primary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          venue.name,
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 6),
                        _VenueInformationRow(
                          icon: Icons.location_on_outlined,
                          text: venue.address,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  _VenueStatusBadge(isActive: venue.isActive),
                ],
              ),
              const SizedBox(height: 14),
              _VenueInformationRow(
                icon: Icons.schedule_outlined,
                text:
                    '${_formatTime(venue.openingTime)}'
                    ' - ${_formatTime(venue.closingTime)}',
              ),
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    venue.isActive ? 'Ver espacios' : 'Sede no disponible',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      color: venue.isActive
                          ? colorScheme.primary
                          : colorScheme.onSurfaceVariant,
                    ),
                  ),
                  if (venue.isActive) ...[
                    const SizedBox(width: 4),
                    Icon(Icons.chevron_right, color: colorScheme.primary),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Reduce HH:mm:ss a HH:mm para mostrarlo en la interfaz.
  String _formatTime(String value) {
    final parts = value.split(':');

    if (parts.length < 2) {
      return value;
    }

    return '${parts[0]}:${parts[1]}';
  }
}

/// Muestra un dato acompañado por un icono.
class _VenueInformationRow extends StatelessWidget {
  const _VenueInformationRow({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 20,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(text, style: Theme.of(context).textTheme.bodyMedium),
        ),
      ],
    );
  }
}

/// Indica visualmente si una sede esta activa.
class _VenueStatusBadge extends StatelessWidget {
  const _VenueStatusBadge({required this.isActive});

  final bool isActive;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    final backgroundColor = isActive
        ? colorScheme.primaryContainer
        : colorScheme.surfaceContainerHighest;

    final foregroundColor = isActive
        ? colorScheme.onPrimaryContainer
        : colorScheme.onSurfaceVariant;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        child: Text(
          isActive ? 'Activa' : 'Inactiva',
          style: Theme.of(context).textTheme.labelMedium
              ?.copyWith(color: foregroundColor, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}

/// Muestra el estado vacio del listado.
class _VenueEmptyView extends StatelessWidget {
  const _VenueEmptyView();

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('venue-list-empty'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.location_city_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'No hay sedes disponibles',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Las sedes registradas apareceran '
              'en esta pantalla.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}

/// Muestra un error y permite repetir la consulta.
class _VenueErrorView extends StatelessWidget {
  const _VenueErrorView({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('venue-list-error'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.cloud_off_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'No se pudieron cargar las sedes',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              key: const Key('venue-list-retry'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
            ),
          ],
        ),
      ),
    );
  }
}

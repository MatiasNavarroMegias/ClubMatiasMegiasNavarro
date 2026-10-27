import 'package:flutter/material.dart';

import '../../../venues/data/models/venue.dart';
import '../../data/models/sports_space.dart';
import '../../data/services/sports_space_api_client.dart';

/// Muestra los espacios deportivos activos de una sede.
///
/// La pantalla permite filtrar localmente por tipo de deporte después
/// de obtener los espacios activos desde FastAPI.
class SportsSpaceListScreen extends StatefulWidget {
  const SportsSpaceListScreen({
    required this.venue,
    this.apiClient,
    this.onSportsSpaceSelected,
    super.key,
  });

  /// Sede cuyos espacios deben consultarse.
  final Venue venue;

  /// Cliente reemplazable durante las pruebas automatizadas.
  final SportsSpaceApiClient? apiClient;

  /// Accion opcional ejecutada al seleccionar un espacio.
  ///
  /// En el modulo de reservas permitira continuar hacia la consulta
  /// de disponibilidad.
  final ValueChanged<SportsSpace>? onSportsSpaceSelected;

  @override
  State<SportsSpaceListScreen> createState() => _SportsSpaceListScreenState();
}

class _SportsSpaceListScreenState extends State<SportsSpaceListScreen> {
  late final SportsSpaceApiClient _apiClient;
  late final bool _ownsApiClient;

  List<SportsSpace> _sportsSpaces = const [];
  String? _selectedSportType;
  String? _errorMessage;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();

    _ownsApiClient = widget.apiClient == null;
    _apiClient = widget.apiClient ?? SportsSpaceApiClient();

    _loadSportsSpaces();
  }

  @override
  void dispose() {
    if (_ownsApiClient) {
      _apiClient.close();
    }

    super.dispose();
  }

  /// Consulta solamente los espacios activos de la sede seleccionada.
  Future<void> _loadSportsSpaces() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final sportsSpaces = await _apiClient.getSportsSpaces(
        venueId: widget.venue.id,
        isActive: true,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _sportsSpaces = sportsSpaces;
        _selectedSportType = null;
        _isLoading = false;
      });
    } on SportsSpaceApiException catch (error) {
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

  /// Obtiene los deportes disponibles sin duplicados.
  List<String> get _availableSportTypes {
    final sportTypes = _sportsSpaces
        .map((sportsSpace) => sportsSpace.sportType)
        .toSet()
        .toList();

    sportTypes.sort();

    return sportTypes;
  }

  /// Devuelve los espacios visibles para el filtro seleccionado.
  List<SportsSpace> get _filteredSportsSpaces {
    final selectedSportType = _selectedSportType;

    if (selectedSportType == null) {
      return _sportsSpaces;
    }

    return _sportsSpaces.where((sportsSpace) {
      return sportsSpace.sportType == selectedSportType;
    }).toList();
  }

  /// Cambia el filtro deportivo visible.
  void _selectSportType(String? sportType) {
    setState(() {
      _selectedSportType = sportType;
    });
  }

  /// Ejecuta la accion configurada para el espacio seleccionado.
  void _selectSportsSpace(SportsSpace sportsSpace) {
    final onSportsSpaceSelected = widget.onSportsSpaceSelected;

    if (onSportsSpaceSelected != null) {
      onSportsSpaceSelected(sportsSpace);
      return;
    }

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            '${sportsSpace.name} se utilizara '
            'para consultar disponibilidad.',
          ),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Espacios deportivos'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: SafeArea(
        child: Column(
          children: [
            _VenueSummary(venue: widget.venue),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        key: Key('sports-space-list-loading'),
        child: CircularProgressIndicator(),
      );
    }

    final errorMessage = _errorMessage;

    if (errorMessage != null) {
      return _SportsSpaceErrorView(
        message: errorMessage,
        onRetry: _loadSportsSpaces,
      );
    }

    if (_sportsSpaces.isEmpty) {
      return _SportsSpaceEmptyView(venueName: widget.venue.name);
    }

    final filteredSportsSpaces = _filteredSportsSpaces;

    return RefreshIndicator(
      onRefresh: _loadSportsSpaces,
      child: CustomScrollView(
        key: const Key('sports-space-list-scroll'),
        slivers: [
          SliverToBoxAdapter(
            child: _SportFilters(
              sportTypes: _availableSportTypes,
              selectedSportType: _selectedSportType,
              onSelected: _selectSportType,
            ),
          ),
          if (filteredSportsSpaces.isEmpty)
            const SliverFillRemaining(
              hasScrollBody: false,
              child: _NoFilterResultsView(),
            )
          else
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              sliver: SliverList.separated(
                itemCount: filteredSportsSpaces.length,
                separatorBuilder: (context, index) =>
                    const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final sportsSpace = filteredSportsSpaces[index];

                  return _SportsSpaceCard(
                    sportsSpace: sportsSpace,
                    onTap: () {
                      _selectSportsSpace(sportsSpace);
                    },
                  );
                },
              ),
            ),
        ],
      ),
    );
  }
}

/// Muestra los datos principales de la sede seleccionada.
class _VenueSummary extends StatelessWidget {
  const _VenueSummary({required this.venue});

  final Venue venue;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: colorScheme.surfaceContainer,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Row(
          children: [
            DecoratedBox(
              decoration: BoxDecoration(
                color: colorScheme.primary.withValues(alpha: 0.16),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: const EdgeInsets.all(14),
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
                  const SizedBox(height: 5),
                  Text(
                    venue.address,
                    style: Theme.of(context).textTheme.bodyMedium
                        ?.copyWith(color: colorScheme.onSurfaceVariant),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Muestra los filtros deportivos disponibles.
class _SportFilters extends StatelessWidget {
  const _SportFilters({
    required this.sportTypes,
    required this.selectedSportType,
    required this.onSelected,
  });

  final List<String> sportTypes;
  final String? selectedSportType;
  final ValueChanged<String?> onSelected;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      key: const Key('sports-space-sport-filters'),
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      child: Row(
        children: [
          ChoiceChip(
            key: const Key('sports-space-filter-all'),
            label: const Text('Todos'),
            selected: selectedSportType == null,
            onSelected: (_) {
              onSelected(null);
            },
          ),
          for (final sportType in sportTypes) ...[
            const SizedBox(width: 8),
            ChoiceChip(
              key: ValueKey('sports-space-filter-$sportType'),
              label: Text(sportType),
              selected: selectedSportType == sportType,
              onSelected: (_) {
                onSelected(sportType);
              },
            ),
          ],
        ],
      ),
    );
  }
}

/// Tarjeta temporal utilizada para mostrar un espacio.
class _SportsSpaceCard extends StatelessWidget {
  const _SportsSpaceCard({required this.sportsSpace, required this.onTap});

  final SportsSpace sportsSpace;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      key: ValueKey('sports-space-card-${sportsSpace.id}'),
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
                  color: colorScheme.primary.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: SizedBox.square(
                  dimension: 58,
                  child: Icon(
                    _sportIcon(sportsSpace.sportType),
                    color: colorScheme.primary,
                    size: 30,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      sportsSpace.name,
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      sportsSpace.sportType,
                      style: Theme.of(context).textTheme.bodyMedium
                          ?.copyWith(color: colorScheme.onSurfaceVariant),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Espacio ${sportsSpace.spaceNumber}',
                      style: Theme.of(context).textTheme.bodySmall,
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

  /// Selecciona un icono aproximado para cada deporte.
  IconData _sportIcon(String sportType) {
    return switch (sportType.toLowerCase()) {
      'futbol' => Icons.sports_soccer,
      'tenis' => Icons.sports_tennis,
      'basket' || 'basquet' || 'basquetbol' => Icons.sports_basketball,
      'voley' || 'voleibol' => Icons.sports_volleyball,
      'golf' => Icons.sports_golf,
      'hockey' => Icons.sports_hockey,
      _ => Icons.sports_outlined,
    };
  }
}

/// Muestra el estado sin espacios activos.
class _SportsSpaceEmptyView extends StatelessWidget {
  const _SportsSpaceEmptyView({required this.venueName});

  final String venueName;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('sports-space-list-empty'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.sports_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'No hay espacios disponibles',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              '$venueName todavia no tiene '
              'espacios deportivos activos.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}

/// Muestra un estado sin resultados para el filtro.
class _NoFilterResultsView extends StatelessWidget {
  const _NoFilterResultsView();

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('sports-space-filter-empty'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Text(
          'No hay espacios para el deporte seleccionado.',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.bodyLarge,
        ),
      ),
    );
  }
}

/// Muestra un error y permite repetir la consulta.
class _SportsSpaceErrorView extends StatelessWidget {
  const _SportsSpaceErrorView({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('sports-space-list-error'),
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
              'No se pudieron cargar los espacios',
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
              key: const Key('sports-space-list-retry'),
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

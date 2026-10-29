import 'package:flutter/material.dart';

import '../../data/models/reservation.dart';
import '../../data/services/reservation_api_client.dart';

/// Muestra las proximas reservas del usuario autenticado.
///
/// La pantalla consulta las reservas confirmadas que todavia no
/// comenzaron. La cancelacion se incorporara en el siguiente paso.
class UpcomingReservationsScreen extends StatefulWidget {
  const UpcomingReservationsScreen({
    required this.accessToken,
    this.apiClient,
    super.key,
  });

  /// Token utilizado para consultar las reservas del usuario.
  final String accessToken;

  /// Cliente reemplazable durante las pruebas automatizadas.
  final ReservationApiClient? apiClient;

  @override
  State<UpcomingReservationsScreen> createState() {
    return _UpcomingReservationsScreenState();
  }
}

class _UpcomingReservationsScreenState
    extends State<UpcomingReservationsScreen> {
  late final ReservationApiClient _apiClient;
  late final bool _ownsApiClient;

  List<Reservation> _reservations = const [];
  String? _errorMessage;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();

    _ownsApiClient = widget.apiClient == null;
    _apiClient = widget.apiClient ?? ReservationApiClient();

    _loadReservations();
  }

  @override
  void didUpdateWidget(covariant UpcomingReservationsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.accessToken == widget.accessToken) {
      return;
    }

    _loadReservations();
  }

  @override
  void dispose() {
    if (_ownsApiClient) {
      _apiClient.close();
    }

    super.dispose();
  }

  /// Consulta las proximas reservas del usuario autenticado.
  Future<void> _loadReservations() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final reservations = await _apiClient.getUpcomingReservations(
        accessToken: widget.accessToken,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _reservations = reservations;
        _isLoading = false;
      });
    } on ReservationApiException catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _reservations = const [];
        _errorMessage = error.message;
        _isLoading = false;
      });
    } on Exception {
      if (!mounted) {
        return;
      }

      setState(() {
        _reservations = const [];
        _errorMessage = 'Ocurrio un error inesperado.';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      key: const Key('upcoming-reservations-screen'),
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Mis reservas'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        key: Key('upcoming-reservations-loading'),
        child: CircularProgressIndicator(),
      );
    }

    final errorMessage = _errorMessage;

    if (errorMessage != null) {
      return _UpcomingReservationsErrorView(
        message: errorMessage,
        onRetry: _loadReservations,
      );
    }

    if (_reservations.isEmpty) {
      return const _UpcomingReservationsEmptyView();
    }

    return RefreshIndicator(
      onRefresh: _loadReservations,
      child: ListView.separated(
        key: const Key('upcoming-reservations-list'),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        itemCount: _reservations.length,
        separatorBuilder: (context, index) {
          return const SizedBox(height: 12);
        },
        itemBuilder: (context, index) {
          return _UpcomingReservationCard(reservation: _reservations[index]);
        },
      ),
    );
  }
}

/// Muestra una proxima reserva.
class _UpcomingReservationCard extends StatelessWidget {
  const _UpcomingReservationCard({required this.reservation});

  final Reservation reservation;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final localStart = reservation.startAt.toLocal();
    final localEnd = reservation.endAt.toLocal();

    return Card(
      key: ValueKey('upcoming-reservation-${reservation.id}'),
      elevation: 0,
      color: colorScheme.surfaceContainer,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: colorScheme.primary.withValues(alpha: 0.14),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: SizedBox.square(
                    dimension: 52,
                    child: Icon(
                      Icons.calendar_month_outlined,
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
                        'Reserva #${reservation.id}',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        'Espacio deportivo '
                        '${reservation.sportsSpaceId}',
                        style: Theme.of(context).textTheme.bodyMedium
                            ?.copyWith(color: colorScheme.onSurfaceVariant),
                      ),
                    ],
                  ),
                ),
                _ConfirmedBadge(colorScheme: colorScheme),
              ],
            ),
            const SizedBox(height: 18),
            _ReservationInformationRow(
              icon: Icons.event_outlined,
              text: _formatDate(localStart),
            ),
            const SizedBox(height: 10),
            _ReservationInformationRow(
              icon: Icons.schedule_outlined,
              text:
                  '${_formatTime(localStart)}'
                  ' - ${_formatTime(localEnd)}',
            ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime value) {
    final day = value.day.toString().padLeft(2, '0');
    final month = value.month.toString().padLeft(2, '0');

    return '$day/$month/${value.year}';
  }

  String _formatTime(DateTime value) {
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');

    return '$hour:$minute';
  }
}

/// Indica que la reserva se encuentra confirmada.
class _ConfirmedBadge extends StatelessWidget {
  const _ConfirmedBadge({required this.colorScheme});

  final ColorScheme colorScheme;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        child: Text(
          'Confirmada',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: colorScheme.onPrimaryContainer,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

/// Muestra un dato de la reserva acompañado por un icono.
class _ReservationInformationRow extends StatelessWidget {
  const _ReservationInformationRow({required this.icon, required this.text});

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
        const SizedBox(width: 9),
        Expanded(
          child: Text(text, style: Theme.of(context).textTheme.bodyMedium),
        ),
      ],
    );
  }
}

/// Muestra el estado sin proximas reservas.
class _UpcomingReservationsEmptyView extends StatelessWidget {
  const _UpcomingReservationsEmptyView();

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('upcoming-reservations-empty'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.event_available_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'No tenes proximas reservas',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Cuando reserves un espacio, el turno '
              'aparecera en esta seccion.',
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
class _UpcomingReservationsErrorView extends StatelessWidget {
  const _UpcomingReservationsErrorView({
    required this.message,
    required this.onRetry,
  });

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('upcoming-reservations-error'),
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
              'No se pudieron cargar tus reservas',
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
              key: const Key('upcoming-reservations-retry'),
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

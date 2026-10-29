import 'package:flutter/material.dart';

import '../../data/models/reservation.dart';
import '../../data/services/reservation_api_client.dart';

/// Muestra el historial de reservas del usuario autenticado.
///
/// El historial contiene reservas canceladas y reservas confirmadas
/// cuyo horario ya finalizo.
class ReservationHistoryScreen extends StatefulWidget {
  const ReservationHistoryScreen({
    required this.accessToken,
    this.apiClient,
    super.key,
  });

  /// Token utilizado para consultar el historial del usuario.
  final String accessToken;

  /// Cliente reemplazable durante las pruebas automatizadas.
  final ReservationApiClient? apiClient;

  @override
  State<ReservationHistoryScreen> createState() {
    return _ReservationHistoryScreenState();
  }
}

class _ReservationHistoryScreenState extends State<ReservationHistoryScreen> {
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

    _loadHistory();
  }

  @override
  void didUpdateWidget(covariant ReservationHistoryScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.accessToken == widget.accessToken) {
      return;
    }

    _loadHistory();
  }

  @override
  void dispose() {
    if (_ownsApiClient) {
      _apiClient.close();
    }

    super.dispose();
  }

  /// Consulta el historial del usuario autenticado.
  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final reservations = await _apiClient.getReservationHistory(
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
    return Scaffold(
      key: const Key('reservation-history-screen'),
      body: SafeArea(child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        key: Key('reservation-history-loading'),
        child: CircularProgressIndicator(),
      );
    }

    final errorMessage = _errorMessage;

    if (errorMessage != null) {
      return _ReservationHistoryErrorView(
        message: errorMessage,
        onRetry: _loadHistory,
      );
    }

    if (_reservations.isEmpty) {
      return const _ReservationHistoryEmptyView();
    }

    return RefreshIndicator(
      onRefresh: _loadHistory,
      child: ListView.separated(
        key: const Key('reservation-history-list'),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        itemCount: _reservations.length,
        separatorBuilder: (context, index) {
          return const SizedBox(height: 12);
        },
        itemBuilder: (context, index) {
          return _ReservationHistoryCard(reservation: _reservations[index]);
        },
      ),
    );
  }
}

/// Muestra una reserva historica.
class _ReservationHistoryCard extends StatelessWidget {
  const _ReservationHistoryCard({required this.reservation});

  final Reservation reservation;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final localStart = reservation.startAt.toLocal();
    final localEnd = reservation.endAt.toLocal();

    return Card(
      key: ValueKey('history-reservation-${reservation.id}'),
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
                    color: _badgeBackgroundColor(colorScheme),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: SizedBox.square(
                    dimension: 52,
                    child: Icon(
                      reservation.isCancelled
                          ? Icons.event_busy_outlined
                          : Icons.history_outlined,
                      color: _badgeForegroundColor(colorScheme),
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
                _ReservationHistoryBadge(reservation: reservation),
              ],
            ),
            const SizedBox(height: 18),
            _HistoryInformationRow(
              icon: Icons.event_outlined,
              text: _formatDate(localStart),
            ),
            const SizedBox(height: 10),
            _HistoryInformationRow(
              icon: Icons.schedule_outlined,
              text:
                  '${_formatTime(localStart)}'
                  ' - ${_formatTime(localEnd)}',
            ),
            if (reservation.cancelledAt != null) ...[
              const SizedBox(height: 10),
              _HistoryInformationRow(
                icon: Icons.cancel_outlined,
                text:
                    'Cancelada el '
                    '${_formatDateTime(reservation.cancelledAt!.toLocal())}',
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _badgeBackgroundColor(ColorScheme colorScheme) {
    if (reservation.isCancelled) {
      return colorScheme.errorContainer;
    }

    return colorScheme.secondaryContainer;
  }

  Color _badgeForegroundColor(ColorScheme colorScheme) {
    if (reservation.isCancelled) {
      return colorScheme.onErrorContainer;
    }

    return colorScheme.onSecondaryContainer;
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

  String _formatDateTime(DateTime value) {
    return '${_formatDate(value)} ${_formatTime(value)}';
  }
}

/// Muestra el estado historico de la reserva.
class _ReservationHistoryBadge extends StatelessWidget {
  const _ReservationHistoryBadge({required this.reservation});

  final Reservation reservation;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isCancelled = reservation.isCancelled;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: isCancelled
            ? colorScheme.errorContainer
            : colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        child: Text(
          isCancelled ? 'Cancelada' : 'Finalizada',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
            color: isCancelled
                ? colorScheme.onErrorContainer
                : colorScheme.onSecondaryContainer,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

/// Muestra un dato historico acompañado por un icono.
class _HistoryInformationRow extends StatelessWidget {
  const _HistoryInformationRow({required this.icon, required this.text});

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

/// Muestra el estado sin reservas historicas.
class _ReservationHistoryEmptyView extends StatelessWidget {
  const _ReservationHistoryEmptyView();

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('reservation-history-empty'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.history_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'Todavia no tenes historial',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Las reservas canceladas o finalizadas '
              'apareceran en esta seccion.',
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
class _ReservationHistoryErrorView extends StatelessWidget {
  const _ReservationHistoryErrorView({
    required this.message,
    required this.onRetry,
  });

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('reservation-history-error'),
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
              'No se pudo cargar el historial',
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
              key: const Key('reservation-history-retry'),
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

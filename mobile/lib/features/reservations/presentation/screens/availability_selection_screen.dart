import 'package:flutter/material.dart';

import '../../../sports_spaces/data/models/sports_space.dart';
import '../../../venues/data/models/venue.dart';
import '../../data/models/availability_slot.dart';
import '../../data/services/reservation_api_client.dart';

/// Permite seleccionar una fecha y un turno disponible.
///
/// La pantalla consulta FastAPI utilizando el espacio deportivo y la
/// fecha local seleccionados. En esta etapa solamente permite elegir
/// un horario. La confirmacion de la reserva se agregara posteriormente.
class AvailabilitySelectionScreen extends StatefulWidget {
  const AvailabilitySelectionScreen({
    required this.venue,
    required this.sportsSpace,
    this.apiClient,
    this.accessToken,
    this.nowProvider,
    this.onSlotSelected,
    super.key,
  });

  /// Sede a la que pertenece el espacio deportivo.
  final Venue venue;

  /// Espacio deportivo cuya disponibilidad debe consultarse.
  final SportsSpace sportsSpace;

  /// Cliente reemplazable durante las pruebas automatizadas.
  final ReservationApiClient? apiClient;

  /// Token utilizado para crear una reserva autenticada.
  ///
  /// Puede ser null mientras la pantalla se utiliza solamente para
  /// consultar disponibilidad o durante pruebas específicas.
  final String? accessToken;

  /// Proveedor opcional de la fecha actual.
  ///
  /// Permite utilizar una fecha controlada durante las pruebas.
  final DateTime Function()? nowProvider;

  /// Accion opcional ejecutada al seleccionar un turno.
  final ValueChanged<AvailabilitySlot>? onSlotSelected;

  @override
  State<AvailabilitySelectionScreen> createState() {
    return _AvailabilitySelectionScreenState();
  }
}

class _AvailabilitySelectionScreenState
    extends State<AvailabilitySelectionScreen> {
  late final ReservationApiClient _apiClient;
  late final bool _ownsApiClient;

  late DateTime _selectedDate;

  List<AvailabilitySlot> _availableSlots = const [];
  AvailabilitySlot? _selectedSlot;
  String? _errorMessage;
  bool _isLoading = true;
  bool _isCreatingReservation = false;

  @override
  void initState() {
    super.initState();

    _ownsApiClient = widget.apiClient == null;
    _apiClient = widget.apiClient ?? ReservationApiClient();
    _selectedDate = _dateOnly(_currentDateTime());

    _loadAvailability();
  }

  @override
  void dispose() {
    if (_ownsApiClient) {
      _apiClient.close();
    }

    super.dispose();
  }

  /// Devuelve el momento actual real o el configurado para pruebas.
  DateTime _currentDateTime() {
    return widget.nowProvider?.call() ?? DateTime.now();
  }

  /// Elimina la informacion horaria de una fecha.
  DateTime _dateOnly(DateTime value) {
    return DateTime(value.year, value.month, value.day);
  }

  /// Consulta los horarios disponibles para la fecha seleccionada.
  Future<void> _loadAvailability() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _selectedSlot = null;
    });

    try {
      final slots = await _apiClient.getAvailability(
        sportsSpaceId: widget.sportsSpace.id,
        selectedDate: _selectedDate,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _availableSlots = slots;
        _isLoading = false;
      });
    } on ReservationApiException catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _availableSlots = const [];
        _errorMessage = error.message;
        _isLoading = false;
      });
    } on Exception {
      if (!mounted) {
        return;
      }

      setState(() {
        _availableSlots = const [];
        _errorMessage = 'Ocurrio un error inesperado.';
        _isLoading = false;
      });
    }
  }

  /// Abre el selector de fechas y actualiza la disponibilidad.
  Future<void> _selectDate() async {
    final currentDate = _dateOnly(_currentDateTime());

    final selectedDate = await showDatePicker(
      context: context,
      initialDate: _selectedDate.isBefore(currentDate)
          ? currentDate
          : _selectedDate,
      firstDate: currentDate,
      lastDate: DateTime(
        currentDate.year + 1,
        currentDate.month,
        currentDate.day,
      ),
      helpText: 'Seleccionar fecha',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
    );

    if (selectedDate == null || !mounted) {
      return;
    }

    final normalizedDate = _dateOnly(selectedDate);

    if (normalizedDate == _selectedDate) {
      return;
    }

    setState(() {
      _selectedDate = normalizedDate;
    });

    await _loadAvailability();
  }

  /// Selecciona un horario disponible.
  void _selectSlot(AvailabilitySlot slot) {
    setState(() {
      _selectedSlot = slot;
    });

    widget.onSlotSelected?.call(slot);
  }

  /// Solicita confirmacion y crea la reserva seleccionada.
  Future<void> _confirmReservation() async {
    final selectedSlot = _selectedSlot;

    if (selectedSlot == null) {
      return;
    }

    final accessToken = widget.accessToken;

    if (accessToken == null || accessToken.trim().isEmpty) {
      _showMessage(
        'La sesion no se encuentra disponible. Inicia sesion nuevamente.',
      );
      return;
    }

    final localStart = selectedSlot.startAt.toLocal();
    final localEnd = selectedSlot.endAt.toLocal();

    final confirmed =
        await showDialog<bool>(
          context: context,
          builder: (context) {
            return AlertDialog(
              key: const Key('reservation-confirmation-dialog'),
              title: const Text('Confirmar reserva'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(widget.sportsSpace.name),
                  const SizedBox(height: 8),
                  Text(widget.venue.name),
                  const SizedBox(height: 16),
                  Text('Fecha: ${_formatDate(localStart)}'),
                  const SizedBox(height: 6),
                  Text(
                    'Horario: ${_formatTime(localStart)}'
                    ' - ${_formatTime(localEnd)}',
                  ),
                ],
              ),
              actions: [
                TextButton(
                  key: const Key('reservation-confirmation-cancel'),
                  onPressed: () {
                    Navigator.of(context).pop(false);
                  },
                  child: const Text('Volver'),
                ),
                FilledButton(
                  key: const Key('reservation-confirmation-accept'),
                  onPressed: () {
                    Navigator.of(context).pop(true);
                  },
                  child: const Text('Confirmar'),
                ),
              ],
            );
          },
        ) ??
        false;

    if (!confirmed || !mounted) {
      return;
    }

    setState(() {
      _isCreatingReservation = true;
    });

    try {
      await _apiClient.createReservation(
        accessToken: accessToken,
        sportsSpaceId: widget.sportsSpace.id,
        startAt: selectedSlot.startAt,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _isCreatingReservation = false;
        _selectedSlot = null;
      });

      _showMessage('La reserva fue creada correctamente.');

      await _loadAvailability();
    } on ReservationApiException catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isCreatingReservation = false;
      });

      _showMessage(error.message);
    } on Exception {
      if (!mounted) {
        return;
      }

      setState(() {
        _isCreatingReservation = false;
      });

      _showMessage('Ocurrio un error inesperado al crear la reserva.');
    }
  }

  /// Muestra un mensaje temporal dentro de la pantalla.
  void _showMessage(String message) {
    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  /// Formatea una fecha para mostrarla al usuario.
  String _formatDate(DateTime value) {
    final day = value.day.toString().padLeft(2, '0');
    final month = value.month.toString().padLeft(2, '0');

    return '$day/$month/${value.year}';
  }

  /// Formatea una hora para mostrarla al usuario.
  String _formatTime(DateTime value) {
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');

    return '$hour:$minute';
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      key: const Key('availability-screen'),
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Elegir horario'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: SafeArea(
        child: Column(
          children: [
            _SelectionSummary(
              venue: widget.venue,
              sportsSpace: widget.sportsSpace,
            ),
            _DateSelector(selectedDate: _selectedDate, onPressed: _selectDate),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
          child: FilledButton.icon(
            key: const Key('availability-confirm-button'),
            onPressed: _selectedSlot != null && !_isCreatingReservation
                ? _confirmReservation
                : null,
            icon: _isCreatingReservation
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(
                      key: Key('reservation-creation-loading'),
                      strokeWidth: 2,
                    ),
                  )
                : const Icon(Icons.check_circle_outline),
            label: Text(
              _isCreatingReservation
                  ? 'Creando reserva...'
                  : 'Confirmar reserva',
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        key: Key('availability-loading'),
        child: CircularProgressIndicator(),
      );
    }

    final errorMessage = _errorMessage;

    if (errorMessage != null) {
      return _AvailabilityErrorView(
        message: errorMessage,
        onRetry: _loadAvailability,
      );
    }

    if (_availableSlots.isEmpty) {
      return _AvailabilityEmptyView(selectedDate: _selectedDate);
    }

    return RefreshIndicator(
      onRefresh: _loadAvailability,
      child: ListView.separated(
        key: const Key('availability-slot-list'),
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        itemCount: _availableSlots.length,
        separatorBuilder: (context, index) {
          return const SizedBox(height: 10);
        },
        itemBuilder: (context, index) {
          final slot = _availableSlots[index];
          final isSelected = identical(slot, _selectedSlot);

          return _AvailabilitySlotCard(
            slot: slot,
            isSelected: isSelected,
            onTap: () {
              _selectSlot(slot);
            },
          );
        },
      ),
    );
  }
}

/// Resume la sede y el espacio deportivo seleccionados.
class _SelectionSummary extends StatelessWidget {
  const _SelectionSummary({required this.venue, required this.sportsSpace});

  final Venue venue;
  final SportsSpace sportsSpace;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 10),
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
                color: colorScheme.primary.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(16),
              ),
              child: SizedBox.square(
                dimension: 56,
                child: Icon(
                  Icons.calendar_month_outlined,
                  color: colorScheme.primary,
                  size: 30,
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    sportsSpace.name,
                    style: Theme.of(context).textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    '${venue.name} · ${sportsSpace.sportType}',
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

/// Permite abrir el selector de fecha.
class _DateSelector extends StatelessWidget {
  const _DateSelector({required this.selectedDate, required this.onPressed});

  final DateTime selectedDate;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 6, 16, 10),
      child: SizedBox(
        width: double.infinity,
        child: OutlinedButton.icon(
          key: const Key('availability-date-button'),
          onPressed: onPressed,
          icon: const Icon(Icons.event_outlined),
          label: Text(_formatDate(selectedDate)),
        ),
      ),
    );
  }

  String _formatDate(DateTime value) {
    final day = value.day.toString().padLeft(2, '0');
    final month = value.month.toString().padLeft(2, '0');

    return '$day/$month/${value.year}';
  }
}

/// Representa un turno seleccionable.
class _AvailabilitySlotCard extends StatelessWidget {
  const _AvailabilitySlotCard({
    required this.slot,
    required this.isSelected,
    required this.onTap,
  });

  final AvailabilitySlot slot;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final localStart = slot.startAt.toLocal();
    final localEnd = slot.endAt.toLocal();

    return Card(
      key: ValueKey('availability-slot-${slot.startAt.toIso8601String()}'),
      elevation: 0,
      color: isSelected
          ? colorScheme.primaryContainer
          : colorScheme.surfaceContainer,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          child: Row(
            children: [
              Icon(
                Icons.schedule_outlined,
                color: isSelected
                    ? colorScheme.onPrimaryContainer
                    : colorScheme.primary,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  '${_formatTime(localStart)}'
                  ' - ${_formatTime(localEnd)}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: isSelected ? colorScheme.onPrimaryContainer : null,
                  ),
                ),
              ),
              if (isSelected)
                Icon(
                  Icons.check_circle,
                  key: const Key('availability-selected-slot'),
                  color: colorScheme.onPrimaryContainer,
                )
              else
                Icon(Icons.chevron_right, color: colorScheme.primary),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime value) {
    final hour = value.hour.toString().padLeft(2, '0');
    final minute = value.minute.toString().padLeft(2, '0');

    return '$hour:$minute';
  }
}

/// Muestra una fecha sin horarios disponibles.
class _AvailabilityEmptyView extends StatelessWidget {
  const _AvailabilityEmptyView({required this.selectedDate});

  final DateTime selectedDate;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('availability-empty'),
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.event_busy_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            const SizedBox(height: 16),
            Text(
              'No hay horarios disponibles',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Elegí otra fecha para consultar nuevos turnos.',
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
class _AvailabilityErrorView extends StatelessWidget {
  const _AvailabilityErrorView({required this.message, required this.onRetry});

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      key: const Key('availability-error'),
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
              'No se pudo consultar la disponibilidad',
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
              key: const Key('availability-retry'),
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

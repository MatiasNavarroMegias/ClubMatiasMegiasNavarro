/// Representa una reserva deportiva devuelta por FastAPI.
///
/// La reserva conserva el usuario propietario, el espacio reservado,
/// el horario de una hora, su estado y la fecha de cancelacion cuando
/// corresponda.
class Reservation {
  const Reservation({
    required this.id,
    required this.userId,
    required this.sportsSpaceId,
    required this.startAt,
    required this.endAt,
    required this.status,
    required this.cancelledAt,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Identificador interno de la reserva.
  final int id;

  /// Identificador del usuario propietario.
  final int userId;

  /// Identificador del espacio deportivo reservado.
  final int sportsSpaceId;

  /// Fecha y hora de inicio del turno.
  final DateTime startAt;

  /// Fecha y hora de finalizacion del turno.
  final DateTime endAt;

  /// Estado actual de la reserva.
  ///
  /// Los valores permitidos por el backend son confirmed y cancelled.
  final String status;

  /// Fecha y hora de cancelacion.
  ///
  /// Permanece en null mientras la reserva esta confirmada.
  final DateTime? cancelledAt;

  /// Fecha y hora de creacion.
  final DateTime createdAt;

  /// Fecha y hora de la ultima modificacion.
  final DateTime updatedAt;

  /// Indica que la reserva permanece confirmada.
  bool get isConfirmed {
    return status == 'confirmed';
  }

  /// Indica que la reserva fue cancelada.
  bool get isCancelled {
    return status == 'cancelled';
  }

  /// Duracion total de la reserva.
  Duration get duration {
    return endAt.difference(startAt);
  }

  /// Indica que la reserva posee una duracion exacta de una hora.
  bool get isOneHour {
    return duration == const Duration(hours: 1);
  }

  /// Construye una reserva desde la respuesta JSON de FastAPI.
  factory Reservation.fromJson(Map<String, dynamic> json) {
    final id = _readPositiveInteger(json, 'id');
    final userId = _readPositiveInteger(json, 'user_id');
    final sportsSpaceId = _readPositiveInteger(json, 'sports_space_id');
    final startAt = _readDateTime(json, 'start_at');
    final endAt = _readDateTime(json, 'end_at');
    final status = _readStatus(json);
    final cancelledAt = _readOptionalDateTime(json, 'cancelled_at');
    final createdAt = _readDateTime(json, 'created_at');
    final updatedAt = _readDateTime(json, 'updated_at');

    if (!endAt.isAfter(startAt)) {
      throw const FormatException(
        'El horario final debe ser posterior al inicio.',
      );
    }

    if (status == 'confirmed' && cancelledAt != null) {
      throw const FormatException(
        'Una reserva confirmada no puede tener fecha de cancelacion.',
      );
    }

    if (status == 'cancelled' && cancelledAt == null) {
      throw const FormatException(
        'Una reserva cancelada debe tener fecha de cancelacion.',
      );
    }

    return Reservation(
      id: id,
      userId: userId,
      sportsSpaceId: sportsSpaceId,
      startAt: startAt,
      endAt: endAt,
      status: status,
      cancelledAt: cancelledAt,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }

  /// Convierte la reserva nuevamente en un objeto JSON.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'sports_space_id': sportsSpaceId,
      'start_at': startAt.toIso8601String(),
      'end_at': endAt.toIso8601String(),
      'status': status,
      'cancelled_at': cancelledAt?.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// Lee un identificador entero positivo.
  static int _readPositiveInteger(Map<String, dynamic> json, String fieldName) {
    final value = json[fieldName];

    if (value is! int || value <= 0) {
      throw FormatException(
        'El campo $fieldName debe ser un numero entero positivo.',
      );
    }

    return value;
  }

  /// Lee y valida el estado de la reserva.
  static String _readStatus(Map<String, dynamic> json) {
    final value = json['status'];

    if (value is! String || value.trim().isEmpty) {
      throw const FormatException('El campo status debe contener texto.');
    }

    final normalizedValue = value.trim();

    if (normalizedValue != 'confirmed' && normalizedValue != 'cancelled') {
      throw const FormatException('El estado de la reserva no es valido.');
    }

    return normalizedValue;
  }

  /// Lee una fecha obligatoria.
  static DateTime _readDateTime(Map<String, dynamic> json, String fieldName) {
    final value = json[fieldName];

    if (value is! String || value.trim().isEmpty) {
      throw FormatException('El campo $fieldName debe contener una fecha.');
    }

    final parsedValue = DateTime.tryParse(value.trim());

    if (parsedValue == null) {
      throw FormatException('El campo $fieldName contiene una fecha invalida.');
    }

    return parsedValue;
  }

  /// Lee una fecha opcional.
  static DateTime? _readOptionalDateTime(
    Map<String, dynamic> json,
    String fieldName,
  ) {
    final value = json[fieldName];

    if (value == null) {
      return null;
    }

    if (value is! String || value.trim().isEmpty) {
      throw FormatException('El campo $fieldName debe ser una fecha o null.');
    }

    final parsedValue = DateTime.tryParse(value.trim());

    if (parsedValue == null) {
      throw FormatException('El campo $fieldName contiene una fecha invalida.');
    }

    return parsedValue;
  }
}

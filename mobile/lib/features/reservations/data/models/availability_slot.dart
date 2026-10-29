/// Representa un turno disponible para reservar.
///
/// Cada turno posee una fecha de inicio y una fecha de finalizacion
/// recibidas desde FastAPI con informacion de zona horaria.
class AvailabilitySlot {
  const AvailabilitySlot({required this.startAt, required this.endAt});

  /// Fecha y hora de inicio del turno.
  final DateTime startAt;

  /// Fecha y hora de finalizacion del turno.
  final DateTime endAt;

  /// Construye un turno disponible desde la respuesta JSON.
  factory AvailabilitySlot.fromJson(Map<String, dynamic> json) {
    final startAt = _readDateTime(json, 'start_at');
    final endAt = _readDateTime(json, 'end_at');

    if (!endAt.isAfter(startAt)) {
      throw const FormatException(
        'El horario final debe ser posterior al inicio.',
      );
    }

    return AvailabilitySlot(startAt: startAt, endAt: endAt);
  }

  /// Convierte el turno a un objeto JSON.
  ///
  /// Este metodo facilita las pruebas y permite reutilizar el modelo
  /// si una pantalla necesita conservar temporalmente el horario.
  Map<String, dynamic> toJson() {
    return {
      'start_at': startAt.toIso8601String(),
      'end_at': endAt.toIso8601String(),
    };
  }

  /// Duracion total del turno.
  Duration get duration {
    return endAt.difference(startAt);
  }

  /// Indica que el turno posee una duracion exacta de una hora.
  bool get isOneHour {
    return duration == const Duration(hours: 1);
  }

  /// Lee una fecha obligatoria desde un objeto JSON.
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
}

/// Representa un espacio deportivo recibido desde FastAPI.
///
/// El modelo contiene solamente informacion persistente. La
/// disponibilidad se consultara posteriormente para una fecha y
/// horario determinados.
class SportsSpace {
  const SportsSpace({
    required this.id,
    required this.venueId,
    required this.name,
    required this.sportType,
    required this.spaceNumber,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Identificador interno del espacio deportivo.
  final int id;

  /// Identificador de la sede a la que pertenece.
  final int venueId;

  /// Nombre visible del espacio.
  final String name;

  /// Tipo de deporte utilizado para filtros.
  final String sportType;

  /// Numero que diferencia espacios del mismo deporte.
  final int spaceNumber;

  /// Indica si el espacio puede utilizarse para nuevas operaciones.
  final bool isActive;

  /// Fecha y hora de creacion.
  final DateTime createdAt;

  /// Fecha y hora de la ultima modificacion.
  final DateTime updatedAt;

  /// Construye el modelo desde una respuesta JSON.
  factory SportsSpace.fromJson(Map<String, dynamic> json) {
    return SportsSpace(
      id: _readInt(json, 'id'),
      venueId: _readInt(json, 'venue_id'),
      name: _readString(json, 'name'),
      sportType: _readString(json, 'sport_type'),
      spaceNumber: _readInt(json, 'space_number'),
      isActive: _readBool(json, 'is_active'),
      createdAt: _readDateTime(json, 'created_at'),
      updatedAt: _readDateTime(json, 'updated_at'),
    );
  }

  /// Convierte el modelo en un objeto JSON.
  ///
  /// Este metodo facilita pruebas y futuras operaciones locales.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'venue_id': venueId,
      'name': name,
      'sport_type': sportType,
      'space_number': spaceNumber,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  static int _readInt(Map<String, dynamic> json, String fieldName) {
    final value = json[fieldName];

    if (value is! int) {
      throw FormatException('El campo $fieldName debe ser un numero entero.');
    }

    return value;
  }

  static String _readString(Map<String, dynamic> json, String fieldName) {
    final value = json[fieldName];

    if (value is! String || value.trim().isEmpty) {
      throw FormatException('El campo $fieldName debe contener texto.');
    }

    return value;
  }

  static bool _readBool(Map<String, dynamic> json, String fieldName) {
    final value = json[fieldName];

    if (value is! bool) {
      throw FormatException('El campo $fieldName debe ser booleano.');
    }

    return value;
  }

  static DateTime _readDateTime(Map<String, dynamic> json, String fieldName) {
    final value = json[fieldName];

    if (value is! String) {
      throw FormatException('El campo $fieldName debe contener una fecha.');
    }

    final parsedValue = DateTime.tryParse(value);

    if (parsedValue == null) {
      throw FormatException('El campo $fieldName contiene una fecha invalida.');
    }

    return parsedValue;
  }
}

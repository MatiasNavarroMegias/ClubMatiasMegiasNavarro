/// Representa una sede recibida desde la API.
///
/// La clase contiene los mismos datos que VenueResponse en FastAPI.
/// Tambien permite transformar respuestas JSON en objetos de Dart.
class Venue {
  const Venue({
    required this.id,
    required this.name,
    required this.address,
    required this.openingTime,
    required this.closingTime,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Identificador generado por PostgreSQL.
  final int id;

  /// Nombre visible de la sede.
  final String name;

  /// Direccion fisica de la sede.
  final String address;

  /// Horario habitual de apertura en formato HH:mm:ss.
  final String openingTime;

  /// Horario habitual de cierre en formato HH:mm:ss.
  final String closingTime;

  /// Indica si la sede se encuentra activa.
  final bool isActive;

  /// Fecha y hora en que se creo la sede.
  final DateTime createdAt;

  /// Fecha y hora de la ultima actualizacion.
  final DateTime updatedAt;

  /// Construye una sede a partir de una respuesta JSON de FastAPI.
  factory Venue.fromJson(Map<String, dynamic> json) {
    return Venue(
      id: json['id'] as int,
      name: json['name'] as String,
      address: json['address'] as String,
      openingTime: json['opening_time'] as String,
      closingTime: json['closing_time'] as String,
      isActive: json['is_active'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Genera el cuerpo JSON necesario para crear una sede.
  ///
  /// El identificador, el estado y las fechas no se envian porque
  /// esos valores son administrados por FastAPI y PostgreSQL.
  Map<String, dynamic> toCreateJson() {
    return {
      'name': name,
      'address': address,
      'opening_time': openingTime,
      'closing_time': closingTime,
    };
  }

  /// Crea una nueva instancia reemplazando solamente algunos valores.
  ///
  /// Este metodo facilita actualizar la interfaz sin modificar
  /// directamente un objeto existente.
  Venue copyWith({
    int? id,
    String? name,
    String? address,
    String? openingTime,
    String? closingTime,
    bool? isActive,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Venue(
      id: id ?? this.id,
      name: name ?? this.name,
      address: address ?? this.address,
      openingTime: openingTime ?? this.openingTime,
      closingTime: closingTime ?? this.closingTime,
      isActive: isActive ?? this.isActive,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

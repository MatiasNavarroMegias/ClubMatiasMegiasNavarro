/// Representa el perfil publico del usuario autenticado.
///
/// La clase refleja UserResponse del backend y no contiene contrasena
/// ni password_hash.
class AuthenticatedUser {
  const AuthenticatedUser({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.birthDate,
    required this.email,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Identificador generado por PostgreSQL.
  final int id;

  /// Nombre editable del usuario.
  final String firstName;

  /// Apellido editable del usuario.
  final String lastName;

  /// Fecha de nacimiento editable.
  final DateTime birthDate;

  /// Correo inmutable utilizado para autenticacion.
  final String email;

  /// Indica si la cuenta puede iniciar y mantener sesiones.
  final bool isActive;

  /// Fecha de creacion de la cuenta.
  final DateTime createdAt;

  /// Fecha de la ultima actualizacion.
  final DateTime updatedAt;

  /// Nombre completo utilizado por la interfaz.
  String get fullName => '$firstName $lastName';

  /// Construye el perfil desde una respuesta JSON de FastAPI.
  factory AuthenticatedUser.fromJson(Map<String, dynamic> json) {
    return AuthenticatedUser(
      id: json['id'] as int,
      firstName: json['first_name'] as String,
      lastName: json['last_name'] as String,
      birthDate: DateTime.parse(json['birth_date'] as String),
      email: json['email'] as String,
      isActive: json['is_active'] as bool,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  /// Crea una copia modificando solamente los valores indicados.
  AuthenticatedUser copyWith({
    int? id,
    String? firstName,
    String? lastName,
    DateTime? birthDate,
    String? email,
    bool? isActive,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return AuthenticatedUser(
      id: id ?? this.id,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      birthDate: birthDate ?? this.birthDate,
      email: email ?? this.email,
      isActive: isActive ?? this.isActive,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}

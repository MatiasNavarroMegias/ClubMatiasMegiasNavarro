/// Representa una instalacion registrada para recibir notificaciones.
///
/// El modelo contiene la informacion publica devuelta por
/// POST /push-devices.
class PushDevice {
  const PushDevice({
    required this.id,
    required this.userId,
    required this.installationId,
    required this.platform,
    required this.isActive,
    required this.createdAt,
    required this.updatedAt,
  });

  /// Identificador interno asignado por PostgreSQL.
  final int id;

  /// Usuario propietario de la instalacion.
  final int userId;

  /// Identificador de instalacion entregado por Firebase.
  final String installationId;

  /// Plataforma desde la que se registro la aplicacion.
  final String platform;

  /// Indica si la instalacion puede recibir notificaciones.
  final bool isActive;

  /// Fecha del primer registro de la instalacion.
  final DateTime createdAt;

  /// Fecha de la ultima actualizacion.
  final DateTime updatedAt;

  /// Construye un dispositivo desde la respuesta JSON del backend.
  factory PushDevice.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final userId = json['user_id'];
    final installationId = json['installation_id'];
    final platform = json['platform'];
    final isActive = json['is_active'];
    final createdAt = json['created_at'];
    final updatedAt = json['updated_at'];

    if (id is! int ||
        userId is! int ||
        installationId is! String ||
        installationId.isEmpty ||
        platform is! String ||
        platform.isEmpty ||
        isActive is! bool ||
        createdAt is! String ||
        updatedAt is! String) {
      throw const FormatException(
        'La API devolvio un dispositivo push invalido.',
      );
    }

    final parsedCreatedAt = DateTime.tryParse(createdAt);
    final parsedUpdatedAt = DateTime.tryParse(updatedAt);

    if (parsedCreatedAt == null || parsedUpdatedAt == null) {
      throw const FormatException(
        'La API devolvio un dispositivo push invalido.',
      );
    }

    return PushDevice(
      id: id,
      userId: userId,
      installationId: installationId,
      platform: platform,
      isActive: isActive,
      createdAt: parsedCreatedAt,
      updatedAt: parsedUpdatedAt,
    );
  }
}

import 'dart:async';

/// Conserva temporalmente el Firebase Installation ID actual.
///
/// Firebase puede entregar el identificador antes o despues de que el
/// usuario inicie sesion. Este almacenamiento permite conservar el
/// ultimo valor recibido e informar futuros cambios.
class PushInstallationStore {
  /// Controlador que informa identificadores nuevos.
  ///
  /// broadcast permite que mas de un componente escuche los cambios
  /// sin limitar el stream a una sola suscripcion.
  final StreamController<String> _installationIdController =
      StreamController<String>.broadcast();

  String? _currentInstallationId;

  /// Ultimo identificador valido entregado por Firebase.
  String? get currentInstallationId => _currentInstallationId;

  /// Informa cada identificador diferente recibido.
  Stream<String> get installationIds => _installationIdController.stream;

  /// Conserva e informa un identificador entregado por Firebase.
  ///
  /// Los espacios externos se eliminan. Los valores vacios y los
  /// identificadores repetidos se ignoran.
  void update(String installationId) {
    final normalizedInstallationId = installationId.trim();

    if (normalizedInstallationId.isEmpty ||
        normalizedInstallationId == _currentInstallationId) {
      return;
    }

    _currentInstallationId = normalizedInstallationId;
    _installationIdController.add(normalizedInstallationId);
  }

  /// Libera el controlador utilizado por el stream.
  void dispose() {
    _installationIdController.close();
  }
}

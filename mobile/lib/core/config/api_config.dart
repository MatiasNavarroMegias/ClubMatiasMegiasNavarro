/// Centraliza la configuracion necesaria para comunicarse con la API.
///
/// Android Emulator utiliza 10.0.2.2 para acceder al localhost
/// de la computadora donde se ejecuta FastAPI.
abstract final class ApiConfig {
  /// Direccion base utilizada por los servicios remotos.
  ///
  /// El valor puede reemplazarse al ejecutar Flutter mediante:
  ///
  /// flutter run --dart-define=API_BASE_URL=https://api.example.com
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  // La clase contiene solamente configuraciones estaticas.
  const ApiConfig._();
}

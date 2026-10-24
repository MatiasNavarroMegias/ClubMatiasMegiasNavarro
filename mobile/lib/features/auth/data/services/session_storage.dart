import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Define las operaciones utilizadas para conservar la sesion.
///
/// La abstraccion permite utilizar almacenamiento seguro en el
/// dispositivo y una implementacion en memoria durante las pruebas.
abstract interface class SessionStorage {
  Future<String?> readToken();

  Future<void> saveToken(String token);

  Future<void> deleteToken();
}

/// Conserva el JWT mediante el almacenamiento seguro del sistema.
///
/// En Android, flutter_secure_storage utiliza los mecanismos protegidos
/// disponibles en el dispositivo para evitar guardar el token como
/// texto plano dentro de preferencias comunes.
class SecureSessionStorage implements SessionStorage {
  SecureSessionStorage({FlutterSecureStorage? secureStorage})
    : _secureStorage = secureStorage ?? const FlutterSecureStorage();

  static const String _accessTokenKey = 'access_token';

  final FlutterSecureStorage _secureStorage;

  @override
  Future<String?> readToken() {
    return _secureStorage.read(key: _accessTokenKey);
  }

  @override
  Future<void> saveToken(String token) {
    return _secureStorage.write(key: _accessTokenKey, value: token);
  }

  @override
  Future<void> deleteToken() {
    return _secureStorage.delete(key: _accessTokenKey);
  }
}

/// Almacenamiento simple utilizado durante las pruebas.
///
/// Evita acceder al almacenamiento nativo cuando se ejecutan pruebas
/// unitarias o de widgets.
class MemorySessionStorage implements SessionStorage {
  MemorySessionStorage({String? initialToken}) : _token = initialToken;

  String? _token;

  @override
  Future<String?> readToken() async {
    return _token;
  }

  @override
  Future<void> saveToken(String token) async {
    _token = token;
  }

  @override
  Future<void> deleteToken() async {
    _token = null;
  }
}

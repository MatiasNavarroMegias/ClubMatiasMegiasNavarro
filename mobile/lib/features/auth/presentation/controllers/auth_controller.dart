import 'dart:async';
import 'dart:developer' as developer;

import 'package:flutter/foundation.dart';

import '../../../notifications/data/services/push_device_api_client.dart';
import '../../../notifications/data/services/push_installation_store.dart';
import '../../data/models/authenticated_user.dart';
import '../../data/models/profile_update_data.dart';
import '../../data/models/registration_data.dart';
import '../../data/services/auth_api_client.dart';
import '../../data/services/session_storage.dart';

/// Representa el estado general de autenticacion de la aplicacion.
enum AuthStatus {
  /// La aplicacion todavia esta comprobando si existe una sesion.
  initializing,

  /// No existe una sesion valida.
  unauthenticated,

  /// Existe una operacion de autenticacion en progreso.
  loading,

  /// Existe una sesion valida y un usuario autenticado.
  authenticated,
}

/// Coordina el cliente HTTP, el almacenamiento seguro y la interfaz.
///
/// AuthController centraliza el token, el usuario actual y los errores.
/// Las pantallas escuchan sus cambios mediante ChangeNotifier.
class AuthController extends ChangeNotifier {
  /// Construye el controlador utilizando dependencias reemplazables.
  ///
  /// Los parametros publicos conservan nombres claros para facilitar
  /// la construccion desde ClubApp y desde las pruebas automatizadas.
  factory AuthController({
    required AuthApiClient apiClient,
    required SessionStorage sessionStorage,
    PushDeviceApiClient? pushDeviceApiClient,
    PushInstallationStore? pushInstallationStore,
  }) {
    return AuthController._(
      apiClient,
      sessionStorage,
      pushDeviceApiClient,
      pushInstallationStore,
    );
  }

  AuthController._(
    this._apiClient,
    this._sessionStorage,
    this._pushDeviceApiClient,
    this._pushInstallationStore,
  ) {
    _pushInstallationSubscription = _pushInstallationStore?.installationIds
        .listen(_handleInstallationId);
  }

  final AuthApiClient _apiClient;
  final SessionStorage _sessionStorage;
  final PushDeviceApiClient? _pushDeviceApiClient;
  final PushInstallationStore? _pushInstallationStore;

  StreamSubscription<String>? _pushInstallationSubscription;

  AuthStatus _status = AuthStatus.initializing;
  AuthenticatedUser? _currentUser;
  String? _accessToken;
  String? _errorMessage;

  /// Estado actual de la sesion.
  AuthStatus get status => _status;

  /// Usuario autenticado o null si no existe una sesion valida.
  AuthenticatedUser? get currentUser => _currentUser;

  /// Token de acceso utilizado por las operaciones autenticadas.
  ///
  /// El valor solamente puede leerse desde fuera del controlador.
  /// AuthController continua siendo el unico responsable de guardarlo,
  /// actualizarlo y eliminarlo.
  String? get accessToken => _accessToken;

  /// Ultimo mensaje de error visible para la interfaz.
  String? get errorMessage => _errorMessage;

  /// Indica que existe una operacion asincronica en progreso.
  bool get isLoading =>
      _status == AuthStatus.initializing || _status == AuthStatus.loading;

  /// Comprueba si existe una sesion almacenada al iniciar la app.
  Future<void> initialize() async {
    _status = AuthStatus.initializing;
    _errorMessage = null;
    notifyListeners();

    final storedToken = await _sessionStorage.readToken();

    if (storedToken == null || storedToken.isEmpty) {
      _setUnauthenticated();
      return;
    }

    try {
      final user = await _apiClient.getCurrentUser(accessToken: storedToken);

      _accessToken = storedToken;
      _currentUser = user;
      _status = AuthStatus.authenticated;
      notifyListeners();

      await _registerCurrentPushDevice();
    } on AuthApiException {
      // Si el token almacenado vencio, fue alterado o ya no identifica
      // una cuenta valida, se elimina para evitar reutilizarlo.
      await _sessionStorage.deleteToken();
      _setUnauthenticated();
    }
  }

  /// Inicia sesion y almacena el JWT de forma segura.
  ///
  /// Devuelve true cuando el login y la consulta del perfil fueron
  /// exitosos. Devuelve false y conserva el mensaje visible cuando
  /// alguna operacion falla.
  Future<bool> login({required String email, required String password}) async {
    _beginOperation();

    try {
      final session = await _apiClient.login(email: email, password: password);

      await _sessionStorage.saveToken(session.accessToken);

      final user = await _apiClient.getCurrentUser(
        accessToken: session.accessToken,
      );

      _accessToken = session.accessToken;
      _currentUser = user;
      _status = AuthStatus.authenticated;
      _errorMessage = null;
      notifyListeners();

      await _registerCurrentPushDevice();

      return true;
    } on AuthApiException catch (error) {
      // Si el login o la consulta del perfil falla, se elimina cualquier
      // token que pudiera haberse almacenado durante el proceso.
      await _sessionStorage.deleteToken();

      _accessToken = null;
      _currentUser = null;
      _status = AuthStatus.unauthenticated;
      _errorMessage = error.message;
      notifyListeners();

      return false;
    }
  }

  /// Registra una cuenta e inicia sesion automaticamente.
  ///
  /// La contrasena existe solamente durante el registro y el login
  /// posterior. AuthController no conserva la contrasena.
  Future<bool> register(RegistrationData registrationData) async {
    _beginOperation();

    try {
      await _apiClient.register(registrationData);

      final session = await _apiClient.login(
        email: registrationData.email,
        password: registrationData.password,
      );

      await _sessionStorage.saveToken(session.accessToken);

      final user = await _apiClient.getCurrentUser(
        accessToken: session.accessToken,
      );

      _accessToken = session.accessToken;
      _currentUser = user;
      _status = AuthStatus.authenticated;
      _errorMessage = null;
      notifyListeners();

      await _registerCurrentPushDevice();

      return true;
    } on AuthApiException catch (error) {
      await _sessionStorage.deleteToken();

      _accessToken = null;
      _currentUser = null;
      _status = AuthStatus.unauthenticated;
      _errorMessage = error.message;
      notifyListeners();

      return false;
    }
  }

  /// Actualiza el perfil del usuario autenticado.
  ///
  /// Devuelve false si no existe una sesion o si el backend rechaza
  /// la actualizacion.
  Future<bool> updateProfile(ProfileUpdateData updateData) async {
    final token = _accessToken;

    if (token == null) {
      _setUnauthenticated();
      return false;
    }

    _beginOperation();

    try {
      final updatedUser = await _apiClient.updateProfile(
        accessToken: token,
        updateData: updateData,
      );

      _currentUser = updatedUser;
      _status = AuthStatus.authenticated;
      _errorMessage = null;
      notifyListeners();

      return true;
    } on AuthApiException catch (error) {
      if (error.isUnauthorized) {
        // Un token rechazado deja de ser utilizable y debe eliminarse.
        await logout();
        return false;
      }

      // Para errores de validacion o solicitudes sin cambios se mantiene
      // la sesion activa y se muestra el mensaje recibido.
      _status = AuthStatus.authenticated;
      _errorMessage = error.message;
      notifyListeners();

      return false;
    }
  }

  /// Vuelve a consultar el perfil utilizando el token actual.
  ///
  /// Se utilizara para actualizar los datos visibles cuando la
  /// aplicacion vuelva al primer plano o despues de otra operacion.
  Future<bool> refreshProfile() async {
    final token = _accessToken;

    if (token == null) {
      _setUnauthenticated();
      return false;
    }

    try {
      final user = await _apiClient.getCurrentUser(accessToken: token);

      _currentUser = user;
      _status = AuthStatus.authenticated;
      _errorMessage = null;
      notifyListeners();

      return true;
    } on AuthApiException catch (error) {
      if (error.isUnauthorized) {
        await logout();
        return false;
      }

      _status = AuthStatus.authenticated;
      _errorMessage = error.message;
      notifyListeners();

      return false;
    }
  }

  /// Elimina la sesion local y vuelve al flujo no autenticado.
  Future<void> logout() async {
    await _sessionStorage.deleteToken();
    _setUnauthenticated();
  }

  /// Intenta registrar el identificador conservado actualmente.
  ///
  /// La autenticacion no falla si Firebase todavia no entrego un FID
  /// o si el backend no puede registrar las notificaciones.
  Future<void> _registerCurrentPushDevice() async {
    final installationId = _pushInstallationStore?.currentInstallationId;

    if (installationId == null) {
      return;
    }

    await _registerPushDevice(installationId);
  }

  /// Registra una instalacion cuando existe una sesion valida.
  ///
  /// Los errores push se registran para diagnostico, pero no modifican
  /// el estado de autenticacion ni muestran un error en la interfaz.
  Future<void> _registerPushDevice(String installationId) async {
    final accessToken = _accessToken;
    final pushDeviceApiClient = _pushDeviceApiClient;

    if (_status != AuthStatus.authenticated ||
        accessToken == null ||
        pushDeviceApiClient == null) {
      return;
    }

    try {
      await pushDeviceApiClient.register(
        accessToken: accessToken,
        installationId: installationId,
        platform: 'android',
      );
    } on PushDeviceApiException catch (error, stackTrace) {
      developer.log(
        'No se pudo registrar el dispositivo push.',
        name: 'AuthController',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  /// Procesa un identificador entregado despues de autenticar al usuario.
  void _handleInstallationId(String installationId) {
    unawaited(_registerPushDevice(installationId));
  }

  /// Limpia un error despues de mostrarlo o editar el formulario.
  void clearError() {
    if (_errorMessage == null) {
      return;
    }

    _errorMessage = null;
    notifyListeners();
  }

  /// Prepara el estado para una operacion asincronica.
  void _beginOperation() {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();
  }

  /// Elimina del controlador los datos vinculados con una sesion.
  void _setUnauthenticated() {
    _accessToken = null;
    _currentUser = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  @override
  void dispose() {
    // La cancelacion evita continuar escuchando identificadores cuando
    // el controlador ya no forma parte de la aplicacion.
    unawaited(_pushInstallationSubscription?.cancel());

    // AuthController es propietario de los clientes recibidos y libera
    // sus recursos cuando deja de utilizarse.
    _pushDeviceApiClient?.close();
    _apiClient.close();

    super.dispose();
  }
}

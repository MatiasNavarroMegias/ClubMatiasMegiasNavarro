import 'package:firebase_auth/firebase_auth.dart';

/// Usuario autenticado por Firebase sin exponer el objeto del plugin.
class FirebaseAuthenticatedUser {
  const FirebaseAuthenticatedUser({required this.uid, required this.email});

  final String uid;
  final String email;
}

/// Error controlado producido por Firebase Authentication.
class FirebaseAuthenticationException implements Exception {
  const FirebaseAuthenticationException({
    required this.code,
    required this.message,
  });

  final String code;
  final String message;

  @override
  String toString() => message;
}

/// Abstraccion testeable de las operaciones Firebase Authentication.
abstract interface class FirebaseAuthenticationClient {
  FirebaseAuthenticatedUser? get currentUser;

  Stream<FirebaseAuthenticatedUser?> get idTokenChanges;

  Future<FirebaseAuthenticatedUser> createUser({
    required String email,
    required String password,
  });

  Future<FirebaseAuthenticatedUser> signIn({
    required String email,
    required String password,
  });

  Future<String> getIdToken({bool forceRefresh = false});

  Future<void> signOut();

  Future<void> sendPasswordResetEmail({required String email});
}

/// Implementacion que delega en FirebaseAuth.
class FirebaseAuthClient implements FirebaseAuthenticationClient {
  FirebaseAuthClient({FirebaseAuth? firebaseAuth})
    : _providedFirebaseAuth = firebaseAuth,
      _firebaseAuth = firebaseAuth;

  final FirebaseAuth? _providedFirebaseAuth;
  FirebaseAuth? _firebaseAuth;

  FirebaseAuth? get _auth {
    if (_firebaseAuth != null) {
      return _firebaseAuth;
    }

    try {
      _firebaseAuth = _providedFirebaseAuth ?? FirebaseAuth.instance;
    } on Object {
      return null;
    }

    return _firebaseAuth;
  }

  @override
  FirebaseAuthenticatedUser? get currentUser => _mapUser(_auth?.currentUser);

  @override
  Stream<FirebaseAuthenticatedUser?> get idTokenChanges =>
      _auth?.idTokenChanges().map(_mapUser) ?? const Stream.empty();

  @override
  Future<FirebaseAuthenticatedUser> createUser({
    required String email,
    required String password,
  }) async {
    try {
      final credential = await _requireAuth().createUserWithEmailAndPassword(
        email: email.trim().toLowerCase(),
        password: password,
      );
      return _requireUser(credential.user);
    } on FirebaseAuthException catch (error) {
      throw _mapError(error);
    }
  }

  @override
  Future<FirebaseAuthenticatedUser> signIn({
    required String email,
    required String password,
  }) async {
    try {
      final credential = await _requireAuth().signInWithEmailAndPassword(
        email: email.trim().toLowerCase(),
        password: password,
      );
      return _requireUser(credential.user);
    } on FirebaseAuthException catch (error) {
      throw _mapError(error);
    }
  }

  @override
  Future<String> getIdToken({bool forceRefresh = false}) async {
    final user = _auth?.currentUser;
    if (user == null) {
      throw const FirebaseAuthenticationException(
        code: 'no-current-user',
        message: 'No existe una sesion de Firebase activa.',
      );
    }

    try {
      final token = await user.getIdToken(forceRefresh);
      if (token == null || token.isEmpty) {
        throw const FirebaseAuthenticationException(
          code: 'missing-id-token',
          message: 'Firebase no devolvio un token de identidad.',
        );
      }
      return token;
    } on FirebaseAuthException catch (error) {
      throw _mapError(error);
    }
  }

  @override
  Future<void> signOut() => _auth?.signOut() ?? Future<void>.value();

  @override
  Future<void> sendPasswordResetEmail({required String email}) async {
    try {
      await _requireAuth().sendPasswordResetEmail(
        email: email.trim().toLowerCase(),
      );
    } on FirebaseAuthException catch (error) {
      throw _mapError(error);
    }
  }

  static FirebaseAuthenticatedUser? _mapUser(User? user) {
    if (user == null || user.email == null) {
      return null;
    }

    return FirebaseAuthenticatedUser(uid: user.uid, email: user.email!);
  }

  static FirebaseAuthenticatedUser _requireUser(User? user) {
    final mappedUser = _mapUser(user);
    if (mappedUser == null) {
      throw const FirebaseAuthenticationException(
        code: 'missing-user',
        message: 'Firebase no devolvio un usuario valido.',
      );
    }
    return mappedUser;
  }

  static FirebaseAuthenticationException _mapError(
    FirebaseAuthException error,
  ) {
    final message = switch (error.code) {
      'invalid-credential' ||
      'wrong-password' ||
      'user-not-found' => 'El correo o la contrasena no son correctos.',
      'email-already-in-use' => 'El correo ya pertenece a otra cuenta.',
      'weak-password' => 'La contrasena no cumple los requisitos de Firebase.',
      'user-disabled' => 'La cuenta de Firebase se encuentra deshabilitada.',
      'invalid-email' => 'El correo electronico no es valido.',
      'too-many-requests' =>
        'Demasiados intentos. Intenta nuevamente mas tarde.',
      _ => 'No se pudo completar la autenticacion con Firebase.',
    };

    return FirebaseAuthenticationException(code: error.code, message: message);
  }

  FirebaseAuth _requireAuth() {
    final auth = _auth;
    if (auth == null) {
      throw const FirebaseAuthenticationException(
        code: 'firebase-not-initialized',
        message: 'Firebase Authentication no esta inicializado.',
      );
    }
    return auth;
  }
}

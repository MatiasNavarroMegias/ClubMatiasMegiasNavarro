import 'dart:async';

import 'package:club_matias_megias_navarro/features/auth/data/models/registration_data.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/auth_api_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/firebase_authentication_client.dart';
import 'package:club_matias_megias_navarro/features/auth/data/services/session_storage.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  test('register crea Firebase y completa el perfil local', () async {
    final firebase = FakeFirebaseAuthenticationClient();
    final requests = <http.Request>[];
    final controller = AuthController(
      apiClient: AuthApiClient(
        baseUrl: baseUrl,
        httpClient: MockClient((request) async {
          requests.add(request);
          return http.Response(
            '{"id":8,"first_name":"Ana","last_name":"Gomez",'
            '"birth_date":"1995-02-03","email":"ana@example.com",'
            '"is_active":true,"created_at":"2026-10-23T12:00:00Z",'
            '"updated_at":"2026-10-23T13:00:00Z"}',
            201,
          );
        }),
      ),
      sessionStorage: MemorySessionStorage(),
      firebaseAuthenticationClient: firebase,
    );

    final result = await controller.register(
      RegistrationData(
        firstName: 'Ana',
        lastName: 'Gomez',
        birthDate: DateTime(1995, 2, 3),
        email: 'ana@example.com',
        password: 'password-segura',
      ),
    );

    expect(result, isTrue);
    expect(firebase.createdEmails, ['ana@example.com']);
    expect(requests.single.url.path, '/users/profile');
    expect(requests.single.headers['authorization'], 'Bearer firebase-token');
    expect(requests.single.body, contains('"first_name":"Ana"'));
    expect(requests.single.body, isNot(contains('password')));

    controller.dispose();
  });

  test(
    'reintenta completar el perfil si Firebase ya tiene la cuenta',
    () async {
      final firebase = FakeFirebaseAuthenticationClient(
        createError: const FirebaseAuthenticationException(
          code: 'email-already-in-use',
          message: 'El correo ya pertenece a otra cuenta.',
        ),
      );
      final controller = AuthController(
        apiClient: AuthApiClient(
          baseUrl: baseUrl,
          httpClient: MockClient(
            (_) async => http.Response(
              '{"id":8,"first_name":"Ana","last_name":"Gomez",'
              '"birth_date":"1995-02-03","email":"ana@example.com",'
              '"is_active":true,"created_at":"2026-10-23T12:00:00Z",'
              '"updated_at":"2026-10-23T13:00:00Z"}',
              201,
            ),
          ),
        ),
        sessionStorage: MemorySessionStorage(),
        firebaseAuthenticationClient: firebase,
      );

      expect(
        await controller.register(
          RegistrationData(
            firstName: 'Ana',
            lastName: 'Gomez',
            birthDate: DateTime(1995, 2, 3),
            email: 'ana@example.com',
            password: 'password-segura',
          ),
        ),
        isTrue,
      );
      expect(firebase.signInCount, 1);

      controller.dispose();
    },
  );

  test('refreshProfile solicita un token renovado', () async {
    final firebase = FakeFirebaseAuthenticationClient();
    final controller = AuthController(
      apiClient: AuthApiClient(
        baseUrl: baseUrl,
        httpClient: MockClient(
          (_) async => http.Response(
            '{"id":8,"first_name":"Ana","last_name":"Gomez",'
            '"birth_date":"1995-02-03","email":"ana@example.com",'
            '"is_active":true,"created_at":"2026-10-23T12:00:00Z",'
            '"updated_at":"2026-10-23T13:00:00Z"}',
            200,
          ),
        ),
      ),
      sessionStorage: MemorySessionStorage(),
      firebaseAuthenticationClient: firebase,
    );

    await controller.refreshProfile();

    expect(firebase.forceRefreshValues, [true]);
    controller.dispose();
  });
}

class FakeFirebaseAuthenticationClient implements FirebaseAuthenticationClient {
  FakeFirebaseAuthenticationClient({this.createError});

  final FirebaseAuthenticationException? createError;
  final _changes = StreamController<FirebaseAuthenticatedUser?>.broadcast();
  FirebaseAuthenticatedUser? _currentUser;
  final createdEmails = <String>[];
  final forceRefreshValues = <bool>[];
  int signInCount = 0;

  @override
  FirebaseAuthenticatedUser? get currentUser => _currentUser;

  @override
  Stream<FirebaseAuthenticatedUser?> get idTokenChanges => _changes.stream;

  @override
  Future<FirebaseAuthenticatedUser> createUser({
    required String email,
    required String password,
  }) async {
    if (createError != null) {
      throw createError!;
    }
    createdEmails.add(email);
    _currentUser = FirebaseAuthenticatedUser(uid: 'firebase-uid', email: email);
    return _currentUser!;
  }

  @override
  Future<String> getIdToken({bool forceRefresh = false}) async {
    forceRefreshValues.add(forceRefresh);
    return forceRefresh ? 'refreshed-token' : 'firebase-token';
  }

  @override
  Future<FirebaseAuthenticatedUser> signIn({
    required String email,
    required String password,
  }) async {
    signInCount++;
    _currentUser = FirebaseAuthenticatedUser(uid: 'firebase-uid', email: email);
    return _currentUser!;
  }

  @override
  Future<void> signOut() async {
    _currentUser = null;
  }

  @override
  Future<void> sendPasswordResetEmail({required String email}) async {}
}

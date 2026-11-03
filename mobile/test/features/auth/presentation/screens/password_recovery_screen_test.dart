import 'package:club_matias_megias_navarro/features/auth/data/services/firebase_authentication_client.dart';
import 'package:club_matias_megias_navarro/features/auth/presentation/screens/password_recovery_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  Widget createTestApp(FakeFirebaseAuthenticationClient client) {
    return MaterialApp(
      home: PasswordRecoveryScreen(firebaseAuthenticationClient: client),
    );
  }

  Future<void> enterValidEmail(WidgetTester tester) async {
    await tester.enterText(
      find.byKey(const Key('password-recovery-email-field')),
      ' MATIAS@EXAMPLE.COM ',
    );
    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pump();
  }

  testWidgets('muestra inicialmente solo el formulario de correo', (
    tester,
  ) async {
    await tester.pumpWidget(createTestApp(FakeFirebaseAuthenticationClient()));

    expect(
      find.byKey(const Key('password-recovery-email-field')),
      findsOneWidget,
    );
    expect(
      find.byKey(const Key('password-recovery-request-submit')),
      findsOneWidget,
    );
    expect(find.byKey(const Key('password-recovery-code-field')), findsNothing);
    expect(
      find.byKey(const Key('password-recovery-new-password-field')),
      findsNothing,
    );
    expect(find.text('Enviar enlace'), findsOneWidget);
  });

  testWidgets('envia el enlace y muestra mensaje generico', (tester) async {
    final client = FakeFirebaseAuthenticationClient();
    await tester.pumpWidget(createTestApp(client));

    await enterValidEmail(tester);

    expect(client.resetEmails, ['matias@example.com']);
    expect(find.text(firebasePasswordResetMessage), findsOneWidget);
  });

  testWidgets('correo inexistente mantiene el mensaje generico', (
    tester,
  ) async {
    final client = FakeFirebaseAuthenticationClient(
      error: const FirebaseAuthenticationException(
        code: 'user-not-found',
        message: 'internal user detail',
      ),
    );
    await tester.pumpWidget(createTestApp(client));

    await enterValidEmail(tester);

    expect(find.text(firebasePasswordResetMessage), findsOneWidget);
    expect(find.text('internal user detail'), findsNothing);
  });

  testWidgets('mapea errores Firebase sin mostrar detalles internos', (
    tester,
  ) async {
    final cases = {
      'invalid-email': 'Ingresa un correo electronico valido.',
      'too-many-requests': 'Demasiados intentos. Intenta nuevamente mas tarde.',
      'network-request-failed':
          'No se pudo conectar. Verifica tu conexion e intenta nuevamente.',
      'operation-not-allowed':
          'La recuperacion no esta disponible en este momento.',
      'unexpected':
          'No se pudo enviar el correo. Intenta nuevamente mas tarde.',
    };

    for (final entry in cases.entries) {
      final client = FakeFirebaseAuthenticationClient(
        error: FirebaseAuthenticationException(
          code: entry.key,
          message: 'secret Firebase detail',
        ),
      );
      await tester.pumpWidget(createTestApp(client));

      await enterValidEmail(tester);

      expect(find.text(entry.value), findsOneWidget);
      expect(find.text('secret Firebase detail'), findsNothing);
      await tester.pumpWidget(const SizedBox());
    }
  });

  testWidgets('valida el correo sin llamar Firebase', (tester) async {
    final client = FakeFirebaseAuthenticationClient();
    await tester.pumpWidget(createTestApp(client));

    await tester.tap(find.byKey(const Key('password-recovery-request-submit')));
    await tester.pump();

    expect(find.text('Ingresa tu correo electronico.'), findsOneWidget);
    expect(client.resetEmails, isEmpty);
  });
}

class FakeFirebaseAuthenticationClient implements FirebaseAuthenticationClient {
  FakeFirebaseAuthenticationClient({this.error});

  final FirebaseAuthenticationException? error;
  final resetEmails = <String>[];

  @override
  FirebaseAuthenticatedUser? get currentUser => null;

  @override
  Stream<FirebaseAuthenticatedUser?> get idTokenChanges => const Stream.empty();

  @override
  Future<FirebaseAuthenticatedUser> createUser({
    required String email,
    required String password,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<String> getIdToken({bool forceRefresh = false}) {
    throw UnimplementedError();
  }

  @override
  Future<FirebaseAuthenticatedUser> signIn({
    required String email,
    required String password,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<void> signOut() async {}

  @override
  Future<void> sendPasswordResetEmail({required String email}) async {
    if (error != null) {
      throw error!;
    }
    resetEmails.add(email.trim().toLowerCase());
  }
}

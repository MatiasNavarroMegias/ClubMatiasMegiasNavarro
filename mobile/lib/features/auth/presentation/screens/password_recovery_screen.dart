import 'package:flutter/material.dart';

import '../../data/services/firebase_authentication_client.dart';

const firebasePasswordResetMessage =
    'Si la cuenta existe, recibiras un correo para restablecer la contrasena.';

/// Solicita a Firebase el enlace para restablecer la contrasena.
class PasswordRecoveryScreen extends StatefulWidget {
  const PasswordRecoveryScreen({this.firebaseAuthenticationClient, super.key});

  /// Cliente reemplazable durante las pruebas.
  final FirebaseAuthenticationClient? firebaseAuthenticationClient;

  @override
  State<PasswordRecoveryScreen> createState() => _PasswordRecoveryScreenState();
}

class _PasswordRecoveryScreenState extends State<PasswordRecoveryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();

  late final FirebaseAuthenticationClient _firebaseAuthenticationClient;

  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _firebaseAuthenticationClient =
        widget.firebaseAuthenticationClient ?? FirebaseAuthClient();
  }

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _sendResetLink() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      await _firebaseAuthenticationClient.sendPasswordResetEmail(
        email: _emailController.text,
      );
      if (!mounted) {
        return;
      }
      _showGenericMessage();
    } on FirebaseAuthenticationException catch (error) {
      if (!mounted) {
        return;
      }

      if (error.code == 'user-not-found') {
        _showGenericMessage();
      } else {
        _showMessage(
          _messageForFirebaseError(error.code),
          key: const Key('password-recovery-error-snackbar'),
        );
      }
    } on Object {
      if (!mounted) {
        return;
      }
      _showMessage(
        'No se pudo enviar el correo. Intenta nuevamente mas tarde.',
        key: const Key('password-recovery-error-snackbar'),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showGenericMessage() {
    _showMessage(
      firebasePasswordResetMessage,
      key: const Key('password-recovery-success-snackbar'),
    );
  }

  String _messageForFirebaseError(String code) {
    return switch (code) {
      'invalid-email' => 'Ingresa un correo electronico valido.',
      'too-many-requests' =>
        'Demasiados intentos. Intenta nuevamente mas tarde.',
      'network-request-failed' =>
        'No se pudo conectar. Verifica tu conexion e intenta nuevamente.',
      'operation-not-allowed' =>
        'La recuperacion no esta disponible en este momento.',
      _ => 'No se pudo enviar el correo. Intenta nuevamente mas tarde.',
    };
  }

  void _showMessage(String message, {required Key key}) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(key: key, content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      key: const Key('password-recovery-screen'),
      appBar: AppBar(
        title: const Text('Recuperar contrasena'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Icon(
                          Icons.mark_email_read_outlined,
                          size: 64,
                          color: colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Recuperar contrasena',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Recibiras un enlace de Firebase para restablecer '
                          'tu contrasena.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 28),
                        TextFormField(
                          key: const Key('password-recovery-email-field'),
                          controller: _emailController,
                          enabled: !_isLoading,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.done,
                          autocorrect: false,
                          autofillHints: const [AutofillHints.email],
                          decoration: const InputDecoration(
                            labelText: 'Correo electronico',
                            hintText: 'nombre@example.com',
                            prefixIcon: Icon(Icons.email_outlined),
                          ),
                          validator: _validateEmail,
                          onFieldSubmitted: (_) {
                            if (!_isLoading) {
                              _sendResetLink();
                            }
                          },
                        ),
                        const SizedBox(height: 24),
                        FilledButton(
                          key: const Key('password-recovery-request-submit'),
                          onPressed: _isLoading ? null : _sendResetLink,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: _isLoading
                                ? const SizedBox.square(
                                    dimension: 22,
                                    child: CircularProgressIndicator(
                                      key: Key('password-recovery-loading'),
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('Enviar enlace'),
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextButton(
                          key: const Key('password-recovery-back-login'),
                          onPressed: _isLoading
                              ? null
                              : () => Navigator.of(context).pop(false),
                          child: const Text('Volver al inicio de sesion'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  String? _validateEmail(String? value) {
    final normalizedValue = value?.trim() ?? '';
    if (normalizedValue.isEmpty) {
      return 'Ingresa tu correo electronico.';
    }

    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(normalizedValue)) {
      return 'Ingresa un correo electronico valido.';
    }

    return null;
  }
}

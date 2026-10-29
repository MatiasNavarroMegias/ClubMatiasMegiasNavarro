import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../data/services/auth_api_client.dart';

/// Representa la etapa visible de recuperacion.
enum PasswordRecoveryStep { requestCode, confirmPassword }

/// Permite solicitar un codigo y establecer una nueva contrasena.
class PasswordRecoveryScreen extends StatefulWidget {
  const PasswordRecoveryScreen({this.apiClient, super.key});

  /// Cliente reemplazable durante las pruebas.
  final AuthApiClient? apiClient;

  @override
  State<PasswordRecoveryScreen> createState() {
    return _PasswordRecoveryScreenState();
  }
}

class _PasswordRecoveryScreenState extends State<PasswordRecoveryScreen> {
  final _requestFormKey = GlobalKey<FormState>();
  final _confirmationFormKey = GlobalKey<FormState>();

  final _emailController = TextEditingController();
  final _codeController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _passwordConfirmationController = TextEditingController();

  late final AuthApiClient _apiClient;
  late final bool _ownsApiClient;

  PasswordRecoveryStep _step = PasswordRecoveryStep.requestCode;

  bool _isLoading = false;
  bool _obscureNewPassword = true;
  bool _obscurePasswordConfirmation = true;

  @override
  void initState() {
    super.initState();

    _ownsApiClient = widget.apiClient == null;
    _apiClient = widget.apiClient ?? AuthApiClient();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _codeController.dispose();
    _newPasswordController.dispose();
    _passwordConfirmationController.dispose();

    if (_ownsApiClient) {
      _apiClient.close();
    }

    super.dispose();
  }

  /// Solicita el codigo de recuperacion.
  Future<void> _requestCode() async {
    FocusScope.of(context).unfocus();

    if (!_requestFormKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final message = await _apiClient.requestPasswordRecovery(
        email: _emailController.text,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
        _step = PasswordRecoveryStep.confirmPassword;
      });

      _showMessage(
        message,
        key: const Key('password-recovery-success-snackbar'),
      );
    } on AuthApiException catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
      });

      _showMessage(
        error.message,
        key: const Key('password-recovery-error-snackbar'),
      );
    } on Exception {
      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
      });

      _showMessage(
        'Ocurrio un error inesperado.',
        key: const Key('password-recovery-error-snackbar'),
      );
    }
  }

  /// Confirma el codigo y establece la nueva contrasena.
  Future<void> _confirmRecovery() async {
    FocusScope.of(context).unfocus();

    if (!_confirmationFormKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final message = await _apiClient.confirmPasswordRecovery(
        email: _emailController.text,
        code: _codeController.text,
        newPassword: _newPasswordController.text,
        newPasswordConfirmation: _passwordConfirmationController.text,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
      });

      _showMessage(
        message,
        key: const Key('password-recovery-success-snackbar'),
      );

      Navigator.of(context).pop(true);
    } on AuthApiException catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
      });

      _showMessage(
        error.message,
        key: const Key('password-recovery-error-snackbar'),
      );
    } on Exception {
      if (!mounted) {
        return;
      }

      setState(() {
        _isLoading = false;
      });

      _showMessage(
        'Ocurrio un error inesperado.',
        key: const Key('password-recovery-error-snackbar'),
      );
    }
  }

  /// Regresa al ingreso del correo.
  void _returnToEmailStep() {
    if (_isLoading) {
      return;
    }

    setState(() {
      _step = PasswordRecoveryStep.requestCode;
      _codeController.clear();
      _newPasswordController.clear();
      _passwordConfirmationController.clear();
    });
  }

  /// Muestra u oculta la nueva contrasena.
  void _toggleNewPasswordVisibility() {
    setState(() {
      _obscureNewPassword = !_obscureNewPassword;
    });
  }

  /// Muestra u oculta la confirmacion.
  void _toggleConfirmationVisibility() {
    setState(() {
      _obscurePasswordConfirmation = !_obscurePasswordConfirmation;
    });
  }

  /// Muestra un mensaje temporal.
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
                  child: _step == PasswordRecoveryStep.requestCode
                      ? _buildRequestStep()
                      : _buildConfirmationStep(),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  /// Construye el formulario para solicitar el codigo.
  Widget _buildRequestStep() {
    return Form(
      key: _requestFormKey,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Icon(
            Icons.mark_email_read_outlined,
            size: 64,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'Recuperar contrasena',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Text(
            'Ingresa el correo de tu cuenta para '
            'solicitar un codigo temporal.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
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
                _requestCode();
              }
            },
          ),
          const SizedBox(height: 24),
          FilledButton(
            key: const Key('password-recovery-request-submit'),
            onPressed: _isLoading ? null : _requestCode,
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
                  : const Text('Solicitar codigo'),
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            key: const Key('password-recovery-back-login'),
            onPressed: _isLoading
                ? null
                : () {
                    Navigator.of(context).pop(false);
                  },
            child: const Text('Volver al inicio de sesion'),
          ),
        ],
      ),
    );
  }

  /// Construye el formulario para confirmar la recuperacion.
  Widget _buildConfirmationStep() {
    return Form(
      key: _confirmationFormKey,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Icon(
            Icons.password_outlined,
            size: 64,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'Ingresa el codigo',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Text(
            'Usa el codigo enviado para '
            '${_emailController.text.trim().toLowerCase()}.',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 28),
          TextFormField(
            key: const Key('password-recovery-code-field'),
            controller: _codeController,
            enabled: !_isLoading,
            keyboardType: TextInputType.number,
            textInputAction: TextInputAction.next,
            maxLength: 8,
            inputFormatters: [
              FilteringTextInputFormatter.digitsOnly,
              LengthLimitingTextInputFormatter(8),
            ],
            decoration: const InputDecoration(
              labelText: 'Codigo de recuperacion',
              prefixIcon: Icon(Icons.pin_outlined),
              counterText: '',
            ),
            validator: _validateCode,
          ),
          const SizedBox(height: 16),
          TextFormField(
            key: const Key('password-recovery-new-password-field'),
            controller: _newPasswordController,
            enabled: !_isLoading,
            obscureText: _obscureNewPassword,
            textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: 'Nueva contrasena',
              prefixIcon: const Icon(Icons.lock_outline),
              suffixIcon: IconButton(
                key: const Key('password-recovery-password-visibility'),
                onPressed: _isLoading ? null : _toggleNewPasswordVisibility,
                icon: Icon(
                  _obscureNewPassword
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                ),
              ),
            ),
            validator: _validateNewPassword,
          ),
          const SizedBox(height: 16),
          TextFormField(
            key: const Key('password-recovery-confirmation-field'),
            controller: _passwordConfirmationController,
            enabled: !_isLoading,
            obscureText: _obscurePasswordConfirmation,
            textInputAction: TextInputAction.done,
            decoration: InputDecoration(
              labelText: 'Confirmar contrasena',
              prefixIcon: const Icon(Icons.lock_reset_outlined),
              suffixIcon: IconButton(
                key: const Key('password-recovery-confirmation-visibility'),
                onPressed: _isLoading ? null : _toggleConfirmationVisibility,
                icon: Icon(
                  _obscurePasswordConfirmation
                      ? Icons.visibility_outlined
                      : Icons.visibility_off_outlined,
                ),
              ),
            ),
            validator: _validatePasswordConfirmation,
            onFieldSubmitted: (_) {
              if (!_isLoading) {
                _confirmRecovery();
              }
            },
          ),
          const SizedBox(height: 24),
          FilledButton(
            key: const Key('password-recovery-confirm-submit'),
            onPressed: _isLoading ? null : _confirmRecovery,
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
                  : const Text('Restablecer contrasena'),
            ),
          ),
          const SizedBox(height: 12),
          TextButton(
            key: const Key('password-recovery-change-email'),
            onPressed: _isLoading ? null : _returnToEmailStep,
            child: const Text('Cambiar correo'),
          ),
        ],
      ),
    );
  }

  String? _validateEmail(String? value) {
    final normalizedValue = value?.trim() ?? '';

    if (normalizedValue.isEmpty) {
      return 'Ingresa tu correo electronico.';
    }

    final emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

    if (!emailPattern.hasMatch(normalizedValue)) {
      return 'Ingresa un correo electronico valido.';
    }

    return null;
  }

  String? _validateCode(String? value) {
    final normalizedValue = value?.trim() ?? '';

    if (!RegExp(r'^\d{8}$').hasMatch(normalizedValue)) {
      return 'Ingresa el codigo de ocho digitos.';
    }

    return null;
  }

  String? _validateNewPassword(String? value) {
    final password = value ?? '';

    if (password.length < 8) {
      return 'La contrasena debe tener al menos 8 caracteres.';
    }

    if (password.length > 128) {
      return 'La contrasena no puede superar los 128 caracteres.';
    }

    if (password != password.trim()) {
      return 'La contrasena no puede comenzar ni terminar con espacios.';
    }

    if (!password.contains(RegExp(r'[A-Z]'))) {
      return 'La contrasena debe incluir una letra mayuscula.';
    }

    if (!password.contains(RegExp(r'[a-z]'))) {
      return 'La contrasena debe incluir una letra minuscula.';
    }

    if (!password.contains(RegExp(r'[0-9]'))) {
      return 'La contrasena debe incluir un numero.';
    }

    return null;
  }

  String? _validatePasswordConfirmation(String? value) {
    if (value != _newPasswordController.text) {
      return 'Las contrasenas no coinciden.';
    }

    return null;
  }
}

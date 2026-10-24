import 'package:flutter/material.dart';

import '../controllers/auth_controller.dart';

/// Muestra el formulario utilizado para iniciar sesion.
///
/// La pantalla valida localmente los datos basicos y delega la
/// autenticacion real en AuthController.
class LoginScreen extends StatefulWidget {
  const LoginScreen({
    required this.authController,
    required this.onShowRegistration,
    super.key,
  });

  /// Controlador compartido de autenticacion.
  final AuthController authController;

  /// Accion utilizada para mostrar la pantalla de registro.
  final VoidCallback onShowRegistration;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    widget.authController.addListener(_handleControllerChange);
  }

  @override
  void didUpdateWidget(covariant LoginScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.authController == widget.authController) {
      return;
    }

    oldWidget.authController.removeListener(_handleControllerChange);
    widget.authController.addListener(_handleControllerChange);
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleControllerChange);
    _emailController.dispose();
    _passwordController.dispose();

    super.dispose();
  }

  void _handleControllerChange() {
    if (mounted) {
      setState(() {});
    }
  }

  /// Valida el formulario e intenta iniciar sesion.
  Future<void> _submit() async {
    FocusScope.of(context).unfocus();

    if (!_formKey.currentState!.validate()) {
      return;
    }

    final success = await widget.authController.login(
      email: _emailController.text,
      password: _passwordController.text,
    );

    if (!mounted || success) {
      return;
    }

    final errorMessage = widget.authController.errorMessage;

    if (errorMessage == null) {
      return;
    }

    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          key: const Key('login-error-snackbar'),
          content: Text(errorMessage),
        ),
      );
  }

  /// Alterna la visibilidad de la contrasena.
  void _togglePasswordVisibility() {
    setState(() {
      _obscurePassword = !_obscurePassword;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = widget.authController.status == AuthStatus.loading;
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
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
                          Icons.sports_soccer,
                          size: 64,
                          color: colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'ClubMatiasMegiasNavarro',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Inicia sesion para consultar sedes, '
                          'espacios y reservas.',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 32),
                        TextFormField(
                          key: const Key('login-email-field'),
                          controller: _emailController,
                          enabled: !isLoading,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                          autocorrect: false,
                          autofillHints: const [AutofillHints.email],
                          decoration: const InputDecoration(
                            labelText: 'Correo electronico',
                            hintText: 'nombre@example.com',
                            prefixIcon: Icon(Icons.email_outlined),
                          ),
                          validator: _validateEmail,
                          onChanged: (_) {
                            widget.authController.clearError();
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          key: const Key('login-password-field'),
                          controller: _passwordController,
                          enabled: !isLoading,
                          obscureText: _obscurePassword,
                          textInputAction: TextInputAction.done,
                          autofillHints: const [AutofillHints.password],
                          decoration: InputDecoration(
                            labelText: 'Contrasena',
                            prefixIcon: const Icon(Icons.lock_outline),
                            suffixIcon: IconButton(
                              key: const Key('login-password-visibility'),
                              onPressed: isLoading
                                  ? null
                                  : _togglePasswordVisibility,
                              tooltip: _obscurePassword
                                  ? 'Mostrar contrasena'
                                  : 'Ocultar contrasena',
                              icon: Icon(
                                _obscurePassword
                                    ? Icons.visibility_outlined
                                    : Icons.visibility_off_outlined,
                              ),
                            ),
                          ),
                          validator: _validatePassword,
                          onFieldSubmitted: (_) {
                            if (!isLoading) {
                              _submit();
                            }
                          },
                          onChanged: (_) {
                            widget.authController.clearError();
                          },
                        ),
                        const SizedBox(height: 24),
                        FilledButton(
                          key: const Key('login-submit'),
                          onPressed: isLoading ? null : _submit,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: isLoading
                                ? const SizedBox.square(
                                    dimension: 22,
                                    child: CircularProgressIndicator(
                                      key: Key('login-loading'),
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('Iniciar sesion'),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextButton(
                          key: const Key('login-show-registration'),
                          onPressed: isLoading
                              ? null
                              : widget.onShowRegistration,
                          child: const Text('¿No tenes una cuenta? Registrate'),
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

  /// Valida localmente el correo antes de consultar la API.
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

  /// Valida que la contrasena contenga un valor utilizable.
  String? _validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Ingresa tu contrasena.';
    }

    if (value != value.trim()) {
      return 'La contrasena no puede comenzar ni terminar con espacios.';
    }

    if (value.length > 128) {
      return 'La contrasena no puede superar los 128 caracteres.';
    }

    return null;
  }
}

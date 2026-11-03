import 'package:flutter/material.dart';

import '../../data/models/registration_data.dart';
import '../controllers/auth_controller.dart';

/// Muestra el formulario utilizado para registrar una cuenta.
///
/// La pantalla realiza validaciones locales para mejorar la experiencia,
/// mientras que el backend conserva la validacion definitiva.
class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({
    required this.authController,
    required this.onShowLogin,
    super.key,
  });

  /// Controlador compartido de autenticacion.
  final AuthController authController;

  /// Accion utilizada para regresar al inicio de sesion.
  final VoidCallback onShowLogin;

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _formKey = GlobalKey<FormState>();

  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _passwordConfirmationController = TextEditingController();

  DateTime? _selectedBirthDate;
  bool _obscurePassword = true;
  bool _obscurePasswordConfirmation = true;

  @override
  void initState() {
    super.initState();
    widget.authController.addListener(_handleControllerChange);
  }

  @override
  void didUpdateWidget(covariant RegistrationScreen oldWidget) {
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

    _firstNameController.dispose();
    _lastNameController.dispose();
    _birthDateController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _passwordConfirmationController.dispose();

    super.dispose();
  }

  void _handleControllerChange() {
    if (mounted) {
      setState(() {});
    }
  }

  /// Valida el formulario y solicita el registro de la cuenta.
  Future<void> _submit() async {
    FocusScope.of(context).unfocus();

    if (!_formKey.currentState!.validate()) {
      return;
    }

    final birthDate = _selectedBirthDate;

    if (birthDate == null) {
      _showMessage('Selecciona tu fecha de nacimiento.');
      return;
    }

    final registrationData = RegistrationData(
      firstName: _firstNameController.text,
      lastName: _lastNameController.text,
      birthDate: birthDate,
      email: _emailController.text,
      password: _passwordController.text,
    );

    final success = await widget.authController.register(registrationData);

    if (!mounted || success) {
      return;
    }

    final errorMessage = widget.authController.errorMessage;

    if (errorMessage != null) {
      _showMessage(errorMessage);
    }
  }

  /// Abre el selector nativo de fecha.
  Future<void> _selectBirthDate() async {
    FocusScope.of(context).unfocus();

    final now = DateTime.now();
    final lastAllowedDate = DateTime(
      now.year,
      now.month,
      now.day,
    ).subtract(const Duration(days: 1));

    final selectedDate = await showDatePicker(
      context: context,
      initialDate:
          _selectedBirthDate ?? DateTime(now.year - 18, now.month, now.day),
      firstDate: DateTime(1900),
      lastDate: lastAllowedDate,
      helpText: 'Seleccionar fecha de nacimiento',
      cancelText: 'Cancelar',
      confirmText: 'Aceptar',
    );

    if (selectedDate == null) {
      return;
    }

    setState(() {
      _selectedBirthDate = selectedDate;
      _birthDateController.text = _formatDate(selectedDate);
    });

    widget.authController.clearError();
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          key: const Key('registration-error-snackbar'),
          content: Text(message),
        ),
      );
  }

  void _togglePasswordVisibility() {
    setState(() {
      _obscurePassword = !_obscurePassword;
    });
  }

  void _togglePasswordConfirmationVisibility() {
    setState(() {
      _obscurePasswordConfirmation = !_obscurePasswordConfirmation;
    });
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = widget.authController.status == AuthStatus.loading;
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Crear cuenta'),
        leading: IconButton(
          key: const Key('registration-back-to-login'),
          onPressed: isLoading ? null : widget.onShowLogin,
          tooltip: 'Volver al inicio de sesion',
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Icon(
                          Icons.person_add_alt_1_outlined,
                          size: 56,
                          color: colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Registrate en el club',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Completa tus datos para comenzar a reservar.',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 32),
                        TextFormField(
                          key: const Key('registration-first-name-field'),
                          controller: _firstNameController,
                          enabled: !isLoading,
                          textInputAction: TextInputAction.next,
                          textCapitalization: TextCapitalization.words,
                          autofillHints: const [AutofillHints.givenName],
                          decoration: const InputDecoration(
                            labelText: 'Nombre',
                            prefixIcon: Icon(Icons.person_outline),
                          ),
                          validator: (value) {
                            return _validatePersonName(
                              value,
                              fieldName: 'nombre',
                            );
                          },
                          onChanged: (_) {
                            widget.authController.clearError();
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          key: const Key('registration-last-name-field'),
                          controller: _lastNameController,
                          enabled: !isLoading,
                          textInputAction: TextInputAction.next,
                          textCapitalization: TextCapitalization.words,
                          autofillHints: const [AutofillHints.familyName],
                          decoration: const InputDecoration(
                            labelText: 'Apellido',
                            prefixIcon: Icon(Icons.badge_outlined),
                          ),
                          validator: (value) {
                            return _validatePersonName(
                              value,
                              fieldName: 'apellido',
                            );
                          },
                          onChanged: (_) {
                            widget.authController.clearError();
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          key: const Key('registration-birth-date-field'),
                          controller: _birthDateController,
                          enabled: !isLoading,
                          readOnly: true,
                          onTap: isLoading ? null : _selectBirthDate,
                          decoration: const InputDecoration(
                            labelText: 'Fecha de nacimiento',
                            hintText: 'AAAA-MM-DD',
                            prefixIcon: Icon(Icons.calendar_month_outlined),
                            suffixIcon: Icon(Icons.arrow_drop_down),
                          ),
                          validator: (_) {
                            if (_selectedBirthDate == null) {
                              return 'Selecciona tu fecha de nacimiento.';
                            }

                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          key: const Key('registration-email-field'),
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
                          key: const Key('registration-password-field'),
                          controller: _passwordController,
                          enabled: !isLoading,
                          obscureText: _obscurePassword,
                          textInputAction: TextInputAction.next,
                          autofillHints: const [AutofillHints.newPassword],
                          decoration: InputDecoration(
                            labelText: 'Contrasena',
                            prefixIcon: const Icon(Icons.lock_outline),
                            suffixIcon: IconButton(
                              key: const Key(
                                'registration-password-visibility',
                              ),
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
                          onChanged: (_) {
                            widget.authController.clearError();
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          key: const Key(
                            'registration-password-confirmation-field',
                          ),
                          controller: _passwordConfirmationController,
                          enabled: !isLoading,
                          obscureText: _obscurePasswordConfirmation,
                          textInputAction: TextInputAction.done,
                          autofillHints: const [AutofillHints.newPassword],
                          decoration: InputDecoration(
                            labelText: 'Confirmar contrasena',
                            prefixIcon: const Icon(Icons.lock_reset_outlined),
                            suffixIcon: IconButton(
                              key: const Key(
                                'registration-confirmation-visibility',
                              ),
                              onPressed: isLoading
                                  ? null
                                  : _togglePasswordConfirmationVisibility,
                              tooltip: _obscurePasswordConfirmation
                                  ? 'Mostrar confirmacion'
                                  : 'Ocultar confirmacion',
                              icon: Icon(
                                _obscurePasswordConfirmation
                                    ? Icons.visibility_outlined
                                    : Icons.visibility_off_outlined,
                              ),
                            ),
                          ),
                          validator: _validatePasswordConfirmation,
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
                        Text(
                          'La contrasena debe tener entre 8 y 128 '
                          'caracteres e incluir mayuscula, minuscula '
                          'y numero.',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(height: 16),
                        FilledButton(
                          key: const Key('registration-submit'),
                          onPressed: isLoading ? null : _submit,
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            child: isLoading
                                ? const SizedBox.square(
                                    dimension: 22,
                                    child: CircularProgressIndicator(
                                      key: Key('registration-loading'),
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text('Crear cuenta'),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextButton(
                          key: const Key('registration-show-login'),
                          onPressed: isLoading ? null : widget.onShowLogin,
                          child: const Text(
                            '¿Ya tenes una cuenta? Inicia sesion',
                          ),
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

  String? _validatePersonName(String? value, {required String fieldName}) {
    final normalizedValue = value?.trim() ?? '';

    if (normalizedValue.isEmpty) {
      return 'Ingresa tu $fieldName.';
    }

    if (normalizedValue.length > 50) {
      return 'El $fieldName no puede superar los 50 caracteres.';
    }

    return null;
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

  String? _validatePassword(String? value) {
    final password = value ?? '';

    if (password.isEmpty) {
      return 'Ingresa una contrasena.';
    }

    if (password != password.trim()) {
      return 'La contrasena no puede comenzar ni terminar con espacios.';
    }

    if (password.length < 8) {
      return 'La contrasena debe tener al menos 8 caracteres.';
    }

    if (password.length > 128) {
      return 'La contrasena no puede superar los 128 caracteres.';
    }

    if (!password.contains(RegExp('[A-Z]'))) {
      return 'La contrasena debe incluir una letra mayuscula.';
    }

    if (!password.contains(RegExp('[a-z]'))) {
      return 'La contrasena debe incluir una letra minuscula.';
    }

    if (!password.contains(RegExp('[0-9]'))) {
      return 'La contrasena debe incluir un numero.';
    }

    return null;
  }

  String? _validatePasswordConfirmation(String? value) {
    if (value == null || value.isEmpty) {
      return 'Confirma la contrasena.';
    }

    if (value != _passwordController.text) {
      return 'Las contrasenas no coinciden.';
    }

    return null;
  }

  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }
}

import 'package:flutter/material.dart';

import '../../data/models/profile_update_data.dart';
import '../controllers/auth_controller.dart';

/// Muestra y permite editar el perfil del usuario autenticado.
///
/// El correo permanece visible, pero no puede modificarse. El backend
/// conserva la validacion definitiva de los campos editables.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({required this.authController, super.key});

  final AuthController authController;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();

  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _birthDateController = TextEditingController();
  final _emailController = TextEditingController();

  DateTime? _selectedBirthDate;
  bool _isEditing = false;
  bool _formInitialized = false;

  @override
  void initState() {
    super.initState();
    widget.authController.addListener(_handleControllerChange);
    _loadUserData();
  }

  @override
  void didUpdateWidget(covariant ProfileScreen oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.authController == widget.authController) {
      return;
    }

    oldWidget.authController.removeListener(_handleControllerChange);
    widget.authController.addListener(_handleControllerChange);

    _formInitialized = false;
    _loadUserData();
  }

  @override
  void dispose() {
    widget.authController.removeListener(_handleControllerChange);

    _firstNameController.dispose();
    _lastNameController.dispose();
    _birthDateController.dispose();
    _emailController.dispose();

    super.dispose();
  }

  void _handleControllerChange() {
    if (!mounted) {
      return;
    }

    if (!_isEditing) {
      _loadUserData();
    }

    setState(() {});
  }

  /// Completa el formulario con el usuario almacenado en AuthController.
  void _loadUserData() {
    final user = widget.authController.currentUser;

    if (user == null) {
      return;
    }

    _firstNameController.text = user.firstName;
    _lastNameController.text = user.lastName;
    _selectedBirthDate = user.birthDate;
    _birthDateController.text = _formatDate(user.birthDate);
    _emailController.text = user.email;
    _formInitialized = true;
  }

  /// Activa el modo de edicion.
  void _startEditing() {
    widget.authController.clearError();

    setState(() {
      _isEditing = true;
    });
  }

  /// Descarta modificaciones locales y restaura los datos del usuario.
  void _cancelEditing() {
    widget.authController.clearError();
    _loadUserData();

    setState(() {
      _isEditing = false;
    });
  }

  /// Abre el selector de fecha de nacimiento.
  Future<void> _selectBirthDate() async {
    if (!_isEditing || widget.authController.isLoading) {
      return;
    }

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

  /// Construye solamente los campos cuyo valor fue modificado.
  ProfileUpdateData? _buildUpdateData() {
    final user = widget.authController.currentUser;
    final selectedBirthDate = _selectedBirthDate;

    if (user == null || selectedBirthDate == null) {
      return null;
    }

    final firstName = _firstNameController.text.trim();
    final lastName = _lastNameController.text.trim();

    final firstNameChanged = firstName != user.firstName;
    final lastNameChanged = lastName != user.lastName;
    final birthDateChanged = !_sameDate(selectedBirthDate, user.birthDate);

    if (!firstNameChanged && !lastNameChanged && !birthDateChanged) {
      return null;
    }

    return ProfileUpdateData(
      firstName: firstNameChanged ? firstName : null,
      lastName: lastNameChanged ? lastName : null,
      birthDate: birthDateChanged ? selectedBirthDate : null,
    );
  }

  /// Valida y envía la actualización al backend.
  Future<void> _saveProfile() async {
    FocusScope.of(context).unfocus();

    if (!_formKey.currentState!.validate()) {
      return;
    }

    final updateData = _buildUpdateData();

    if (updateData == null) {
      _showMessage('No realizaste cambios en el perfil.');
      return;
    }

    final success = await widget.authController.updateProfile(updateData);

    if (!mounted) {
      return;
    }

    if (!success) {
      final errorMessage = widget.authController.errorMessage;

      if (errorMessage != null) {
        _showMessage(errorMessage);
      }

      return;
    }

    _loadUserData();

    setState(() {
      _isEditing = false;
    });

    _showMessage('Perfil actualizado correctamente.');
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          key: const Key('profile-message-snackbar'),
          content: Text(message),
        ),
      );
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.authController.currentUser;
    final isLoading = widget.authController.isLoading;
    final colorScheme = Theme.of(context).colorScheme;

    if (!_formInitialized && user != null) {
      _loadUserData();
    }

    return Scaffold(
      backgroundColor: colorScheme.surface,
      appBar: AppBar(
        title: const Text('Mi perfil'),
        backgroundColor: colorScheme.surface,
        surfaceTintColor: Colors.transparent,
        actions: [
          if (!_isEditing)
            IconButton(
              key: const Key('profile-edit'),
              onPressed: isLoading ? null : _startEditing,
              tooltip: 'Editar perfil',
              icon: const Icon(Icons.edit_outlined),
            ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          key: const Key('profile-screen'),
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
          children: [
            Center(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  color: colorScheme.primary.withValues(alpha: 0.18),
                  shape: BoxShape.circle,
                ),
                child: SizedBox.square(
                  dimension: 96,
                  child: Center(
                    child: Text(
                      _profileInitials(user?.firstName, user?.lastName),
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(
                            color: colorScheme.primary,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              user?.fullName ?? 'Usuario',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 6),
            Text(
              user?.email ?? '',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyLarge
                  ?.copyWith(color: colorScheme.onSurfaceVariant),
            ),
            const SizedBox(height: 28),
            Card(
              elevation: 0,
              color: colorScheme.surfaceContainer,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Form(
                  key: _formKey,
                  child: Column(
                    children: [
                      TextFormField(
                        key: const Key('profile-first-name-field'),
                        controller: _firstNameController,
                        enabled: _isEditing && !isLoading,
                        textCapitalization: TextCapitalization.words,
                        textInputAction: TextInputAction.next,
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
                        key: const Key('profile-last-name-field'),
                        controller: _lastNameController,
                        enabled: _isEditing && !isLoading,
                        textCapitalization: TextCapitalization.words,
                        textInputAction: TextInputAction.next,
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
                        key: const Key('profile-birth-date-field'),
                        controller: _birthDateController,
                        enabled: _isEditing && !isLoading,
                        readOnly: true,
                        onTap: _selectBirthDate,
                        decoration: const InputDecoration(
                          labelText: 'Fecha de nacimiento',
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
                        key: const Key('profile-email-field'),
                        controller: _emailController,
                        enabled: false,
                        decoration: const InputDecoration(
                          labelText: 'Correo electronico',
                          prefixIcon: Icon(Icons.email_outlined),
                          helperText: 'El correo no puede modificarse.',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            if (_isEditing) ...[
              FilledButton.icon(
                key: const Key('profile-save'),
                onPressed: isLoading ? null : _saveProfile,
                icon: isLoading
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(
                          key: Key('profile-loading'),
                          strokeWidth: 2,
                        ),
                      )
                    : const Icon(Icons.save_outlined),
                label: const Text('Guardar cambios'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                key: const Key('profile-cancel'),
                onPressed: isLoading ? null : _cancelEditing,
                child: const Text('Cancelar'),
              ),
            ] else ...[
              FilledButton.icon(
                key: const Key('profile-start-editing'),
                onPressed: isLoading ? null : _startEditing,
                icon: const Icon(Icons.edit_outlined),
                label: const Text('Editar perfil'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                key: const Key('profile-logout'),
                onPressed: isLoading ? null : widget.authController.logout,
                icon: const Icon(Icons.logout),
                label: const Text('Cerrar sesion'),
              ),
            ],
          ],
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

  String _profileInitials(String? firstName, String? lastName) {
    final firstInitial = firstName == null || firstName.isEmpty
        ? ''
        : firstName[0];

    final lastInitial = lastName == null || lastName.isEmpty ? '' : lastName[0];

    final initials = '$firstInitial$lastInitial'.toUpperCase();

    return initials.isEmpty ? '?' : initials;
  }

  bool _sameDate(DateTime first, DateTime second) {
    return first.year == second.year &&
        first.month == second.month &&
        first.day == second.day;
  }

  String _formatDate(DateTime value) {
    final year = value.year.toString().padLeft(4, '0');
    final month = value.month.toString().padLeft(2, '0');
    final day = value.day.toString().padLeft(2, '0');

    return '$year-$month-$day';
  }
}

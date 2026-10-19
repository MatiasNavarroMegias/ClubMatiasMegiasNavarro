import 'package:flutter/material.dart';

/// Centraliza los colores utilizados por la aplicacion.
///
/// Mantener los colores en una sola clase evita repetir valores
/// hexadecimales dentro de las pantallas y facilita la creacion
/// de los temas claro y oscuro.
abstract final class AppColors {
  /// Verde principal utilizado en botones, iconos y estados activos.
  static const Color primary = Color(0xFFB8D83D);

  /// Variante oscura del verde principal.
  ///
  /// Puede utilizarse para textos, bordes o elementos que necesiten
  /// mayor contraste sobre fondos claros.
  static const Color primaryDark = Color(0xFF365314);

  /// Fondo principal del modo claro.
  static const Color backgroundLight = Color(0xFFF5F7F2);

  /// Fondo principal del modo oscuro.
  ///
  /// Se utiliza un tono oscuro con un leve matiz verde en lugar
  /// de negro puro para mantener la identidad visual del proyecto.
  static const Color backgroundDark = Color(0xFF080B09);

  /// Superficie utilizada por tarjetas y formularios en modo claro.
  static const Color surfaceLight = Color(0xFFFFFFFF);

  /// Superficie utilizada por tarjetas y formularios en modo oscuro.
  static const Color surfaceDark = Color(0xFF121713);

  /// Color principal de texto para el modo claro.
  static const Color textPrimaryLight = Color(0xFF18211B);

  /// Color principal de texto para el modo oscuro.
  static const Color textPrimaryDark = Color(0xFFF5F7F5);

  /// Color de texto secundario para el modo claro.
  static const Color textSecondaryLight = Color(0xFF667268);

  /// Color de texto secundario para el modo oscuro.
  static const Color textSecondaryDark = Color(0xFFA5AEA7);

  /// Color utilizado para errores y acciones destructivas.
  static const Color error = Color(0xFFD92D20);

  /// Color de error con mayor contraste para el modo oscuro.
  static const Color errorDark = Color(0xFFFF8D8D);

  // La clase solo contiene constantes y no debe instanciarse.
  const AppColors._();
}

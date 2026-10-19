import 'package:flutter/material.dart';

import 'theme/app_theme.dart';

/// Widget principal de ClubMatiasMegiasNavarro.
///
/// Este widget centraliza la configuracion global de MaterialApp,
/// incluyendo el nombre, los temas visuales y la pantalla inicial.
class ClubApp extends StatelessWidget {
  const ClubApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      // Oculta la etiqueta DEBUG que Flutter muestra durante el desarrollo.
      debugShowCheckedModeBanner: false,

      // Nombre utilizado por el sistema operativo y algunas herramientas.
      title: 'ClubMatiasMegiasNavarro',

      // Configuraciones visuales para los modos claro y oscuro.
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,

      // Utiliza automaticamente el tema configurado en el dispositivo.
      themeMode: ThemeMode.system,

      // Pantalla temporal que confirma que la estructura inicial funciona.
      home: const AppShell(),
    );
  }
}

/// Pantalla inicial temporal de la aplicacion.
///
/// Esta pantalla sera reemplazada mas adelante por el flujo de
/// autenticacion o por la pantalla principal del usuario.
class AppShell extends StatelessWidget {
  const AppShell({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ClubMatiasMegiasNavarro')),
      body: const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'Configuracion inicial completada',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}

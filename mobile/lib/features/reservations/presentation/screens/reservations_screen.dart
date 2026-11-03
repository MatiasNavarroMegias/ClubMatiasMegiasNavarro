import 'package:flutter/material.dart';

import '../../data/services/reservation_api_client.dart';
import 'reservation_history_screen.dart';
import 'upcoming_reservations_screen.dart';

/// Agrupa las proximas reservas y el historial del usuario.
///
/// Ambas secciones comparten el token autenticado y el cliente HTTP,
/// pero administran sus consultas y estados de forma independiente.
class ReservationsScreen extends StatelessWidget {
  const ReservationsScreen({
    required this.accessToken,
    this.apiClient,
    super.key,
  });

  /// Token utilizado por las operaciones autenticadas.
  final String accessToken;

  /// Cliente reemplazable durante las pruebas.
  final ReservationApiClient? apiClient;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        key: const Key('reservations-screen'),
        backgroundColor: colorScheme.surface,
        appBar: AppBar(
          title: const Text('Mis reservas'),
          backgroundColor: colorScheme.surface,
          surfaceTintColor: Colors.transparent,
          bottom: const TabBar(
            tabs: [
              Tab(
                key: Key('reservations-upcoming-tab'),
                icon: Icon(Icons.event_available_outlined),
                text: 'Proximas',
              ),
              Tab(
                key: Key('reservations-history-tab'),
                icon: Icon(Icons.history_outlined),
                text: 'Historial',
              ),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            UpcomingReservationsScreen(
              accessToken: accessToken,
              apiClient: apiClient,
              showAppBar: false,
            ),
            ReservationHistoryScreen(
              accessToken: accessToken,
              apiClient: apiClient,
            ),
          ],
        ),
      ),
    );
  }
}

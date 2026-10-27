import 'dart:async';
import 'dart:convert';

import 'package:club_matias_megias_navarro/features/sports_spaces/data/models/sports_space.dart';
import 'package:club_matias_megias_navarro/features/sports_spaces/data/services/sports_space_api_client.dart';
import 'package:club_matias_megias_navarro/features/sports_spaces/presentation/screens/sports_space_list_screen.dart';
import 'package:club_matias_megias_navarro/features/venues/data/models/venue.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const baseUrl = 'http://example.test';

  Venue createVenue({
    int id = 2,
    String name = 'Sede Ramos Mejia',
    bool isActive = true,
  }) {
    return Venue.fromJson({
      'id': id,
      'name': name,
      'address': 'Avenida de Mayo 1000',
      'opening_time': '08:00:00',
      'closing_time': '23:00:00',
      'is_active': isActive,
      'created_at': '2026-10-25T12:00:00Z',
      'updated_at': '2026-10-25T13:00:00Z',
    });
  }

  Map<String, dynamic> sportsSpaceJson({
    int id = 5,
    int venueId = 2,
    String name = 'Cancha de Futbol 1',
    String sportType = 'Futbol',
    int spaceNumber = 1,
    bool isActive = true,
  }) {
    return {
      'id': id,
      'venue_id': venueId,
      'name': name,
      'sport_type': sportType,
      'space_number': spaceNumber,
      'is_active': isActive,
      'created_at': '2026-10-25T12:00:00Z',
      'updated_at': '2026-10-25T13:00:00Z',
    };
  }

  Widget createTestApp({
    required SportsSpaceApiClient apiClient,
    ValueChanged<SportsSpace>? onSportsSpaceSelected,
  }) {
    return MaterialApp(
      home: SportsSpaceListScreen(
        venue: createVenue(),
        apiClient: apiClient,
        onSportsSpaceSelected: onSportsSpaceSelected,
      ),
    );
  }

  testWidgets('muestra el indicador mientras carga los espacios', (
    tester,
  ) async {
    final responseCompleter = Completer<http.Response>();

    final httpClient = MockClient((request) {
      return responseCompleter.future;
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));

    expect(find.byKey(const Key('sports-space-list-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    responseCompleter.complete(
      http.Response(jsonEncode(<Map<String, dynamic>>[]), 200),
    );

    await tester.pumpAndSettle();
  });

  testWidgets('consulta los espacios activos de la sede seleccionada', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      expect(request.method, 'GET');
      expect(request.url.path, '/sports-spaces');
      expect(request.url.queryParameters, {
        'venue_id': '2',
        'is_active': 'true',
      });

      return http.Response(
        jsonEncode([sportsSpaceJson()]),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(find.text('Espacios deportivos'), findsOneWidget);
    expect(find.text('Sede Ramos Mejia'), findsOneWidget);
    expect(find.text('Avenida de Mayo 1000'), findsOneWidget);
    expect(find.text('Cancha de Futbol 1'), findsOneWidget);
    expect(find.byKey(const ValueKey('sports-space-card-5')), findsOneWidget);
  });

  testWidgets('muestra tarjetas y filtros deportivos dinamicos', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          sportsSpaceJson(
            id: 5,
            name: 'Cancha de Futbol 1',
            sportType: 'Futbol',
            spaceNumber: 1,
          ),
          sportsSpaceJson(
            id: 6,
            name: 'Cancha de Tenis 1',
            sportType: 'Tenis',
            spaceNumber: 1,
          ),
          sportsSpaceJson(
            id: 7,
            name: 'Cancha de Futbol 2',
            sportType: 'Futbol',
            spaceNumber: 2,
          ),
        ]),
        200,
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('sports-space-filter-all')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('sports-space-filter-Futbol')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('sports-space-filter-Tenis')),
      findsOneWidget,
    );

    expect(find.byKey(const ValueKey('sports-space-card-5')), findsOneWidget);
    expect(find.byKey(const ValueKey('sports-space-card-6')), findsOneWidget);
    expect(find.byKey(const ValueKey('sports-space-card-7')), findsOneWidget);
  });

  testWidgets('filtra las tarjetas por tipo de deporte', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([
          sportsSpaceJson(
            id: 5,
            name: 'Cancha de Futbol 1',
            sportType: 'Futbol',
          ),
          sportsSpaceJson(id: 6, name: 'Cancha de Tenis 1', sportType: 'Tenis'),
        ]),
        200,
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('sports-space-filter-Tenis')));
    await tester.pumpAndSettle();

    expect(find.text('Cancha de Tenis 1'), findsOneWidget);
    expect(find.text('Cancha de Futbol 1'), findsNothing);

    await tester.tap(find.byKey(const Key('sports-space-filter-all')));
    await tester.pumpAndSettle();

    expect(find.text('Cancha de Tenis 1'), findsOneWidget);
    expect(find.text('Cancha de Futbol 1'), findsOneWidget);
  });

  testWidgets('muestra el estado vacio cuando no existen espacios activos', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      return http.Response(jsonEncode(<Map<String, dynamic>>[]), 200);
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('sports-space-list-empty')), findsOneWidget);
    expect(find.text('No hay espacios disponibles'), findsOneWidget);
    expect(
      find.text(
        'Sede Ramos Mejia todavia no tiene '
        'espacios deportivos activos.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('muestra el error recibido desde la API', (tester) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode({'detail': 'No se pudieron consultar los espacios.'}),
        500,
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('sports-space-list-error')), findsOneWidget);
    expect(find.text('No se pudieron cargar los espacios'), findsOneWidget);
    expect(find.text('No se pudieron consultar los espacios.'), findsOneWidget);
    expect(find.byKey(const Key('sports-space-list-retry')), findsOneWidget);
  });

  testWidgets('reintenta la consulta despues de un error', (tester) async {
    var requestCount = 0;

    final httpClient = MockClient((request) async {
      requestCount++;

      if (requestCount == 1) {
        return http.Response(
          jsonEncode({'detail': 'No se pudieron consultar los espacios.'}),
          500,
        );
      }

      return http.Response(
        jsonEncode([sportsSpaceJson(id: 8, name: 'Cancha Recuperada')]),
        200,
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    expect(requestCount, 1);
    expect(find.byKey(const Key('sports-space-list-error')), findsOneWidget);

    await tester.tap(find.byKey(const Key('sports-space-list-retry')));
    await tester.pumpAndSettle();

    expect(requestCount, 2);
    expect(find.text('Cancha Recuperada'), findsOneWidget);
    expect(find.byKey(const Key('sports-space-list-error')), findsNothing);
  });

  testWidgets('entrega el espacio seleccionado mediante callback', (
    tester,
  ) async {
    SportsSpace? selectedSportsSpace;

    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([sportsSpaceJson(id: 5, name: 'Cancha de Futbol 1')]),
        200,
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(
      createTestApp(
        apiClient: apiClient,
        onSportsSpaceSelected: (sportsSpace) {
          selectedSportsSpace = sportsSpace;
        },
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('sports-space-card-5')));
    await tester.pumpAndSettle();

    expect(selectedSportsSpace, isNotNull);
    expect(selectedSportsSpace?.id, 5);
    expect(selectedSportsSpace?.name, 'Cancha de Futbol 1');
  });

  testWidgets('muestra un mensaje temporal sin callback de seleccion', (
    tester,
  ) async {
    final httpClient = MockClient((request) async {
      return http.Response(
        jsonEncode([sportsSpaceJson(id: 5, name: 'Cancha de Futbol 1')]),
        200,
      );
    });

    final apiClient = SportsSpaceApiClient(
      httpClient: httpClient,
      baseUrl: baseUrl,
    );

    addTearDown(apiClient.close);

    await tester.pumpWidget(createTestApp(apiClient: apiClient));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('sports-space-card-5')));
    await tester.pump();

    expect(
      find.text(
        'Cancha de Futbol 1 se utilizara '
        'para consultar disponibilidad.',
      ),
      findsOneWidget,
    );
  });
}

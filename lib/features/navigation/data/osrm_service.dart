import 'package:dio/dio.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/config/env.dart';
import '../models/models.dart';
import 'package:latlong2/latlong.dart';

class OsrmService {
  Future<List<RouteResult>> getRoute(LatLng origin, LatLng destination) async {
    try {
      final String coordinates = '${origin.longitude},${origin.latitude};${destination.longitude},${destination.latitude}';
      final response = await DioClient.instance.get(
        '${Env.osrmBaseUrl}/route/v1/driving/$coordinates',
        queryParameters: {
          'overview': 'full',
          'geometries': 'geojson',
          'steps': 'true',
          'alternatives': '3'
        },
        options: Options(headers: {
          'User-Agent': 'FloodrixApp/1.0.0 (contact@floodrix.app)',
        })
      );

      final data = response.data;
      if (data != null && data['routes'] != null) {
        List<RouteResult> results = [];
        for (var route in data['routes']) {
          final double distance = (route['distance'] as num).toDouble();
          final double duration = (route['duration'] as num).toDouble();
          final List coords = route['geometry']['coordinates'];
          List<LatLng> geometry = coords.map((c) => LatLng((c[1] as num).toDouble(), (c[0] as num).toDouble())).toList();
          List<RouteStep> parsedSteps = [];
          if (route['legs'] != null && route['legs'].isNotEmpty) {
            final leg = route['legs'][0];
            if (leg['steps'] != null) {
              for (var step in leg['steps']) {
                final maneuver = step['maneuver'] ?? {};
                final locationCoords = maneuver['location'];
                LatLng stepLoc = LatLng(0,0);
                if (locationCoords != null && locationCoords.length == 2) {
                  stepLoc = LatLng((locationCoords[1] as num).toDouble(), (locationCoords[0] as num).toDouble());
                }
                
                String type = maneuver['type'] ?? '';
                String modifier = maneuver['modifier'] ?? '';
                String name = step['name'] ?? '';
                double stepDist = (step['distance'] as num).toDouble();
                
                String instruction = type;
                if (modifier.isNotEmpty) instruction += ' $modifier';
                if (name.isNotEmpty) instruction += ' onto $name';
                if (instruction.trim().isEmpty) instruction = 'Continue';
                
                parsedSteps.add(RouteStep(
                  distance: stepDist,
                  instruction: instruction,
                  type: type,
                  modifier: modifier,
                  location: stepLoc
                ));
              }
            }
          }
          results.add(RouteResult(
            id: 'osrm_${results.length + 1}',
            distance: distance, 
            duration: duration, 
            geometry: geometry, 
            steps: parsedSteps
          ));
        }
        return results;
      }
      throw Exception('No routes found');
    } catch (e) {
      throw Exception('Unable to calculate route: $e');
    }
  }

  Future<List<RouteResult>> evaluateRoutesRisk(List<RouteResult> routes) async {
    try {
      final payload = {
        "routes": routes.map((r) => {
          "route_id": r.id,
          "distance_km": r.distance / 1000.0,
          "eta_minutes": r.duration / 60.0,
          "waypoints": r.geometry.map((ll) => {"latitude": ll.latitude, "longitude": ll.longitude}).toList(),
        }).toList(),
        "cargo_type": "GENERAL"
      };

      print('🚀 [OsrmService] Sending ${routes.length} routes to Backend for Risk Evaluation...');
      print('🚀 [OsrmService] API Endpoint: ${Env.apiBaseUrl}/api/v1/routes/evaluate');

      final response = await DioClient.instance.post(
        '${Env.apiBaseUrl}/api/v1/routes/evaluate',
        data: payload
      );

      print('✅ [OsrmService] Received Response from Backend (Status: ${response.statusCode})');

      final data = response.data;
      if (data != null && data['recommended_route'] != null) {
        print('✅ [OsrmService] Backend selected Recommended Route: ${data['recommended_route']['route_id']} with Risk: ${data['recommended_route']['route_risk']}');
        // Map risks back to RouteResult
        Map<String, dynamic> riskData = {};
        
        final rec = data['recommended_route'];
        riskData[rec['route_id']] = rec;
        
        for (var alt in data['alternative_routes'] ?? []) {
          riskData[alt['route_id']] = alt;
        }

        List<RouteResult> evaluatedRoutes = [];
        for (var r in routes) {
          if (riskData.containsKey(r.id)) {
            final rd = riskData[r.id];
            evaluatedRoutes.add(RouteResult(
              id: r.id,
              distance: r.distance,
              duration: r.duration,
              geometry: r.geometry,
              steps: r.steps,
              riskScore: (rd['route_risk'] as num).toDouble(),
              riskDecision: rd['decision'] as String,
            ));
          } else {
            evaluatedRoutes.add(r);
          }
        }

        // Sort by risk
        evaluatedRoutes.sort((a, b) => a.riskScore.compareTo(b.riskScore));
        return evaluatedRoutes;
      }
      return routes;
    } catch (e) {
      print('Warning: Failed to evaluate routes with backend: $e');
      return routes; // Fallback to raw routes if backend fails
    }
  }
}
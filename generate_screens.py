import os

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

create_dir('lib/screens')

api_mock_content = """
class ApiMockData {
  static const Map<String, dynamic> planRouteRequest = {
    "origin": {"latitude": 10.7867, "longitude": 76.6548},
    "destination": {"latitude": 9.9312, "longitude": 76.2673},
    "cargo_type": "perishable",
    "departure_time": "2026-10-07T11:00:00+05:30"
  };

  static const Map<String, dynamic> planRouteResponse = {
    "recommended_route": {
      "route_id": "R1",
      "distance_km": 178.4,
      "base_eta_minutes": 265,
      "risk_score": 0.21,
      "risk_level": "LOW",
      "eta_best_minutes": 265,
      "eta_worst_minutes": 310
    },
    "alternatives": [
      {
        "route_id": "R2",
        "distance_km": 184.2,
        "base_eta_minutes": 280,
        "risk_score": 0.12,
        "risk_level": "LOW",
        "eta_best_minutes": 280,
        "eta_worst_minutes": 300
      }
    ],
    "decision": "R1"
  };

  static const Map<String, dynamic> singleLocationFloodPrediction = {
    "latitude": 10.0159,
    "longitude": 76.3419,
    "rainfall_1h": 18.4,
    "rainfall_6h": 62.7,
    "rainfall_24h": 141.2,
    "elevation": 12.5,
    "historical_flood_frequency": 0.72,
    "flood_zone": 1
  };

  static const Map<String, dynamic> currentWeatherResponse = {
    "latitude": 10.01,
    "longitude": 76.34,
    "rainfall_1h": 12.4,
    "rainfall_6h": 43.8,
    "rainfall_24h": 112.2,
    "temperature": 27.4,
    "weather_code": 65
  };
  
  static const Map<String, dynamic> activeAlertsResponse = {
    "alerts": [
      {
        "id": "ALT001",
        "type": "FLOOD_RISK",
        "severity": "HIGH",
        "title": "High flood probability ahead",
        "message": "High flood probability detected 8 km ahead.",
        "latitude": 10.12,
        "longitude": 76.34
      }
    ]
  };
}
"""

with open('lib/api_mock.dart', 'w') as f:
    f.write(api_mock_content)

main_dart_content = """
import 'package:flutter/material.dart';
import 'screens/role_selection.dart';
import 'screens/permission_request.dart';
import 'screens/home_dashboard.dart';
import 'screens/plan_trip.dart';
import 'screens/route_options.dart';
import 'screens/route_details.dart';
import 'screens/navigation_live_trip.dart';
import 'screens/live_alerts.dart';
import 'screens/weather_forecast.dart';
import 'screens/flood_risk_map.dart';
import 'screens/my_trips.dart';
import 'screens/profile_settings.dart';

void main() {
  runApp(const FloodrixApp());
}

class FloodrixApp extends StatelessWidget {
  const FloodrixApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FLOODRIX',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        fontFamily: 'Roboto',
      ),
      initialRoute: '/role_selection',
      routes: {
        '/role_selection': (context) => const RoleSelectionScreen(),
        '/permission_request': (context) => const PermissionRequestScreen(),
        '/home_dashboard': (context) => const HomeDashboardScreen(),
        '/plan_trip': (context) => const PlanTripScreen(),
        '/route_options': (context) => const RouteOptionsScreen(),
        '/route_details': (context) => const RouteDetailsScreen(),
        '/navigation_live_trip': (context) => const NavigationLiveTripScreen(),
        '/live_alerts': (context) => const LiveAlertsScreen(),
        '/weather_forecast': (context) => const WeatherForecastScreen(),
        '/flood_risk_map': (context) => const FloodRiskMapScreen(),
        '/my_trips': (context) => const MyTripsScreen(),
        '/profile_settings': (context) => const ProfileSettingsScreen(),
      },
    );
  }
}
"""

with open('lib/main.dart', 'w') as f:
    f.write(main_dart_content)

screens = {
    'role_selection': ("RoleSelectionScreen", "Role Selection", "/permission_request"),
    'permission_request': ("PermissionRequestScreen", "Enable Permissions", "/home_dashboard"),
    'home_dashboard': ("HomeDashboardScreen", "Home Dashboard", "/plan_trip"),
    'plan_trip': ("PlanTripScreen", "Plan Your Trip", "/route_options"),
    'route_options': ("RouteOptionsScreen", "Route Options", "/route_details"),
    'route_details': ("RouteDetailsScreen", "Selected Route", "/navigation_live_trip"),
    'navigation_live_trip': ("NavigationLiveTripScreen", "Navigation", "/home_dashboard"),
    'live_alerts': ("LiveAlertsScreen", "Alerts", None),
    'weather_forecast': ("WeatherForecastScreen", "Weather Forecast", None),
    'flood_risk_map': ("FloodRiskMapScreen", "Flood Risk Map", None),
    'my_trips': ("MyTripsScreen", "My Trips", None),
    'profile_settings': ("ProfileSettingsScreen", "Profile & Settings", None),
}

for filename, (class_name, title, next_route) in screens.items():
    button_code = f"""
            ElevatedButton(
              onPressed: () {{
                Navigator.pushNamed(context, '{next_route}');
              }},
              child: const Text('Continue'),
            )""" if next_route else ""
            
    content = f"""
import 'package:flutter/material.dart';
import '../api_mock.dart';

class {class_name} extends StatelessWidget {{
  const {class_name}({{Key? key}}) : super(key: key);

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{title}'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('{title} Screen UI goes here.'),
            const SizedBox(height: 20),
            {button_code}
          ],
        ),
      ),
    );
  }}
}}
"""
    with open(f'lib/screens/{filename}.dart', 'w') as f:
        f.write(content.strip())

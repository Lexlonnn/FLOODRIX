
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

import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'features/navigation/screens/navigation_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
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
      initialRoute: '/navigation',
      routes: {
        '/navigation': (context) => const NavigationScreen(),
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

import os

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content.strip())

# 4. User Role Selection
role_selection = """
import 'package:flutter/material.dart';

class RoleSelectionScreen extends StatelessWidget {
  const RoleSelectionScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () {}),
        elevation: 0,
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Who are you?', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
            const SizedBox(height: 8),
            const Text('Choose your role to get a personalized experience.', style: TextStyle(color: Colors.grey), textAlign: TextAlign.center),
            const SizedBox(height: 32),
            _buildRoleCard('Driver', 'I drive and deliver goods', Icons.local_shipping, true),
            const SizedBox(height: 16),
            _buildRoleCard('Transport Operator', 'I manage vehicles and deliveries', Icons.business, false),
            const SizedBox(height: 16),
            _buildRoleCard('Admin', 'I manage the system', Icons.admin_panel_settings, false),
            const Spacer(),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/permission_request'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                backgroundColor: Colors.blue[700]
              ),
              child: const Text('Continue', style: TextStyle(fontSize: 16, color: Colors.white)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildRoleCard(String title, String subtitle, IconData icon, bool selected) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: selected ? Colors.blue : Colors.grey.shade300, width: 2),
        borderRadius: BorderRadius.circular(12),
        color: selected ? Colors.blue.withOpacity(0.05) : Colors.white
      ),
      child: Row(
        children: [
          Icon(icon, color: selected ? Colors.blue : Colors.grey, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: selected ? Colors.blue : Colors.black)),
                Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.grey)),
              ],
            ),
          )
        ],
      ),
    );
  }
}
"""

# 5. Permission Request
permission_request = """
import 'package:flutter/material.dart';

class PermissionRequestScreen extends StatelessWidget {
  const PermissionRequestScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        elevation: 0,
        backgroundColor: Colors.white,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Enable Permissions', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
            const SizedBox(height: 32),
            _buildPermissionItem('Location', 'To show your live location and provide real-time alerts', Icons.location_on, Colors.green, true),
            const Divider(height: 32),
            _buildPermissionItem('Notifications', 'To send flood alerts and route updates', Icons.notifications, Colors.redAccent, true),
            const Divider(height: 32),
            _buildPermissionItem('Background Location', 'To track your trip even when the app is in background', Icons.security, Colors.purple, false),
            const Spacer(),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/home_dashboard'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                backgroundColor: Colors.blue[700]
              ),
              child: const Text('Continue', style: TextStyle(fontSize: 16, color: Colors.white)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildPermissionItem(String title, String subtitle, IconData icon, Color iconColor, bool switchValue) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(color: iconColor.withOpacity(0.1), shape: BoxShape.circle),
          child: Icon(icon, color: iconColor),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        ),
        Switch(value: switchValue, onChanged: (val) {}, activeColor: Colors.blue),
      ],
    );
  }
}
"""

# 6. Home Dashboard
home_dashboard = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class HomeDashboardScreen extends StatelessWidget {
  const HomeDashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final weather = ApiMockData.currentWeatherResponse;
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.white,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Good Morning,', style: TextStyle(color: Colors.grey, fontSize: 14)),
            Text('Arjun 👋', style: TextStyle(color: Colors.black, fontSize: 20, fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.notifications_none, color: Colors.black), onPressed: () => Navigator.pushNamed(context, '/live_alerts')),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [BoxShadow(color: Colors.grey.withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 5))]
              ),
              child: Column(
                children: [
                  const Text('No Active Trip', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text('Start a new trip to get safe routes and flood alerts.', style: TextStyle(color: Colors.grey), textAlign: TextAlign.center),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => Navigator.pushNamed(context, '/plan_trip'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue[700],
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12)
                    ),
                    child: const Text('Start New Trip →', style: TextStyle(color: Colors.white)),
                  )
                ],
              ),
            ),
            const SizedBox(height: 20),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              childAspectRatio: 1.5,
              children: [
                _buildGridAction('Plan Route', Icons.alt_route, Colors.green, () => Navigator.pushNamed(context, '/plan_trip')),
                _buildGridAction('Live Map', Icons.map, Colors.blue, () => Navigator.pushNamed(context, '/flood_risk_map')),
                _buildGridAction('My Trips', Icons.work_history, Colors.purple, () => Navigator.pushNamed(context, '/my_trips')),
                _buildGridAction('Alerts', Icons.warning_amber, Colors.orange, () => Navigator.pushNamed(context, '/live_alerts')),
              ],
            ),
            const SizedBox(height: 20),
            const Text("Today's Weather", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/weather_forecast'),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Kochi', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        Text('Moderate Rain', style: TextStyle(color: Colors.blue[800])),
                      ],
                    ),
                    Row(
                      children: [
                        const Icon(Icons.cloud, color: Colors.blue, size: 40),
                        const SizedBox(width: 12),
                        Text('${weather["temperature"]}°C', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                      ],
                    )
                  ],
                ),
              ),
            )
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        selectedItemColor: Colors.blue,
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.map), label: 'Map'),
          BottomNavigationBarItem(icon: Icon(Icons.directions_bus), label: 'Trips'),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: 'Alerts'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
        onTap: (index) {
          if(index == 1) Navigator.pushNamed(context, '/flood_risk_map');
          if(index == 2) Navigator.pushNamed(context, '/my_trips');
          if(index == 3) Navigator.pushNamed(context, '/live_alerts');
          if(index == 4) Navigator.pushNamed(context, '/profile_settings');
        },
      ),
    );
  }

  Widget _buildGridAction(String title, IconData icon, MaterialColor color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 32),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}
"""

# 7. Plan New Trip
plan_trip = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class PlanTripScreen extends StatelessWidget {
  const PlanTripScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final req = ApiMockData.planRouteRequest;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Plan Your Trip', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildInputField('From', 'Palakkad, Kerala', Icons.location_on, Colors.blue),
            const SizedBox(height: 16),
            _buildInputField('To', 'Kochi, Kerala', Icons.location_on, Colors.red),
            const SizedBox(height: 24),
            const Text('Cargo Type', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8)
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: req["cargo_type"],
                  isExpanded: true,
                  items: const [
                    DropdownMenuItem(value: 'perishable', child: Text('Fruits & Vegetables (Perishable)')),
                    DropdownMenuItem(value: 'electronics', child: Text('Electronics')),
                  ],
                  onChanged: (val) {},
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text('Departure Time', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300),
                borderRadius: BorderRadius.circular(8)
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Now'),
                  Icon(Icons.calendar_today, color: Colors.grey, size: 20)
                ],
              ),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: () => Navigator.pushNamed(context, '/route_options'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue[700],
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
              ),
              child: const Text('Find Safe Routes', style: TextStyle(color: Colors.white, fontSize: 16)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInputField(String label, String hint, IconData icon, Color iconColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextField(
          controller: TextEditingController(text: hint),
          decoration: InputDecoration(
            prefixIcon: Icon(icon, color: iconColor),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            contentPadding: const EdgeInsets.symmetric(vertical: 14)
          ),
        )
      ],
    );
  }
}
"""

# 8. Route Options
route_options = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class RouteOptionsScreen extends StatelessWidget {
  const RouteOptionsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final res = ApiMockData.planRouteResponse;
    final r1 = res["recommended_route"];
    final r2 = res["alternatives"][0];
    return Scaffold(
      body: Stack(
        children: [
          Container(
            height: MediaQuery.of(context).size.height * 0.4,
            color: Colors.grey[300], // Mock Map
            child: const Center(child: Text('Map View: Palakkad to Kochi', style: TextStyle(color: Colors.grey, fontSize: 18))),
          ),
          SafeArea(
            child: Align(
              alignment: Alignment.topLeft,
              child: IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.black),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: MediaQuery.of(context).size.height * 0.65,
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24))
              ),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  const Text('Route Options', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  _buildRouteCard(context, 'Route 1', '4h 20m', '178 km', '78%', 'High Risk', Colors.red, false),
                  _buildRouteCard(context, 'Route 2', '4h 40m', '${r1["distance_km"]} km', '${(r1["risk_score"]*100).toInt()}%', 'Recommended', Colors.green, true),
                  _buildRouteCard(context, 'Route 3', '5h 10m', '${r2["distance_km"]} km', '${(r2["risk_score"]*100).toInt()}%', 'Moderate', Colors.orange, false),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildRouteCard(BuildContext context, String title, String time, String distance, String risk, String badge, Color badgeColor, bool selected) {
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, '/route_details'),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: selected ? Colors.blue : Colors.grey.shade300, width: 2),
          borderRadius: BorderRadius.circular(12),
          color: selected ? Colors.blue.withOpacity(0.05) : Colors.white
        ),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: badgeColor, borderRadius: BorderRadius.circular(4)),
                  child: Text(badge, style: const TextStyle(color: Colors.white, fontSize: 12)),
                )
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(time, style: const TextStyle(fontWeight: FontWeight.bold)),
                const Text(' • '),
                Text(distance),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                const Text('Flood Risk: ', style: TextStyle(color: Colors.grey)),
                Text(risk, style: TextStyle(color: badgeColor, fontWeight: FontWeight.bold)),
              ],
            )
          ],
        ),
      ),
    );
  }
}
"""

# 9. Route Details
route_details = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class RouteDetailsScreen extends StatelessWidget {
  const RouteDetailsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final res = ApiMockData.planRouteResponse["recommended_route"];
    return Scaffold(
      body: Stack(
        children: [
          Container(
            height: MediaQuery.of(context).size.height * 0.4,
            color: Colors.green[100], // Mock Map
            child: const Center(child: Text('Map View: Selected Route 2', style: TextStyle(color: Colors.green, fontSize: 18))),
          ),
          SafeArea(
            child: Align(
              alignment: Alignment.topLeft,
              child: IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.black),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              height: MediaQuery.of(context).size.height * 0.65,
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24))
              ),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Route 2 (Recommended)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(color: Colors.green, borderRadius: BorderRadius.circular(4)),
                          child: const Text('Low Risk', style: TextStyle(color: Colors.white, fontSize: 12)),
                        )
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text('4h 40m • ${res["distance_km"]} km', style: const TextStyle(color: Colors.grey)),
                    const Divider(height: 32),
                    _buildDetailRow(Icons.timer, 'Estimated Time', '4h 40m'),
                    const SizedBox(height: 16),
                    _buildDetailRow(Icons.route, 'Distance', '${res["distance_km"]} km'),
                    const SizedBox(height: 16),
                    _buildDetailRow(Icons.warning_amber, 'Flood Risk', '${(res["risk_score"]*100).toInt()}% (${res["risk_level"]})', valColor: Colors.green),
                    const SizedBox(height: 16),
                    _buildDetailRow(Icons.remove_road, 'Road Closures', '0'),
                    const Spacer(),
                    ElevatedButton(
                      onPressed: () => Navigator.pushNamed(context, '/navigation_live_trip'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue[700],
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))
                      ),
                      child: const Text('Start Navigation', style: TextStyle(color: Colors.white, fontSize: 16)),
                    )
                  ],
                ),
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildDetailRow(IconData icon, String label, String value, {Color? valColor}) {
    return Row(
      children: [
        Icon(icon, color: Colors.grey, size: 20),
        const SizedBox(width: 12),
        Text(label, style: const TextStyle(fontSize: 16)),
        const Spacer(),
        Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: valColor ?? Colors.black)),
      ],
    );
  }
}
"""

# 10. Navigation (Live Trip)
navigation = """
import 'package:flutter/material.dart';

class NavigationLiveTripScreen extends StatelessWidget {
  const NavigationLiveTripScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          Container(
            color: Colors.blueGrey[800], // Dark Map Mock
            child: const Center(child: Text('Live Map View', style: TextStyle(color: Colors.white54, fontSize: 18))),
          ),
          SafeArea(
            child: Column(
              children: [
                Container(
                  margin: const EdgeInsets.all(16),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: Colors.blue[900], borderRadius: BorderRadius.circular(12)),
                  child: Row(
                    children: [
                      const Icon(Icons.turn_left, color: Colors.white, size: 40),
                      const SizedBox(width: 16),
                      const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('2.5 km', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                          Text('Continue on NH 544', style: TextStyle(color: Colors.white70, fontSize: 16)),
                        ],
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 16),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.black87, borderRadius: BorderRadius.circular(8)),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.warning, color: Colors.red),
                        SizedBox(width: 8),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Flood Risk Ahead', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            Text('High risk in 8.2 km', style: TextStyle(color: Colors.white70, fontSize: 12)),
                          ],
                        )
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 16),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(color: Colors.red, borderRadius: BorderRadius.circular(8)),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.remove_road, color: Colors.white),
                        SizedBox(width: 8),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Road Closure', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            Text('Alternate route suggested', style: TextStyle(color: Colors.white70, fontSize: 12)),
                          ],
                        )
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.vertical(top: Radius.circular(24))
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Remaining', style: TextStyle(color: Colors.grey)),
                          Text('3h 20m • 142 km', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      ElevatedButton(
                        onPressed: () => Navigator.pushNamedAndRemoveUntil(context, '/home_dashboard', (route)=>false),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24))
                        ),
                        child: const Text('End Trip', style: TextStyle(color: Colors.white, fontSize: 16)),
                      )
                    ],
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}
"""

# 11. Live Alerts
live_alerts = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class LiveAlertsScreen extends StatelessWidget {
  const LiveAlertsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final alert = ApiMockData.activeAlertsResponse["alerts"][0];
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alerts', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.grey[100],
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildTab('All', true),
              _buildTab('Flood', false),
              _buildTab('Road Closure', false),
              _buildTab('Weather', false),
            ],
          ),
          const SizedBox(height: 16),
          _buildAlertCard(Icons.warning, alert["title"], '${alert["message"]}\\nLat: ${alert["latitude"]}, Lng: ${alert["longitude"]}', '2 mins ago', Colors.red),
          _buildAlertCard(Icons.remove_road, 'Road Closure', 'SH 15 • 12 km ahead\\nRoad submerged due to heavy rain.', '15 mins ago', Colors.red),
          _buildAlertCard(Icons.thunderstorm, 'Heavy Rainfall Warning', 'Ernakulam District\\nIMD alert for heavy rainfall in next 6 hours.', '1 hour ago', Colors.orange),
          _buildAlertCard(Icons.alt_route, 'Route Recalculated', 'A safer alternative route has been suggested.', '1 hour ago', Colors.green),
        ],
      ),
    );
  }

  Widget _buildTab(String title, bool selected) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: selected ? Colors.blue : Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        border: selected ? null : Border.all(color: Colors.grey)
      ),
      child: Text(title, style: TextStyle(color: selected ? Colors.white : Colors.black)),
    );
  }

  Widget _buildAlertCard(IconData icon, String title, String msg, String time, Color iconColor) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: iconColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 4),
                  Text(msg, style: const TextStyle(color: Colors.black87)),
                  const SizedBox(height: 8),
                  Text(time, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            )
          ],
        ),
      ),
    );
  }
}
"""

# 12. Weather Forecast
weather_forecast = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class WeatherForecastScreen extends StatelessWidget {
  const WeatherForecastScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final weather = ApiMockData.currentWeatherResponse;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Weather Forecast', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Row(
              children: [
                Icon(Icons.location_on, color: Colors.blue),
                SizedBox(width: 8),
                Text('Kochi, Kerala', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.cloud, color: Colors.blue, size: 80),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${weather["temperature"]}°C', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold)),
                    const Text('Moderate Rain', style: TextStyle(fontSize: 18, color: Colors.grey)),
                  ],
                )
              ],
            ),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildTab('Hourly', true),
                _buildTab('Daily', false),
                _buildTab('7 Days', false),
              ],
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildTimeForecast('Now', '28°', Icons.cloud),
                _buildTimeForecast('1 PM', '27°', Icons.cloud),
                _buildTimeForecast('2 PM', '26°', Icons.thunderstorm),
                _buildTimeForecast('3 PM', '26°', Icons.thunderstorm),
                _buildTimeForecast('4 PM', '25°', Icons.cloud),
              ],
            ),
            const SizedBox(height: 32),
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Rainfall Forecast', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold))
            ),
            const SizedBox(height: 16),
            Container(
              height: 150,
              color: Colors.blue[50],
              child: const Center(child: Text('Bar Chart Mockup (Rainfall)')),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildTab(String title, bool selected) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      decoration: BoxDecoration(
        color: selected ? Colors.blue : Colors.transparent,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(title, style: TextStyle(color: selected ? Colors.white : Colors.black, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildTimeForecast(String time, String temp, IconData icon) {
    return Column(
      children: [
        Text(time, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Icon(icon, color: Colors.blue),
        const SizedBox(height: 8),
        Text(temp, style: const TextStyle(fontWeight: FontWeight.bold)),
      ],
    );
  }
}
"""

# 13. Flood Risk Map
flood_risk_map = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class FloodRiskMapScreen extends StatelessWidget {
  const FloodRiskMapScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final prediction = ApiMockData.singleLocationFloodPrediction;
    return Scaffold(
      body: Stack(
        children: [
          Container(
            color: Colors.blue[100], // Map Mockup
            child: const Center(child: Text('Heatmap Layer View', style: TextStyle(fontSize: 24, color: Colors.blue))),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: TextField(
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.search),
                  hintText: 'Search location...',
                  fillColor: Colors.white,
                  filled: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(30), borderSide: BorderSide.none),
                  contentPadding: const EdgeInsets.all(0)
                ),
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24)
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Low'),
                  const SizedBox(width: 8),
                  Container(width: 40, height: 8, color: Colors.green),
                  Container(width: 40, height: 8, color: Colors.yellow),
                  Container(width: 40, height: 8, color: Colors.red),
                  const SizedBox(width: 8),
                  const Text('High'),
                ],
              ),
            ),
          )
        ],
      ),
    );
  }
}
"""

# 14. My Trips
my_trips = """
import 'package:flutter/material.dart';

class MyTripsScreen extends StatelessWidget {
  const MyTripsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Trips', style: TextStyle(color: Colors.black)),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.grey[100],
      body: Column(
        children: [
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    alignment: Alignment.center,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(color: Colors.blue, borderRadius: BorderRadius.circular(24)),
                    child: const Text('Ongoing', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  )
                ),
                Expanded(
                  child: Container(
                    alignment: Alignment.center,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: const Text('Completed', style: TextStyle(color: Colors.grey, fontWeight: FontWeight.bold)),
                  )
                )
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildTripCard('Palakkad → Kochi', '4h 40m • 184 km', 'In Progress', '18% Risk', Colors.green),
                _buildTripCard('Thrissur → Ernakulam', '5h 10m • 210 km', 'Completed\\n28 Aug 2024', '12% Risk', Colors.green),
                _buildTripCard('Kozhikode → Kochi', '4h 55m • 190 km', 'Completed\\n25 Aug 2024', '35% Risk', Colors.orange),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildTripCard(String title, String subtitle, String status, String risk, Color riskColor) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: Colors.blue[50], shape: BoxShape.circle),
              child: const Icon(Icons.local_shipping, color: Colors.blue),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 4),
                  Text(subtitle, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(status, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: riskColor.withOpacity(0.1), borderRadius: BorderRadius.circular(4)),
                        child: Text(risk, style: TextStyle(color: riskColor, fontSize: 12, fontWeight: FontWeight.bold)),
                      )
                    ],
                  )
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.grey)
          ],
        ),
      ),
    );
  }
}
"""

# 15. Profile & Settings
profile_settings = """
import 'package:flutter/material.dart';

class ProfileSettingsScreen extends StatelessWidget {
  const ProfileSettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      backgroundColor: Colors.white,
      body: SingleChildScrollView(
        child: Column(
          children: [
            const CircleAvatar(
              radius: 40,
              backgroundColor: Colors.grey,
              child: Icon(Icons.person, size: 40, color: Colors.white),
            ),
            const SizedBox(height: 16),
            const Text('Arjun Kumar', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const Text('Driver', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 4),
            const Text('+91 98765 43210', style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 32),
            _buildListTile(Icons.person_outline, 'Edit Profile'),
            _buildListTile(Icons.notifications_none, 'Notifications'),
            _buildListTile(Icons.settings, 'App Settings'),
            _buildListTile(Icons.help_outline, 'Help & Support'),
            _buildListTile(Icons.info_outline, 'About FLOODRIX'),
            const SizedBox(height: 16),
            const ListTile(
              leading: Icon(Icons.logout, color: Colors.red),
              title: Text('Logout', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
              trailing: Icon(Icons.chevron_right, color: Colors.red),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildListTile(IconData icon, String title) {
    return ListTile(
      leading: Icon(icon, color: Colors.black54),
      title: Text(title, style: const TextStyle(fontSize: 16)),
      trailing: const Icon(Icons.chevron_right, color: Colors.grey),
      onTap: () {},
    );
  }
}
"""

screens = {
    'role_selection': role_selection,
    'permission_request': permission_request,
    'home_dashboard': home_dashboard,
    'plan_trip': plan_trip,
    'route_options': route_options,
    'route_details': route_details,
    'navigation_live_trip': navigation,
    'live_alerts': live_alerts,
    'weather_forecast': weather_forecast,
    'flood_risk_map': flood_risk_map,
    'my_trips': my_trips,
    'profile_settings': profile_settings,
}

for filename, content in screens.items():
    write_file(f'lib/screens/{filename}.dart', content)

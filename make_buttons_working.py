import os

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content.strip())

# 4. User Role Selection
role_selection = """
import 'package:flutter/material.dart';

class RoleSelectionScreen extends StatefulWidget {
  const RoleSelectionScreen({Key? key}) : super(key: key);

  @override
  State<RoleSelectionScreen> createState() => _RoleSelectionScreenState();
}

class _RoleSelectionScreenState extends State<RoleSelectionScreen> {
  String selectedRole = 'Driver';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () {
          if (Navigator.canPop(context)) Navigator.pop(context);
        }),
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
            _buildRoleCard('Driver', 'I drive and deliver goods', Icons.local_shipping),
            const SizedBox(height: 16),
            _buildRoleCard('Transport Operator', 'I manage vehicles and deliveries', Icons.business),
            const SizedBox(height: 16),
            _buildRoleCard('Admin', 'I manage the system', Icons.admin_panel_settings),
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

  Widget _buildRoleCard(String title, String subtitle, IconData icon) {
    final bool selected = selectedRole == title;
    return GestureDetector(
      onTap: () {
        setState(() {
          selectedRole = title;
        });
      },
      child: Container(
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
      ),
    );
  }
}
"""

# 5. Permission Request
permission_request = """
import 'package:flutter/material.dart';

class PermissionRequestScreen extends StatefulWidget {
  const PermissionRequestScreen({Key? key}) : super(key: key);

  @override
  State<PermissionRequestScreen> createState() => _PermissionRequestScreenState();
}

class _PermissionRequestScreenState extends State<PermissionRequestScreen> {
  bool locEnabled = true;
  bool notifEnabled = true;
  bool bgLocEnabled = false;

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
            _buildPermissionItem('Location', 'To show your live location and provide real-time alerts', Icons.location_on, Colors.green, locEnabled, (val) => setState(() => locEnabled = val)),
            const Divider(height: 32),
            _buildPermissionItem('Notifications', 'To send flood alerts and route updates', Icons.notifications, Colors.redAccent, notifEnabled, (val) => setState(() => notifEnabled = val)),
            const Divider(height: 32),
            _buildPermissionItem('Background Location', 'To track your trip even when the app is in background', Icons.security, Colors.purple, bgLocEnabled, (val) => setState(() => bgLocEnabled = val)),
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

  Widget _buildPermissionItem(String title, String subtitle, IconData icon, Color iconColor, bool switchValue, Function(bool) onChanged) {
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
        Switch(value: switchValue, onChanged: onChanged, activeColor: Colors.blue),
      ],
    );
  }
}
"""

# 6. Home Dashboard (Stateful to handle nav index)
home_dashboard = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class HomeDashboardScreen extends StatefulWidget {
  const HomeDashboardScreen({Key? key}) : super(key: key);

  @override
  State<HomeDashboardScreen> createState() => _HomeDashboardScreenState();
}

class _HomeDashboardScreenState extends State<HomeDashboardScreen> {
  @override
  Widget build(BuildContext context) {
    final weather = ApiMockData.currentWeatherResponse;
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        automaticallyImplyLeading: false, // Hide back button for home
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
        currentIndex: 0,
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

class PlanTripScreen extends StatefulWidget {
  const PlanTripScreen({Key? key}) : super(key: key);

  @override
  State<PlanTripScreen> createState() => _PlanTripScreenState();
}

class _PlanTripScreenState extends State<PlanTripScreen> {
  String cargoType = 'perishable';
  TimeOfDay? selectedTime;

  @override
  void initState() {
    super.initState();
    cargoType = ApiMockData.planRouteRequest["cargo_type"];
  }

  Future<void> _selectTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.now(),
    );
    if (picked != null && picked != selectedTime) {
      setState(() {
        selectedTime = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
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
                  value: cargoType,
                  isExpanded: true,
                  items: const [
                    DropdownMenuItem(value: 'perishable', child: Text('Fruits & Vegetables (Perishable)')),
                    DropdownMenuItem(value: 'electronics', child: Text('Electronics')),
                    DropdownMenuItem(value: 'general', child: Text('General Cargo')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => cargoType = val);
                  },
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text('Departure Time', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () => _selectTime(context),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8)
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(selectedTime == null ? 'Now' : selectedTime!.format(context)),
                    const Icon(Icons.calendar_today, color: Colors.grey, size: 20)
                  ],
                ),
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

# Live Alerts
live_alerts = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class LiveAlertsScreen extends StatefulWidget {
  const LiveAlertsScreen({Key? key}) : super(key: key);

  @override
  State<LiveAlertsScreen> createState() => _LiveAlertsScreenState();
}

class _LiveAlertsScreenState extends State<LiveAlertsScreen> {
  String selectedTab = 'All';

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
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _buildTab('All'),
                const SizedBox(width: 8),
                _buildTab('Flood'),
                const SizedBox(width: 8),
                _buildTab('Road Closure'),
                const SizedBox(width: 8),
                _buildTab('Weather'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          if (selectedTab == 'All' || selectedTab == 'Flood')
            _buildAlertCard(Icons.warning, alert["title"], '${alert["message"]}\\nLat: ${alert["latitude"]}, Lng: ${alert["longitude"]}', '2 mins ago', Colors.red),
          if (selectedTab == 'All' || selectedTab == 'Road Closure')
            _buildAlertCard(Icons.remove_road, 'Road Closure', 'SH 15 • 12 km ahead\\nRoad submerged due to heavy rain.', '15 mins ago', Colors.red),
          if (selectedTab == 'All' || selectedTab == 'Weather')
            _buildAlertCard(Icons.thunderstorm, 'Heavy Rainfall Warning', 'Ernakulam District\\nIMD alert for heavy rainfall in next 6 hours.', '1 hour ago', Colors.orange),
          if (selectedTab == 'All')
            _buildAlertCard(Icons.alt_route, 'Route Recalculated', 'A safer alternative route has been suggested.', '1 hour ago', Colors.green),
        ],
      ),
    );
  }

  Widget _buildTab(String title) {
    final bool selected = selectedTab == title;
    return GestureDetector(
      onTap: () => setState(() => selectedTab = title),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? Colors.blue : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: selected ? null : Border.all(color: Colors.grey)
        ),
        child: Text(title, style: TextStyle(color: selected ? Colors.white : Colors.black)),
      ),
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

# Weather Forecast
weather_forecast = """
import 'package:flutter/material.dart';
import '../api_mock.dart';

class WeatherForecastScreen extends StatefulWidget {
  const WeatherForecastScreen({Key? key}) : super(key: key);

  @override
  State<WeatherForecastScreen> createState() => _WeatherForecastScreenState();
}

class _WeatherForecastScreenState extends State<WeatherForecastScreen> {
  String selectedTab = 'Hourly';

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
                _buildTab('Hourly'),
                _buildTab('Daily'),
                _buildTab('7 Days'),
              ],
            ),
            const SizedBox(height: 24),
            if (selectedTab == 'Hourly')
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildTimeForecast('Now', '28°', Icons.cloud),
                  _buildTimeForecast('1 PM', '27°', Icons.cloud),
                  _buildTimeForecast('2 PM', '26°', Icons.thunderstorm),
                  _buildTimeForecast('3 PM', '26°', Icons.thunderstorm),
                  _buildTimeForecast('4 PM', '25°', Icons.cloud),
                ],
              )
            else
              const Padding(
                padding: EdgeInsets.all(24.0),
                child: Text('Data not mocked for this tab', style: TextStyle(color: Colors.grey)),
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

  Widget _buildTab(String title) {
    final bool selected = selectedTab == title;
    return GestureDetector(
      onTap: () => setState(() => selectedTab = title),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? Colors.blue : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(title, style: TextStyle(color: selected ? Colors.white : Colors.black, fontWeight: FontWeight.bold)),
      ),
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

# My Trips
my_trips = """
import 'package:flutter/material.dart';

class MyTripsScreen extends StatefulWidget {
  const MyTripsScreen({Key? key}) : super(key: key);

  @override
  State<MyTripsScreen> createState() => _MyTripsScreenState();
}

class _MyTripsScreenState extends State<MyTripsScreen> {
  bool isOngoing = true;

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
                  child: GestureDetector(
                    onTap: () => setState(() => isOngoing = true),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(color: isOngoing ? Colors.blue : Colors.transparent, borderRadius: BorderRadius.circular(24)),
                      child: Text('Ongoing', style: TextStyle(color: isOngoing ? Colors.white : Colors.grey, fontWeight: FontWeight.bold)),
                    ),
                  )
                ),
                Expanded(
                  child: GestureDetector(
                    onTap: () => setState(() => isOngoing = false),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(color: !isOngoing ? Colors.blue : Colors.transparent, borderRadius: BorderRadius.circular(24)),
                      child: Text('Completed', style: TextStyle(color: !isOngoing ? Colors.white : Colors.grey, fontWeight: FontWeight.bold)),
                    ),
                  )
                )
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: isOngoing ? [
                _buildTripCard('Palakkad → Kochi', '4h 40m • 184 km', 'In Progress', '18% Risk', Colors.green),
              ] : [
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

# Profile & Settings
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
            _buildListTile(context, Icons.person_outline, 'Edit Profile'),
            _buildListTile(context, Icons.notifications_none, 'Notifications'),
            _buildListTile(context, Icons.settings, 'App Settings'),
            _buildListTile(context, Icons.help_outline, 'Help & Support'),
            _buildListTile(context, Icons.info_outline, 'About FLOODRIX'),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.logout, color: Colors.red),
              title: const Text('Logout', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
              trailing: const Icon(Icons.chevron_right, color: Colors.red),
              onTap: () {
                // Clear navigator stack and go to role selection
                Navigator.pushNamedAndRemoveUntil(context, '/role_selection', (route) => false);
              },
            )
          ],
        ),
      ),
    );
  }

  Widget _buildListTile(BuildContext context, IconData icon, String title) {
    return ListTile(
      leading: Icon(icon, color: Colors.black54),
      title: Text(title, style: const TextStyle(fontSize: 16)),
      trailing: const Icon(Icons.chevron_right, color: Colors.grey),
      onTap: () {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Tapped $title')));
      },
    );
  }
}
"""

screens = {
    'role_selection': role_selection,
    'permission_request': permission_request,
    'home_dashboard': home_dashboard,
    'plan_trip': plan_trip,
    'live_alerts': live_alerts,
    'weather_forecast': weather_forecast,
    'my_trips': my_trips,
    'profile_settings': profile_settings,
}

for filename, content in screens.items():
    write_file(f'lib/screens/{filename}.dart', content)

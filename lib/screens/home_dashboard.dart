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
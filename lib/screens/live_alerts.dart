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
            _buildAlertCard(Icons.warning, alert["title"], '${alert["message"]}\nLat: ${alert["latitude"]}, Lng: ${alert["longitude"]}', '2 mins ago', Colors.red),
          if (selectedTab == 'All' || selectedTab == 'Road Closure')
            _buildAlertCard(Icons.remove_road, 'Road Closure', 'SH 15 • 12 km ahead\nRoad submerged due to heavy rain.', '15 mins ago', Colors.red),
          if (selectedTab == 'All' || selectedTab == 'Weather')
            _buildAlertCard(Icons.thunderstorm, 'Heavy Rainfall Warning', 'Ernakulam District\nIMD alert for heavy rainfall in next 6 hours.', '1 hour ago', Colors.orange),
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
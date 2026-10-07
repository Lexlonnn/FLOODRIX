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
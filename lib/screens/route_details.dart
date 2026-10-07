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
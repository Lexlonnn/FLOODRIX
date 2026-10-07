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
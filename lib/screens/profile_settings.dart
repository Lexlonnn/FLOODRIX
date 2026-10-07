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
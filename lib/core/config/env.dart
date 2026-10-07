import 'package:flutter_dotenv/flutter_dotenv.dart';

class Env {
  static String get mapTileUrl => dotenv.env['MAP_TILE_URL'] ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  static String get nominatimBaseUrl => dotenv.env['NOMINATIM_BASE_URL'] ?? 'https://nominatim.openstreetmap.org';
  static String get osrmBaseUrl => dotenv.env['OSRM_BASE_URL'] ?? 'https://router.project-osrm.org';
  static String get apiBaseUrl => dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000';
}
import 'package:dio/dio.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/config/env.dart';
import '../models/models.dart';

class NominatimService {
  Future<List<PlaceResult>> searchPlaces(String query) async {
    if (query.trim().isEmpty) return [];
    try {
      final response = await DioClient.instance.get(
        '${Env.nominatimBaseUrl}/search',
        queryParameters: {
          'q': query,
          'format': 'jsonv2',
          'limit': 5,
          'countrycodes': 'in'
        },
        options: Options(headers: {
          'User-Agent': 'FloodrixApp/1.0.0 (contact@floodrix.app)',
          'Accept': 'application/json',
          'Accept-Language': 'en-US,en;q=0.5'
        })
      );
      if (response.data is List) {
        return (response.data as List).map((e) => PlaceResult.fromJson(e)).toList();
      }
      return [];
    } catch (e) {
      throw Exception('Failed to search places: $e');
    }
  }
}
import 'package:dio/dio.dart';

class DioClient {
  static final Dio instance = Dio(BaseOptions(
    headers: {
      'User-Agent': 'floodrix/1.0.0 (contact@example.com)',
    },
  ));
}
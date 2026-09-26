import 'package:dio/dio.dart';

/// Central HTTP client for talking to the FastAPI backend.
/// Every feature module (auth, catalog, cart, orders, pos...) should go
/// through this client so headers/interceptors stay consistent.
class ApiClient {
  ApiClient._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {'Content-Type': 'application/json'},
      ),
    );
  }

  static final ApiClient instance = ApiClient._internal();
  late final Dio _dio;

  /// Backend base URL — override via --dart-define=API_BASE_URL=... at build time.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  Dio get dio => _dio;

  void setAuthToken(String? token) {
    if (token == null) {
      _dio.options.headers.remove('Authorization');
    } else {
      _dio.options.headers['Authorization'] = 'Bearer $token';
    }
  }
}

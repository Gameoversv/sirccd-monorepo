import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class AuthLocalDataSource {
  Future<void> saveToken(String token);
  Future<String?> getToken();
  Future<void> deleteToken();
}

final class AuthLocalDataSourceImpl implements AuthLocalDataSource {
  const AuthLocalDataSourceImpl(this._storage);

  final FlutterSecureStorage _storage;

  static const _tokenKey = 'auth_token';

  @override
  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  @override
  Future<String?> getToken() => _storage.read(key: _tokenKey);

  @override
  Future<void> deleteToken() => _storage.delete(key: _tokenKey);
}

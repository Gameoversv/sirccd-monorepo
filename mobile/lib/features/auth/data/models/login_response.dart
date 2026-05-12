final class LoginResponse {
  const LoginResponse({required this.accessToken});

  final String accessToken;

  factory LoginResponse.fromJson(Map<String, dynamic> json) =>
      LoginResponse(accessToken: json['access_token'] as String);
}

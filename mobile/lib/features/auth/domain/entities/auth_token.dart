import 'package:equatable/equatable.dart';

final class AuthToken extends Equatable {
  const AuthToken({required this.accessToken});

  final String accessToken;

  @override
  List<Object> get props => [accessToken];
}

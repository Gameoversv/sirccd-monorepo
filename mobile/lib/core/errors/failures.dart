import 'package:equatable/equatable.dart';

sealed class Failure extends Equatable implements Exception {
  const Failure(this.message);

  final String message;

  @override
  List<Object> get props => [message];
}

final class NetworkFailure extends Failure {
  const NetworkFailure([super.message = 'Error de red. Verifica tu conexión.']);
}

final class ServerFailure extends Failure {
  const ServerFailure([super.message = 'Error del servidor. Intenta más tarde.']);
}

final class AuthFailure extends Failure {
  const AuthFailure([super.message = 'Credenciales inválidas.']);
}

final class CacheFailure extends Failure {
  const CacheFailure([super.message = 'Error al acceder al almacenamiento local.']);
}

final class UnknownFailure extends Failure {
  const UnknownFailure([super.message = 'Error inesperado.']);
}

final class OfflineFailure extends Failure {
  const OfflineFailure(
      [super.message =
          'Sin conexión. El reporte se guardó y se enviará al reconectar.']);
}

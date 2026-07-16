import 'dart:async';

final class SessionExpiredEvent {
  const SessionExpiredEvent([
    this.message = 'Tu sesion expiro. Inicia sesion nuevamente.',
  ]);

  final String message;
}

final class SessionService {
  final _expiredController = StreamController<SessionExpiredEvent>.broadcast();

  Stream<SessionExpiredEvent> get expired => _expiredController.stream;

  void notifyExpired([
    String message = 'Tu sesion expiro. Inicia sesion nuevamente.',
  ]) {
    if (_expiredController.isClosed) return;
    _expiredController.add(SessionExpiredEvent(message));
  }

  Future<void> dispose() => _expiredController.close();
}

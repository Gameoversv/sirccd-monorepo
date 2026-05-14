import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';

abstract interface class ConnectivityService {
  Stream<bool> get isConnectedStream;
  Future<bool> isConnected();
  void dispose();
}

final class ConnectivityServiceImpl implements ConnectivityService {
  ConnectivityServiceImpl() {
    _connectivity = Connectivity();
    _controller = StreamController<bool>.broadcast();
    _sub = _connectivity.onConnectivityChanged.listen(
      (results) => _controller.add(_online(results)),
    );
  }

  late final Connectivity _connectivity;
  late final StreamController<bool> _controller;
  late final StreamSubscription<List<ConnectivityResult>> _sub;

  static bool _online(List<ConnectivityResult> results) =>
      results.any((r) => r != ConnectivityResult.none);

  @override
  Stream<bool> get isConnectedStream => _controller.stream;

  @override
  Future<bool> isConnected() async {
    final results = await _connectivity.checkConnectivity();
    return _online(results);
  }

  @override
  void dispose() {
    _sub.cancel();
    _controller.close();
  }
}

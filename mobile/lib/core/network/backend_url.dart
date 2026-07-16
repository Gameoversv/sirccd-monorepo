abstract final class BackendUrl {
  static const _apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  static String normalizeAssetUrl(String url) {
    final assetUri = Uri.tryParse(url);
    final apiUri = Uri.tryParse(_apiBaseUrl);

    if (assetUri == null || apiUri == null || !apiUri.hasAuthority) {
      return url;
    }

    if (!assetUri.hasAuthority && url.startsWith('/')) {
      return apiUri
          .replace(
            path: assetUri.path,
            query: assetUri.hasQuery ? assetUri.query : null,
          )
          .toString();
    }

    if (!assetUri.hasAuthority) {
      return url;
    }

    if (!_isLoopbackHost(assetUri.host) || _isLoopbackHost(apiUri.host)) {
      return url;
    }

    return assetUri.replace(host: apiUri.host).toString();
  }

  static String? normalizeNullableAssetUrl(String? url) {
    if (url == null || url.isEmpty) return url;
    return normalizeAssetUrl(url);
  }

  static bool _isLoopbackHost(String host) {
    final value = host.toLowerCase();
    return value == 'localhost' ||
        value == '127.0.0.1' ||
        value == '0.0.0.0' ||
        value == '::1';
  }
}

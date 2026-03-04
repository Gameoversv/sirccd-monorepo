/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Variables de entorno públicas
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
    NEXT_PUBLIC_MAP_CENTER_LAT: process.env.NEXT_PUBLIC_MAP_CENTER_LAT || '19.4517',
    NEXT_PUBLIC_MAP_CENTER_LNG: process.env.NEXT_PUBLIC_MAP_CENTER_LNG || '-70.6970',
    NEXT_PUBLIC_MAP_DEFAULT_ZOOM: process.env.NEXT_PUBLIC_MAP_DEFAULT_ZOOM || '13',
  },

  // Optimizaciones de imágenes
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '9000',
        pathname: '/sirccd-images/**',
      },
    ],
  },

  // Configuración de webpack para Leaflet
  webpack: (config) => {
    config.externals = [...(config.externals || []), { canvas: 'canvas' }];
    return config;
  },
}

module.exports = nextConfig

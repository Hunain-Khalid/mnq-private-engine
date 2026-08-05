import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*', // Automatically proxies to FastAPI
      },
    ];
  },
};

export default nextConfig;
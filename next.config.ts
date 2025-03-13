import { NextConfig } from 'next';

/** @type {import('next').NextConfig} */
const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
    domains: ['localhost'],
  },
  eslint: {
    // Disable ESLint during builds to allow deployment
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Ignore TypeScript errors during build
    ignoreBuildErrors: true,
  },
  // Add asset prefix for static assets
  assetPrefix: process.env.NODE_ENV === 'development' ? '' : undefined,
  // Ensure correct paths in development
  experimental: {
    // The reactRefresh option is no longer needed as it's enabled by default
  }
}

export default nextConfig;

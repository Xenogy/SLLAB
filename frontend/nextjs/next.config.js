/** @type {import('next').NextConfig} */

// Log environment variables for debugging
console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);

const nextConfig = {
  // Environment variables that should be available at runtime
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
  },
  reactStrictMode: true,
  output: 'standalone',

  // Transpile specific packages that might have issues with React 19
  transpilePackages: ['react-day-picker', 'vaul'],

  // Webpack configuration for React 19 compatibility
  webpack: (config, { isServer }) => {
    // Add any necessary webpack configurations for React 19 compatibility

    // Handle packages that might have issues with React 19
    config.resolve.alias = {
      ...config.resolve.alias,
      // Add any necessary aliases here
    };

    return config;
  },

  // Experimental features
  experimental: {
    // Optimize for React 19
    optimizeCss: true,
  },

  // Temporarily disable ESLint during build
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Temporarily disable TypeScript checking during build
  typescript: {
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;

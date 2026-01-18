/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for Kubernetes deployment with nginx
  output: 'export',

  // Disable image optimization for static export (nginx serves static files)
  images: {
    unoptimized: true,
  },

  // Generate trailing slashes for better nginx compatibility
  trailingSlash: true,
};

export default nextConfig;

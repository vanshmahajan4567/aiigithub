/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  transpilePackages: ['next', 'react', 'react-dom'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://github-scrapper-j7qfkck21-vanshs-projects-47c7f723.vercel.app'}/api/:path*`
      }
    ]
  }
}

module.exports = nextConfig 
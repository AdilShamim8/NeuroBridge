const withMDX = require("@next/mdx")({
  extension: /\.(md|mdx)$/
});

const csp = [
  "default-src 'self'",
  // plausible.io serves the analytics script the layout loads; Google Fonts
  // and jsDelivr serve the Atkinson Hyperlegible / OpenDyslexic dyslexia-font
  // stylesheets. Without these entries the CSP silently blocked the site's
  // own accessibility fonts and analytics.
  "script-src 'self' 'unsafe-inline' https://plausible.io",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
  "img-src 'self' data: https:",
  "font-src 'self' https: data:",
  "connect-src 'self' https:",
  "object-src 'none'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'"
].join("; ");

/** @type {import('next').NextConfig} */
const nextConfig = {
  pageExtensions: ["ts", "tsx", "md", "mdx"],
  experimental: {
    typedRoutes: true
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com"
      }
    ]
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }
        ]
      }
    ];
  }
};

module.exports = withMDX(nextConfig);

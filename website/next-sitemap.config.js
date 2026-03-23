/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: "https://neurobridge.dev",
  generateRobotsTxt: false,
  sitemapSize: 5000,
  changefreq: "weekly",
  priority: 0.7,
  exclude: ["/api/*"]
};

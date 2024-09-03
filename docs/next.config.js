const withNextra = require("nextra")({
    theme: "nextra-theme-docs",
    themeConfig: "./theme.config.tsx",
    latex: true,
    defaultShowCopyCode: true,
});

const nextConfig = {
    images: {
        unoptimized: true,
    },
};

module.exports = withNextra(nextConfig);
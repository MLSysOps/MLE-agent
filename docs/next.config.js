const withNextra = require("nextra")({
    theme: "nextra-theme-docs",
    themeConfig: "./theme.config.tsx",
    latex: true,
    defaultShowCopyCode: true,
});

const nextConfig = {
    output: "export",
    images: {
        unoptimized: true,
    },
};

module.exports = withNextra(nextConfig);
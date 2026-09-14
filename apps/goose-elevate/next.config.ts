import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@goose/ui", "@goose/database"],
};

export default nextConfig;

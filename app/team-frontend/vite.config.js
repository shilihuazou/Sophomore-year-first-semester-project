import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const allowedHosts = (process.env.VITE_ALLOWED_HOSTS || "")
  .split(/[;,]/)
  .map((host) => host.trim())
  .filter(Boolean);

export default defineConfig({
  plugins: [vue()],
  server: {
    host: process.env.APP_BIND_ADDRESS || "0.0.0.0",
    port: 5174,
    strictPort: true,
    ...(allowedHosts.length ? { allowedHosts } : {}),
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
});

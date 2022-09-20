import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  // TODO: find solution
  server: {
    // middlewareMode: {
    //   mode: 'ssr',
    //   // parentServer: parentServer // pass the parent server
    // },
    proxy: {
      "/channel": {
        target: "http://0.0.0.0:5556/channel",
        ws: true,
        secure: false,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});

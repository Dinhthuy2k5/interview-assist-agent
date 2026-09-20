import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// VITE_ALLOWED_HOST: set trong .env trên VPS để Vite dev server chấp nhận
// request từ domain ngoài localhost (vd: ngdinhthuy.duckdns.org).
// Khi build production (npm run build), giá trị này không ảnh hưởng gì.
const extraHost = process.env.VITE_ALLOWED_HOST;

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    ...(extraHost ? { allowedHosts: [extraHost] } : {}),
  },
});
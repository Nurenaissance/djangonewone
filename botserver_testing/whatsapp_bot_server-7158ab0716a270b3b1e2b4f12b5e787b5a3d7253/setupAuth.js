import axios from "axios";
import dotenv from "dotenv";

// Use override: true to force .env file to override system environment variables
dotenv.config({ override: true });

// Backend URLs
// const FASTAPI_URL = "http://localhost:8001";
// const DJANGO_URL  = "http://127.0.0.1:8000";


const FASTAPI_URL = "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net";
const DJANGO_URL  = "https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net";

// Default
axios.defaults.baseURL = FASTAPI_URL;

// Service Key for service-to-service authentication
const NODEJS_SERVICE_KEY = process.env.NODEJS_SERVICE_KEY || "sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34";

// -------- LOGGER INTERCEPTOR --------
axios.interceptors.request.use((config) => {

  const finalUrl = config.url.startsWith("http")
    ? config.url
    : `${config.baseURL}${config.url}`;

  console.log("\n----- OUTGOING REQUEST -----");
  console.log("URL:", finalUrl);
  console.log("METHOD:", config.method?.toUpperCase());
  console.log("HEADERS SENT:", config.headers);
  console.log("-----------------------------\n");

  return config;
});

// -------- AUTH INTERCEPTOR --------
axios.interceptors.request.use((config) => {

  // Use X-Service-Key for service-to-service auth (preferred over JWT for internal services)
  if (!config.headers["X-Service-Key"] && !config.headers["Authorization"]) {
    config.headers["X-Service-Key"] = NODEJS_SERVICE_KEY;
  }

  // Auto tenant support
  if (globalThis.currentTenant && !config.headers["X-Tenant-Id"]) {
    config.headers["X-Tenant-Id"] = globalThis.currentTenant;
  }

  return config;
});

// Export helpers
export function useFastAPI() {
  axios.defaults.baseURL = FASTAPI_URL;
}

export function useDjango() {
  axios.defaults.baseURL = DJANGO_URL;
}

export default axios;

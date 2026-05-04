import cors from "cors";
import { AppError } from "../../lib/errors.js";

export function createCorsMiddleware(config) {
  const baseOrigins = config.corsOrigins;

  return cors({
    origin(origin, callback) {
      if (!origin) {
        callback(null, true);
        return;
      }

      if (baseOrigins.length === 0 && config.isDevelopment) {
        callback(null, true);
        return;
      }

      if (baseOrigins.includes(origin)) {
        callback(null, true);
        return;
      }

      callback(new AppError(403, "CORS_FORBIDDEN", `CORS blocked for origin ${origin}`));
    },
    credentials: true,
  });
}

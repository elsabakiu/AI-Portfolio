import { AppError } from "../../lib/errors.js";

const ROLE_ORDER = {
  reviewer: 1,
  approver: 2,
  admin: 3,
};

function parseBearerToken(authorizationHeader) {
  const header = String(authorizationHeader || "");
  if (!header.toLowerCase().startsWith("bearer ")) return null;
  return header.slice(7).trim();
}

export function createAuthMiddleware(config) {
  return function authMiddleware(req, _res, next) {
    if (config.authMode === "disabled") {
      req.actor = {
        userId: "local-dev-user",
        role: "admin",
        displayName: "Local Dev",
        authenticated: false,
      };
      next();
      return;
    }

    if (config.authMode === "headers") {
      const headerUserId = req.headers["x-user-id"];
      const headerRole = req.headers["x-user-role"];

      req.actor = {
        userId: headerUserId ? String(headerUserId) : "local-dev-user",
        role: headerRole ? String(headerRole) : "reviewer",
        displayName: null,
        authenticated: Boolean(headerUserId),
      };
      next();
      return;
    }

    const token = parseBearerToken(req.headers.authorization);
    const matchedToken = config.authTokens.find((entry) => entry.token === token);

    if (!matchedToken) {
      next(
        new AppError(401, "AUTH_REQUIRED", "A valid bearer token is required for this route.")
      );
      return;
    }

    req.actor = {
      userId: matchedToken.userId,
      role: matchedToken.role,
      displayName: matchedToken.displayName,
      authenticated: true,
    };
    next();
  };
}

export function authorizeRoles(allowedRoles) {
  const minimumRank = Math.min(...allowedRoles.map((role) => ROLE_ORDER[role] || Number.MAX_SAFE_INTEGER));

  return (req, _res, next) => {
    const actorRole = req.actor?.role;
    const actorRank = ROLE_ORDER[actorRole] || 0;
    if (!req.actor || actorRank < minimumRank) {
      next(
        new AppError(
          403,
          "FORBIDDEN",
          `This action requires one of the following roles: ${allowedRoles.join(", ")}.`
        )
      );
      return;
    }

    next();
  };
}

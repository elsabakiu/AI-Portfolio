import { Router } from "express";
import { toSuccessResponse } from "../../lib/errors.js";
import { authorizeRoles } from "../middleware/auth.js";
import { validateRequest } from "../middleware/validate.js";
import { validateProposalBody } from "../validators.js";

export function createSubmissionsRouter({ submissionsService }) {
  const router = Router();

  router.post(
    "/send-to-infracloud",
    authorizeRoles(["approver", "admin"]),
    validateRequest({ body: validateProposalBody }),
    async (req, res, next) => {
      try {
        const result = await submissionsService.createSubmission({
          ...req.validated.body,
          actor: req.actor,
          requestId: req.requestId,
        });

        res.json(
          toSuccessResponse(
            {
              sentAt: result.sentAt,
              mode: result.mode,
            },
            req.requestId
          )
        );
      } catch (error) {
        next(error);
      }
    }
  );

  return router;
}

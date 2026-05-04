import { Router } from "express";
import { toErrorResponse, toSuccessResponse } from "../../lib/errors.js";
import { authorizeRoles } from "../middleware/auth.js";
import { validateRequest } from "../middleware/validate.js";
import { validateDraftParams, validateProposalBody } from "../validators.js";

export function createDraftsRouter({ draftsService }) {
  const router = Router();

  router.get(
    "/draft/:suspicionId",
    authorizeRoles(["reviewer", "approver", "admin"]),
    validateRequest({ params: validateDraftParams }),
    async (req, res, next) => {
      try {
        const draft = await draftsService.getLatestDraftBySuspicionId(
          req.validated.params.suspicionId
        );

        if (!draft) {
          res.status(404).json(
            toErrorResponse({
              code: "DRAFT_NOT_FOUND",
              message: "Draft not found.",
              requestId: req.requestId,
            })
          );
          return;
        }

        res.json(toSuccessResponse(draft, req.requestId));
      } catch (error) {
        next(error);
      }
    }
  );

  router.post(
    "/save-draft",
    authorizeRoles(["approver", "admin"]),
    validateRequest({ body: validateProposalBody }),
    async (req, res, next) => {
      try {
        const result = await draftsService.saveDraft({
          ...req.validated.body,
          actor: req.actor,
          requestId: req.requestId,
        });

        res.json(
          toSuccessResponse(
            {
              savedAt: result.savedAt,
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

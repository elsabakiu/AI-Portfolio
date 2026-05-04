import { Router } from "express";
import multer from "multer";
import { toErrorResponse, toSuccessResponse } from "../../lib/errors.js";
import { authorizeRoles } from "../middleware/auth.js";
import { validateExtractInput, validateWorkflowRunParams } from "../validators.js";
import { validateRequest } from "../middleware/validate.js";

export function createExtractionRouter({ extractionService, config }) {
  const router = Router();
  const upload = multer({
    storage: multer.memoryStorage(),
    limits: {
      fileSize: config.uploadFileSizeLimitBytes,
    },
  });

  router.get(
    "/extractions/:runId",
    authorizeRoles(["reviewer", "approver", "admin"]),
    validateRequest({ params: validateWorkflowRunParams }),
    async (req, res, next) => {
      try {
        const workflowRun = await extractionService.getWorkflowRun(
          req.validated.params.runId
        );

        if (!workflowRun) {
          res.status(404).json(
            toErrorResponse({
              code: "WORKFLOW_RUN_NOT_FOUND",
              message: "Workflow run not found.",
              requestId: req.requestId,
            })
          );
          return;
        }

        res.json(toSuccessResponse(workflowRun, req.requestId));
      } catch (error) {
        next(error);
      }
    }
  );

  router.post("/extract", authorizeRoles(["reviewer", "approver", "admin"]), upload.single("audio_file"), async (req, res, next) => {
    try {
      const validated = validateExtractInput(req);
      const payload = await extractionService.runExtraction({
        suspicionId: validated.suspicionId,
        existingRecord: validated.existingRecord,
        file: req.file,
        requestId: req.requestId,
        actor: req.actor,
      });

      res.json(toSuccessResponse(payload, req.requestId));
    } catch (error) {
      next(error);
    }
  });

  return router;
}

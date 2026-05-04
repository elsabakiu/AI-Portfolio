export function validateRequest({ params, body }) {
  return (req, _res, next) => {
    try {
      req.validated = {
        params: params ? params(req.params) : req.params,
        body: body ? body(req.body) : req.body,
      };
      next();
    } catch (error) {
      next(error);
    }
  };
}

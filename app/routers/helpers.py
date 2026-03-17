from fastapi import Request
from fastapi.responses import RedirectResponse, Response


def htmx_redirect(request: Request, url: str) -> Response:
    """Return HX-Redirect for HTMX requests, RedirectResponse for normal requests."""
    if request.headers.get("HX-Request") == "true":
        response = Response(status_code=200)
        response.headers["HX-Redirect"] = url
        return response
    return RedirectResponse(url=url, status_code=303)

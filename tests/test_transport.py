"""Transport-related tests."""

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_server import QueryTokenProtectedASGIApp


class PlainTextASGIApp:
    """Minimal ASGI app for token wrapper testing."""

    async def __call__(self, scope, receive, send):
        response = PlainTextResponse("ok")
        await response(scope, receive, send)


def test_query_token_wrapper_allows_matching_token():
    """Query token auth should allow matching requests."""
    app = Starlette(
        routes=[Route("/mcp", endpoint=QueryTokenProtectedASGIApp(PlainTextASGIApp(), "secret"))]
    )

    with TestClient(app) as client:
        response = client.get("/mcp?token=secret")

    assert response.status_code == 200
    assert response.text == "ok"


def test_query_token_wrapper_rejects_missing_token():
    """Query token auth should reject requests without a token."""
    app = Starlette(
        routes=[Route("/mcp", endpoint=QueryTokenProtectedASGIApp(PlainTextASGIApp(), "secret"))]
    )

    with TestClient(app) as client:
        response = client.get("/mcp")

    assert response.status_code == 401
    assert response.text == "Unauthorized"


def test_query_token_wrapper_rejects_wrong_token():
    """Query token auth should reject requests with the wrong token."""
    app = Starlette(
        routes=[Route("/mcp", endpoint=QueryTokenProtectedASGIApp(PlainTextASGIApp(), "secret"))]
    )

    with TestClient(app) as client:
        response = client.get("/mcp?token=wrong")

    assert response.status_code == 401
    assert response.text == "Unauthorized"

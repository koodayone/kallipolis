import logging
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from students.api import router as students_router
from courses.api import router as courses_router
from occupations.api import router as occupations_router
from employers.api import router as employers_router
from partnerships.api import router as partnerships_router
from analytics.api import router as analytics_router
from ontology.schema import init_schema, close_driver
from ontology.timing import set_request_context
from contextlib import AsyncExitStack, asynccontextmanager
from mcp_server.server import mcp as mcp_server, build_oauth_mcp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The MCP server rides this app in-process. Build its Streamable-HTTP ASGI app
# and run its session manager inside the app lifespan — a mounted sub-app's
# lifespan is NOT started by Starlette, so we start it here, alongside the Neo4j
# schema init/teardown that previously lived in on_event handlers.
mcp_app = mcp_server.streamable_http_app()

# Optional OAuth-protected endpoint (this app is the resource server; WorkOS is
# the authorization server). Built only when MCP_OAUTH_* env is set, so nothing
# changes until we switch it on. Mounted at /mcp-oauth alongside the bearer-gated
# /mcp for the claude.ai handshake test; its host-root discovery doc (RFC 9728) is
# routed to the mounted location by Caddy.
_oauth_mcp = build_oauth_mcp()
oauth_app = _oauth_mcp.streamable_http_app() if _oauth_mcp else None


@asynccontextmanager
async def lifespan(app: "FastAPI"):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(mcp_server.session_manager.run())
        if _oauth_mcp is not None:
            await stack.enter_async_context(_oauth_mcp.session_manager.run())
        logger.info("Initializing Neo4j schema and seed data...")
        init_schema()
        # Warm the landscape index at startup so the first /partnerships/landscapes
        # request doesn't pay the ~2.3s cold build (live_catalog is lru-cached — this
        # just moves the one-time cost off the user's request onto boot). Neo4j is
        # already healthy (compose depends_on), so the graph read is valid here; a
        # failure is non-fatal — the lazy path rebuilds on first request.
        try:
            from partnerships.registry import live_catalog
            logger.info("Warmed landscape index: %d instances.", len(live_catalog()))
        except Exception as e:  # noqa: BLE001 — warm-up is best-effort, never blocks boot
            logger.warning("Landscape index warm-up skipped (%s); will build lazily.", e)
        logger.info("Startup complete.")
        try:
            yield
        finally:
            close_driver()


app = FastAPI(
    title="Kallipolis Atlas API",
    description="Institutional intelligence API for California Community College program coordinators",
    version="0.1.0",
    lifespan=lifespan,
)

cors_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3001").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def attribute_neo4j_queries(request: Request, call_next):
    # Tag every Neo4j query with its triggering route so the JSONL log
    # can be aggregated per-endpoint. The route template isn't resolved
    # at middleware entry (that happens during call_next), so we record
    # the raw path here and the aggregator normalizes UUIDs/numerics.
    set_request_context(f"{request.method} {request.url.path}")
    try:
        return await call_next(request)
    finally:
        set_request_context("")


app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(courses_router, prefix="/courses", tags=["Courses"])
app.include_router(occupations_router, prefix="/occupations", tags=["Occupations"])
app.include_router(employers_router, prefix="/employers", tags=["Employers"])
app.include_router(partnerships_router, prefix="/partnerships", tags=["Partnerships"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

# The MCP server (Streamable-HTTP), mounted in-process at /mcp. A bare mount (not
# include_router with a prefix=) is invisible to the vocabulary_alignment audit
# and needs no product doc — mcp_server is shared infrastructure, not an ontology unit.
app.mount("/mcp", mcp_app)
if oauth_app is not None:
    app.mount("/mcp-oauth", oauth_app)


@app.get("/health")
def health():
    return {"status": "ok"}

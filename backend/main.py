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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kallipolis Atlas API",
    description="Institutional intelligence API for California Community College program coordinators",
    version="0.1.0",
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


@app.on_event("startup")
async def startup():
    logger.info("Initializing Neo4j schema and seed data...")
    init_schema()
    logger.info("Startup complete.")


@app.on_event("shutdown")
async def shutdown():
    close_driver()


app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(courses_router, prefix="/courses", tags=["Courses"])
app.include_router(occupations_router, prefix="/occupations", tags=["Occupations"])
app.include_router(employers_router, prefix="/employers", tags=["Employers"])
app.include_router(partnerships_router, prefix="/partnerships", tags=["Partnerships"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])


@app.get("/health")
def health():
    return {"status": "ok"}

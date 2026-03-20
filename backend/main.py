import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.ontology import router as ontology_router
from api.workflows import router as workflows_router
from ontology.schema import init_schema, close_driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kallipolis Atlas API",
    description="Institutional intelligence API for California Community College program coordinators",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Initializing Neo4j schema and seed data...")
    init_schema()
    logger.info("Startup complete.")


@app.on_event("shutdown")
async def shutdown():
    close_driver()


app.include_router(ontology_router, prefix="/ontology", tags=["Ontology"])
app.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])


@app.get("/health")
def health():
    return {"status": "ok"}

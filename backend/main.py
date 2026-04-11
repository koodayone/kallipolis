import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from students.api import router as students_router
from courses.api import router as courses_router
from occupations.api import router as occupations_router
from employers.api import router as employers_router
from partnerships.api import router as partnerships_router
from strong_workforce.api import router as strong_workforce_router
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


app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(courses_router, prefix="/courses", tags=["Courses"])
app.include_router(occupations_router, prefix="/occupations", tags=["Occupations"])
app.include_router(employers_router, prefix="/employers", tags=["Employers"])
app.include_router(partnerships_router, prefix="/partnerships", tags=["Partnerships"])
app.include_router(strong_workforce_router, prefix="/strong-workforce", tags=["Strong Workforce"])


@app.get("/health")
def health():
    return {"status": "ok"}

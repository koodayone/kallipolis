# Kallipolis

Institutional intelligence platform for California Community College program coordinators.

## Repository Structure

```
kallipolis/
├── app/          # Landing page (Next.js, port 3000)
├── atlas/        # Atlas application (Next.js, port 3001)
├── backend/      # API server (FastAPI + Neo4j)
└── docker-compose.yml
```

## Setup

### 1. Environment Variables

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start Backend Services

Requires Docker and Docker Compose.

```bash
docker-compose up -d
```

This starts:
- **Neo4j** on `localhost:7474` (browser) and `localhost:7687` (bolt)
- **FastAPI backend** on `localhost:8000`

The backend automatically seeds the Neo4j database with Sierra Vista Community College data on first startup. Allow ~30 seconds for Neo4j to become healthy before the backend connects.

Verify the backend is running:

```bash
curl http://localhost:8000/ontology/institution
```

### 3. Start the Atlas Frontend

```bash
cd atlas
npm install
npm run dev
```

The Atlas runs at **http://localhost:3001**

## API Documentation

Interactive API docs: http://localhost:8000/docs

## Neo4j Browser

http://localhost:7474 — Username: `neo4j` / Password: `kallipolis_dev`

## Development (backend without Docker)

```bash
cd backend
pip install -r requirements.txt
# Ensure .env has NEO4J_URI pointing to your running Neo4j instance
uvicorn main:app --reload --port 8000
```

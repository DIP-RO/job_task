# Docker Deployment Guide
## Prerequisites
- Docker and Docker Compose installed on your machine
- OpenAI API key (required for draft generation)

## Quick Start
1. **Clone the repository**
```bash
git clone https://github.com/your-username/legal-ai-system.git
cd legal-ai-system
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
nano .env
```

3. **Start all services with Docker Compose**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Redis: localhost:6379

## Services Overview
When you run `docker-compose up`, it starts 3 containers:
1. **redis**: Redis cache for session and API request caching
2. **backend**: FastAPI backend server with all processing logic
3. **frontend**: Next.js frontend with single-page UI

## Persistent Storage
Docker volumes are created for:
- `redis_data`: Persists Redis cache data
- `backend/data/db`: SQLite database files
- `backend/uploads`: Uploaded user documents

## Stop the application
```bash
docker-compose down
```

## Stop and remove all volumes (reset database)
```bash
docker-compose down -v
```

## Troubleshooting
### Backend fails health check
Check logs:
```bash
docker-compose logs backend
```

### Frontend can't connect to backend
Verify the `NEXT_PUBLIC_API_URL` in `.env` is set correctly.

### OCR/Image processing fails
Ensure Tesseract is installed in the backend container (it's included in the Dockerfile).
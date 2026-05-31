# Testing Guide for RAG Video Comparator

## Setup

Make sure you have:
1. Python 3.11+
2. Node.js 18+
3. Docker (optional, for ChromaDB)
4. OpenAI API key in your environment variables or `.env` file

---

## 1. Running Unit Tests (Fast, No API Key Needed)

These tests use mocks and don't require external services.

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt pytest pytest-asyncio
pytest tests/unit -v
```

---

## 2. Running Integration Tests (Requires OpenAI API Key)

These tests interact with ChromaDB and OpenAI's API.

```bash
cd backend
source venv/bin/activate
pytest tests/integration -v
```

---

## 3. Running API Tests

```bash
cd backend
source venv/bin/activate
pytest tests/api -v
```

---

## 4. Running Frontend E2E Tests (Requires Both Servers Running)

First, start the backend and frontend:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
```

Then run Playwright tests:

```bash
cd frontend
npx playwright install --with-deps
npx playwright test
```

---

## 5. Running Load Tests with Locust

First, ensure the backend is running. Then:

```bash
cd backend/tests/load
pip install locust
locust -f locustfile.py
```

Then open your browser to http://localhost:8089.

Or use the pre-defined profiles:
```bash
# Smoke test (1 user, 1 min)
locust -f locustfile.py --config locust.conf --tags smoke

# Load test (50 users, 5 min)
locust -f locustfile.py --config locust.conf --tags load
```

---

## 6. Running the Cost & Quality Benchmark

```bash
cd backend
source venv/bin/activate
cd ..
python benchmark.py
```

---

## 7. GitHub Actions CI

The test workflow will automatically run on every push and pull request to `main`.

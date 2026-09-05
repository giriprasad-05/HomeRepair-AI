# HomeRepair AI

HomeRepair AI is an Agentic AI system designed to help users diagnose household appliance problems, inspect manuals and error codes, and coordinate repairs.

---

## Project Structure

```
HomeRepair-AI/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── styles/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database/
│   │   ├── agent/
│   │   ├── tools/
│   │   ├── memory/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── .env.example
│   └── requirements.txt
├── .env.example
├── .gitignore
├── PROJECT_RULES.md
└── README.md
```

---

## Tech Stack

- **Frontend**: React, Vite, JavaScript, Regular CSS (No Tailwind CSS)
- **Backend**: Python, FastAPI, Uvicorn
- **Database**: PostgreSQL, SQLAlchemy
- **Agent Framework**: LangGraph (to be added in future phases)

---

## Getting Started

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend health check endpoint:
- `GET http://localhost:8000/api/health`
- Interactive API Docs: `http://localhost:8000/docs`

Expected response:
```json
{
  "status": "healthy",
  "service": "HomeRepair AI"
}
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run frontend development server
npm run dev
```

Frontend will run at: `http://localhost:5173`

# HomeRepair AI

> An Agentic AI system for intelligent household appliance diagnosis and repair coordination.

## Overview

HomeRepair AI helps users register household appliances, report problems, and receive AI-powered diagnostics.

Unlike a normal chatbot, the system uses an Agentic AI workflow with:

- Persistent Memory
- Reasoning
- Tool Selection
- Decision Making
- Issue History

---

# Agentic AI Flow

```text
User Reports Issue
        ↓
Load Appliance Context
        ↓
Retrieve History & Memory
        ↓
Reasoning / Decision Making
        ↓
Select Required Tools
        ↓
Collect Evidence
        ↓
AI Diagnosis
        ↓
Store Diagnosis & Memory
        ↓
Reuse Knowledge for Future Issues
```

---

# Memory

HomeRepair AI uses PostgreSQL for persistent appliance-specific memory.

The system stores:

- Previous issues
- Previous diagnoses
- Repair history
- Repair outcomes
- Successful repairs
- Failed repairs
- Recurring problems

Before diagnosing a new issue, the agent retrieves relevant historical information.

If a similar issue occurs again, the agent can reuse previous knowledge instead of investigating everything from scratch.

---

# Reasoning

LangGraph manages the Agentic AI reasoning workflow.

The agent analyzes the current issue and selects an appropriate investigation path.

## Historical Match

A similar issue was previously resolved successfully.

The agent reuses relevant historical knowledge.

## Fresh Investigation

No useful similar issue exists.

The agent performs a new investigation.

## Reinvestigation

A previous repair failed or was partially resolved.

The agent uses previous information as evidence and investigates the issue again.

## Insufficient Data

There is not enough information for a reliable diagnosis.

The agent avoids generating unreliable information and requests additional details.

---

# Tools

The AI agent uses deterministic tools to collect factual information before generating a diagnosis.

### History Analysis Tool

Checks:

- Previous issues
- Previous diagnoses
- Similar incidents
- Recurring problems

### Repair Outcome Tool

Analyzes:

- Successful repairs
- Failed repairs
- Partially resolved repairs

### Warranty Tool

Checks appliance warranty information.

### Pattern Analysis Tool

Analyzes appliance and issue information to identify recurring patterns.

### Manual / Error Code Tool

Uses structured appliance and error-code information when relevant.

The agent conditionally selects tools based on the current issue instead of running every tool unnecessarily.

---

# Complete Agent Decision Flow

```text
Current Issue
      ↓
Load Appliance Context
      ↓
Check Issue History
      ↓
Retrieve Long-Term Memory
      ↓
Compare Previous Incidents
      ↓
Agent Reasoning
      │
      ├── Historical Match
      │       ↓
      │   Reuse Previous Knowledge
      │
      ├── Fresh Investigation
      │       ↓
      │   Select Diagnostic Tools
      │
      ├── Reinvestigation
      │       ↓
      │   Investigate Again
      │
      └── Insufficient Data
              ↓
       Request More Information
              ↓
        Generate AI Diagnosis
              ↓
        Store Diagnosis
              ↓
        Update Memory
```

---

# Features

- Appliance registration and management
- Issue tracking
- AI-powered diagnosis
- Persistent issue history
- Long-term appliance memory
- Historical diagnosis reuse
- Fresh investigation for new issues
- Reinvestigation for failed repairs
- Repair outcome tracking
- Warranty analysis
- Appliance status tracking

---

# Architecture

```text
React + Vite
      ↓
   FastAPI
      ↓
LangGraph Agent
      ├── History Retrieval
      ├── Memory Retrieval
      ├── Reasoning
      ├── Decision Making
      ├── Tool Selection
      └── Investigation
              ↓
       OpenRouter LLM
              ↓
         PostgreSQL
```

---

# Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| Agent Framework | LangGraph |
| AI Model Access | OpenRouter |
| ORM | SQLAlchemy |

---

# Project Structure

```text
HomeRepair-AI/
│
├── backend/
│   ├── app/
│   │   ├── agent/          # LangGraph agent workflow
│   │   ├── api/            # API routes
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Request/response schemas
│   │   ├── services/       # Business logic
│   │   ├── tools/          # Agent tools
│   │   └── main.py         # FastAPI application
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API communication
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── .env
├── .gitignore
└── README.md
```

---

# Requirements

Before running the project, install:

- Python 3.x
- Node.js and npm
- PostgreSQL
- OpenRouter API Key

---

# Configuration

## 1. Configure PostgreSQL

Install PostgreSQL and ensure the PostgreSQL server is running.

Create a database:

```sql
CREATE DATABASE homerepair;
```

You may use another database name, but make sure to use the same name in the `.env` configuration.

---

## 2. Configure `.env`

The project contains a `.env` file.

Open the `.env` file and configure:

- OpenRouter API Key
- OpenRouter AI Model
- PostgreSQL Username
- PostgreSQL Password
- PostgreSQL Database Name

Example:

```env
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=YOUR_MODEL_NAME

DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/homerepair
```

Replace:

```text
YOUR_OPENROUTER_API_KEY
YOUR_MODEL_NAME
USERNAME
PASSWORD
```

with your own credentials.

Example database configuration:

```env
DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/homerepair
```

The application uses the values configured in `.env`. No API key or database credentials are hardcoded in the source code.

---

# How to Run the Project

## 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd HomeRepair-AI
```

---

## 2. Configure PostgreSQL

Make sure PostgreSQL is installed and running.

Create the database:

```sql
CREATE DATABASE homerepair;
```

---

## 3. Configure `.env`

Open the existing `.env` file and add:

```env
OPENROUTER_API_KEY=YOUR_API_KEY
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=YOUR_MODEL_NAME

DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/homerepair
```

---

# Run Backend

Open a terminal in the project directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend:

```bash
python -m uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

---

# Run Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

Open the URL in your browser.

---

# Core Agentic AI Concept

```text
Memory
   +
Reasoning
   +
Tools
   ↓
Agent Decision
   ↓
AI Diagnosis
   ↓
Learning
```

HomeRepair AI does not simply generate an answer for every appliance problem.

The agent retrieves previous knowledge, reasons about the current situation, selects relevant tools, generates a diagnosis, and stores useful information for future issues.

---

**HomeRepair AI — Autonomous Appliance Repair Coordinator**

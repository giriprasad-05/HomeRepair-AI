# Project Rules & Guidelines: HomeRepair AI

## 1. Project Overview
HomeRepair AI is an Agentic AI system that assists users in diagnosing household appliance issues, interpreting symptom evidence and manuals, and coordinating repair services.

## 2. Core Architecture & Tech Stack
- **Frontend**:
  - React (JavaScript)
  - Vite
  - Vanilla / Regular CSS (Tailwind CSS is strictly forbidden)
  - Modular directory layout: `components/`, `pages/`, `services/`, `hooks/`, `styles/`, `utils/`
- **Backend**:
  - Python (FastAPI)
  - SQLAlchemy ORM & PostgreSQL
  - Modular package layout: `api/`, `models/`, `schemas/`, `services/`, `database/`, `agent/`, `tools/`, `memory/`
- **Agentic Engine**:
  - LangGraph (to be integrated incrementally in future phases)

## 3. Incremental Development Directives
- **Strict Scope Adherence**: Only build the exact functionality requested in each prompt.
- **No Premature Complexity**:
  - Do NOT implement authentication, database models, AI/LLM integration, or LangGraph graphs until explicitly tasked.
  - Do NOT introduce mockup business logic or unrequested frontend pages/charts.
  - Do NOT install heavy AI dependencies before their designated phase.
- **Code Standards**:
  - Write clean, maintainable, and well-typed/documented code.
  - Keep separation of concerns clean across frontend and backend services.
  - Ensure all health checks and existing endpoints remain unbroken as features evolve.

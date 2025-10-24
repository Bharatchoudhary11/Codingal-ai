# 🧠 Take-Home Assignment — AI Course Coach (Full‑Stack)

**Company:** Codingal  
**Role:** Frontend Engineering Intern (Full‑Stack variant)  
**Submission window:** 72 hours | **Estimated effort:** 6–10 hours

---

## 🎯 Objective
Build a student learning dashboard with an **AI Course Coach** that recommends the next activity and analyzes code attempts **without remote LLMs/APIs**. Two parts: **React** frontend + **Django REST** backend. Deterministic and explainable.

---

## 📦 Deliverables
- Monorepo with `/frontend` and `/backend`
- Root README with setup steps
- Tests (Vitest & pytest-django)
- Design notes for the recommender (features, scoring, confidence, limitations)

---

## 🔧 What to Build

### Frontend
- **Dashboard**: greeting, courses grid (name, progress, next up, last activity)
- **AI Course Coach panel**: next recommendation + why + confidence + 2 alternatives
- **Course Details**: lessons list; “Code Attempt Viewer” that runs AST-based checks (no LLM)

**AI client-side**
- Heuristic baseline using features like recency, progress gaps, tag gaps, hint rate
- Deterministic (seed any randomness)
- Static JS AST rules: at least 4 (unused var, off-by-one for loops, missing return, duplicate blocks)

**Data**
- Start with local JSON; switch to backend APIs once available

**Tests**
- ≥5 tests for recommender; ≥5 for code checks

### Backend (Django + DRF)
**Models**: Student, Course, Lesson, Attempt  
**Endpoints**:
- `GET /api/students/<id>/overview/`
- `GET /api/students/<id>/recommendation/`
- `POST /api/attempts/`
- `POST /api/analyze-code/` (Python AST analysis)

**Recommender**
- Implement deterministic scoring in `core/services/recommender.py` and return explanation + confidence

**Security/Perf**
- Serializer validation, throttling for writes, avoid N+1, indexes on frequent lookups

**Tests**
- Models, API, recommender determinism, code analysis

**Seed**
- `python manage.py seed_demo`

---

## ✅ Evaluation Rubric
AI design & rigor (25%), Explainability & UX (20%), Static analysis quality (20%), Backend craft (20%), Tests & docs (15%)

---

## 🧰 Starter Provided
Use/extend this starter; keep constraints intact.

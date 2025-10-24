# Codingal — AI Course Coach (Full‑Stack Starter)

Monorepo with a React frontend and Django backend for the take‑home assignment. See `ASSIGNMENT.md` for the brief.

## Quick start

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
# http://127.0.0.1:8000/api/
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

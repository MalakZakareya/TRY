# Agentic AI — Upload Starter

A clean starter project based on the same general FastAPI structure as the provided Agentic AI project.

## Current phase

- FastAPI application
- Black & white web interface
- File picker
- Drag & drop
- Basic `/api/v1/upload` endpoint
- Placeholder for the future Agentic AI / LangGraph workflow

The uploaded file is saved inside the local `uploads/` folder. No AI processing is connected yet.

## Run

```bash
python -m venv .venv
```

Activate the environment, then install:

```bash
pip install -e .
```

Run:

```bash
uvicorn main:app --reload --port 8001
```

Open:

`http://127.0.0.1:8001`

## Structure

```text
agentic_ai_upload_ui/
├── api/
│   └── v1/
│       └── upload.py
├── core/
│   └── config.py
├── core_agents/
│   └── graph.py
├── models/
│   └── uploaded_files.py
├── schemas/
│   └── upload.py
├── services/
│   └── file_service.py
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
├── uploads/
├── main.py
├── pyproject.toml
└── README.md
```

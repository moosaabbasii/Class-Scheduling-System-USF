# Bellini Scheduling Backend

FastAPI backend for the scheduling schema defined in `database.sql`, using the existing `database.sqlite` file directly through an object-oriented repository and service architecture.

## Stack

- Python
- FastAPI
- SQLite
- Pydantic

## Project structure

```text
app/
  api/           FastAPI routers and dependencies
  core/          settings and custom exceptions
  db/            SQLite connection/session wrapper
  models/        domain entities as dataclasses
  repositories/  data access layer
  schemas/       request/response models
  services/      business logic layer
main.py          ASGI entrypoint
```

## Install

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

or in Powershell 

```shell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If your default `python` command points to the Microsoft Store shim, use a real interpreter path instead.

## Run

```bash
uvicorn main:app --reload --port 8080
```

The API will be available at:

- `http://127.0.0.1:8080/api/v1/health`
- `http://127.0.0.1:8080/docs`

For frontend development, CORS origins can be configured via `CORS_ORIGINS` (comma-separated).
Default includes common Vite dev origins on `localhost`/`127.0.0.1` ports `5173` and `4173`.

## Import semester data from XLSX

Use the built-in importer (no extra Excel package needed):

```bash
python scripts/import_schedule_xlsx.py --db database.sqlite --xlsx "app/data/Bellini Classes F25.xlsx" --schedule-name F25
```

For other files, change `--xlsx` and `--schedule-name` (for example `S25`, `S26`).

## Implemented API areas

- `users`
- `catalog-courses`
- `rooms`
- `instructors`
- `tas`
- `schedules`
- `sections`
- `audits`
- `analytics`
- `exports`

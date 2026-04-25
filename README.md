# MOPS — Class Scheduling System

> A full-stack web application for managing class schedules at Bellini College.  
> Built for CEN4020 Software Engineering, Spring 2026.

**Team 12:** Anne Utegen · Jose Nieves · Moosa Abbasi · Jake Cook

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?style=flat-square&logo=react)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Roles & Permissions](#roles--permissions)
- [API Reference](#api-reference)
- [Dataset](#dataset)

---

## Overview

MOPS is a scheduling management tool built for the Bellini College scheduling committee. It allows committee members to create and manage class sections, detect scheduling conflicts, compare enrollment trends across semesters, and lock finalized schedules for approval.

---

## Features

| Feature | Description |
|---------|-------------|
| 📋 Section Management | Create, edit, and delete class sections with CRN, room, instructor, TA, and meeting time |
| 🔍 Audit Reports | Detect duplicate CRNs, time conflicts, and missing required fields |
| 🗺️ Room Utilization | Heat map visualization of room usage by day and time |
| 📊 Enrollment Comparison | Compare enrollment across semesters with near-capacity (🔴) and growth (📈) indicators |
| 🔒 Schedule Lock | Lock/unlock finalized schedules (Chair only) to prevent accidental edits |
| 📜 Modification History | Track schedule changes and draft notification emails |
| 📄 PDF Export | Export schedules, audit reports, and enrollment comparisons as PDFs |
| 👥 Role-Based Access | Separate permissions for Committee Members and Committee Chairs |

---

## Tech Stack

**Backend**
- Python 3.x
- FastAPI
- SQLAlchemy (ORM)
- Pydantic (schema validation)
- SQLite

**Frontend**
- React + TypeScript
- Vite
- Tailwind CSS

---

## Project Structure

```
project2/
├── backend/
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Config & exceptions
│   │   ├── db/               # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   ├── scripts/              # Data import scripts
│   ├── database.sqlite       # SQLite database file
│   ├── database.sql          # Schema definition
│   ├── main.py               # App entry point
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/       # Reusable UI components
        ├── pages/            # Page-level components
        ├── services/         # API client & auth context
        └── types/            # TypeScript type definitions
    ├── index.html
    └── package.json
```

---

## Getting Started

### Prerequisites

- Python 3.x
- Node.js (v18+)

### Backend

```bash
cd backend
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload --port 8080
```

- API base: `http://127.0.0.1:8080`
- Swagger docs: `http://127.0.0.1:8080/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173`

---

## Roles & Permissions

Role selection happens on the home page — no authentication required in the current version.

| Role | Permissions |
|------|-------------|
| **Committee Member** | View, create, edit, and delete sections; view enrollment comparison |
| **Committee Chair** | All member permissions + run audits, lock/unlock schedules, finalize schedule |

---

## API Reference

Base URL: `/api/v1`

| Resource | Method | Endpoint |
|----------|--------|----------|
| Users | `GET` `POST` | `/users` |
| Schedules | `GET` `POST` `PATCH` `DELETE` | `/schedules` |
| Lock Schedule | `POST` | `/schedules/{id}/lock` |
| Unlock Schedule | `POST` | `/schedules/{id}/unlock` |
| Sections | `GET` `POST` `PATCH` `DELETE` | `/sections` |
| Audits | `GET` `POST` | `/audits` |
| Enrollment Analytics | `GET` | `/analytics/enrollment-comparison` |
| Export Schedule PDF | `GET` | `/exports/schedules/pdf` |
| Export Audit PDF | `GET` | `/exports/audits/{id}/pdf` |
| Export Enrollment PDF | `GET` | `/exports/analytics/enrollment-comparison/pdf` |

Full API documentation: [`backend/API.md`](backend/API.md)

---

## Dataset

The system is pre-loaded with Bellini College class data across three semesters:

| Schedule ID | Semester |
|-------------|----------|
| 1 | Fall 2025 |
| 2 | Spring 2025 |
| 3 | Spring 2026 |

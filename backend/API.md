# Bellini Scheduling API

## Overview

- App name: `Bellini Scheduling API`
- API prefix: `/api/v1`
- OpenAPI JSON: `/openapi.json`
- Swagger UI: `/docs`

Example base URL:

```text
http://127.0.0.1:8000
```

All JSON endpoints use `application/json`.

## Authorization Model

This project currently uses a simple actor model via query parameter, not JWT/session auth.

- `actor_user_id` is required on protected endpoints.
- Role rules: `member` or `chair` can mutate schedules/sections and use analytics/exports.
- Role rules: `chair` only can lock/unlock schedules and run finalize/audit actions.

## Error Response Format

Application errors are returned as:

```json
{
  "detail": "Human-readable message"
}
```

Common status codes:

- `200` OK
- `201` Created
- `204` No Content
- `403` Forbidden
- `404` Not Found
- `409` Conflict
- `422` Validation Error

## Core Schemas

### User

```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "role": "member"
}
```

### Schedule

```json
{
  "id": 1,
  "name": "F25",
  "locked": false,
  "status": "draft",
  "created_by": 1,
  "approved_by": null,
  "created_at": "2026-04-15T00:00:00",
  "approved_at": null
}
```

### Course Section

```json
{
  "id": 1,
  "schedule_id": 1,
  "catalog_course_id": 1,
  "crn": 91940,
  "level": "UG",
  "enrollment": 99,
  "start_date": "2025-08-25",
  "end_date": "2025-12-11",
  "room_id": 1,
  "instructor_id": 1,
  "meetings": [
    {
      "id": 1,
      "section_id": 1,
      "days": "TR",
      "start_time": "11:00",
      "end_time": "12:15"
    }
  ],
  "ta_assignments": [
    {
      "ta_id": 1,
      "assigned_hours": 2.5,
      "ta_name": "Some TA",
      "ta_email": "ta@example.com",
      "max_hours": 20
    }
  ]
}
```

## Endpoints

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check. Returns `{"status":"ok"}`. |

## Users

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/users` | List users. |
| POST | `/api/v1/users` | Create user. |
| GET | `/api/v1/users/{user_id}` | Get user by ID. |
| PATCH | `/api/v1/users/{user_id}` | Update user. |
| DELETE | `/api/v1/users/{user_id}` | Delete user. |

`POST /api/v1/users` body:

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "secret",
  "role": "member"
}
```

## Lookups

### Catalog Courses

| Method | Path |
|---|---|
| GET | `/api/v1/catalog-courses` |
| POST | `/api/v1/catalog-courses` |
| GET | `/api/v1/catalog-courses/{item_id}` |
| PATCH | `/api/v1/catalog-courses/{item_id}` |
| DELETE | `/api/v1/catalog-courses/{item_id}` |

Create body:

```json
{
  "course_number": "COP 4703",
  "title": "Advanced Database Systems"
}
```

### Rooms

| Method | Path |
|---|---|
| GET | `/api/v1/rooms` |
| POST | `/api/v1/rooms` |
| GET | `/api/v1/rooms/{item_id}` |
| PATCH | `/api/v1/rooms/{item_id}` |
| DELETE | `/api/v1/rooms/{item_id}` |

Create body:

```json
{
  "room_number": "ENB 118",
  "capacity": 60
}
```

### Instructors

| Method | Path |
|---|---|
| GET | `/api/v1/instructors` |
| POST | `/api/v1/instructors` |
| GET | `/api/v1/instructors/{item_id}` |
| PATCH | `/api/v1/instructors/{item_id}` |
| DELETE | `/api/v1/instructors/{item_id}` |

Create body:

```json
{
  "name": "Jane Doe",
  "email": "jane@usf.edu"
}
```

### TAs

| Method | Path |
|---|---|
| GET | `/api/v1/tas` |
| POST | `/api/v1/tas` |
| GET | `/api/v1/tas/{item_id}` |
| PATCH | `/api/v1/tas/{item_id}` |
| DELETE | `/api/v1/tas/{item_id}` |

Notes:

- `max_hours` is stored on the TA record.
- `hours` is derived weekly from the classes the TA is assigned to.
- Derived `hours` are schedule-specific. Use `schedule_id` on `GET /api/v1/tas` or `GET /api/v1/tas/{item_id}` to calculate them for one schedule only.
- If `schedule_id` is omitted, `hours` returns `0`.

Create body:

```json
{
  "name": "TA Name",
  "email": "ta@usf.edu",
  "max_hours": 20
}
```

TA response example:

```json
{
  "id": 1,
  "name": "TA Name",
  "email": "ta@usf.edu",
  "max_hours": 20,
  "hours": 7.5
}
```

## Schedules

Protected endpoints in this group require `actor_user_id`.

| Method | Path | Role |
|---|---|---|
| GET | `/api/v1/schedules` | Public |
| POST | `/api/v1/schedules?actor_user_id={id}` | member/chair |
| GET | `/api/v1/schedules/{schedule_id}` | Public |
| PATCH | `/api/v1/schedules/{schedule_id}?actor_user_id={id}` | member/chair |
| DELETE | `/api/v1/schedules/{schedule_id}?actor_user_id={id}` | member/chair |
| POST | `/api/v1/schedules/{schedule_id}/lock?actor_user_id={id}` | chair |
| POST | `/api/v1/schedules/{schedule_id}/unlock?actor_user_id={id}` | chair |
| POST | `/api/v1/schedules/{schedule_id}/finalize?actor_user_id={id}` | chair |
| GET | `/api/v1/schedules/{schedule_id}/sections` | Public |
| POST | `/api/v1/schedules/{schedule_id}/sections?actor_user_id={id}` | member/chair |

Create schedule body:

```json
{
  "name": "F25",
  "status": "draft",
  "created_by": 1
}
```

Create schedule section body:

```json
{
  "catalog_course_id": 1,
  "crn": 91940,
  "level": "UG",
  "enrollment": 99,
  "start_date": "2025-08-25",
  "end_date": "2025-12-11",
  "room_id": 1,
  "instructor_id": 1,
  "meetings": [
    { "days": "TR", "start_time": "11:00", "end_time": "12:15" }
  ],
  "ta_assignments": [
    { "ta_id": 1 }
  ]
}
```

Validation notes on section create/update:

- Required for save: CRN, room assignment, instructor assignment, at least one meeting.
- Detects duplicate CRN in the same schedule.
- Detects room time conflicts and instructor time conflicts.

## Sections

Protected write endpoints require `actor_user_id`.

| Method | Path | Role |
|---|---|---|
| GET | `/api/v1/sections/{section_id}` | Public |
| PATCH | `/api/v1/sections/{section_id}?actor_user_id={id}` | member/chair |
| DELETE | `/api/v1/sections/{section_id}?actor_user_id={id}` | member/chair |

Update body uses partial fields from section create model.

## Audits

`POST /api/v1/audits/schedules/{schedule_id}` is chair-only and expects actor validation.

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/audits` | Optional query: `schedule_id` |
| GET | `/api/v1/audits/{report_id}` | Get audit report with issues |
| POST | `/api/v1/audits/schedules/{schedule_id}?actor_user_id={id}` | Run audit (chair) |
| PATCH | `/api/v1/audits/{report_id}` | Update report status/passed |
| PATCH | `/api/v1/audits/issues/{issue_id}` | Update issue status |

Run-audit body:

```json
{
  "generated_by": 2
}
```

Constraint: if `generated_by` is provided, it must match `actor_user_id`.

## Analytics

| Method | Path | Role |
|---|---|---|
| GET | `/api/v1/analytics/enrollment-comparison?schedule_ids=1&schedule_ids=2&actor_user_id={id}` | member/chair |

Optional filters:

- `subject`
- `course_number`

Returns per-course, per-semester comparison with:

- `total_enrollment`
- `section_count`
- `near_capacity`
- `offered`
- `instructors`
- `tas`
- `significant_growth`

## Exports

All export endpoints require `actor_user_id` with member/chair role.

| Method | Path | Response |
|---|---|---|
| GET | `/api/v1/exports/schedules/preview` | JSON preview (`ScheduleExportPreviewResponse`) |
| GET | `/api/v1/exports/schedules/pdf` | `application/pdf` |
| GET | `/api/v1/exports/audits/{report_id}/pdf` | `application/pdf` |
| GET | `/api/v1/exports/analytics/enrollment-comparison/pdf` | `application/pdf` |

`/exports/schedules/preview` and `/exports/schedules/pdf` query params:

- `schedule_id` (required)
- `actor_user_id` (required)
- `day` (optional)
- `room_id` (optional)
- `instructor_id` (optional)

`/exports/analytics/enrollment-comparison/pdf` query params:

- `schedule_ids` (required, repeat query key)
- `actor_user_id` (required)
- `subject` (optional)
- `course_number` (optional)

## Quick cURL Examples

Create a member user:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Alice\",\"email\":\"alice@example.com\",\"password\":\"secret\",\"role\":\"member\"}"
```

List schedules:

```bash
curl "http://127.0.0.1:8000/api/v1/schedules"
```

Run finalize (chair):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/schedules/1/finalize?actor_user_id=2"
```

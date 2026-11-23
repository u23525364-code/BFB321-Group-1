# HPC Takt Dashboard: JSON API

All endpoints live in `api.py` (Flask Blueprint, prefix `/api`) and return JSON.
They call the same functions in `services.py` as the web pages, so the data is identical.
The API does not need a login, so readers, scripts and testers can call it directly.

Base URL when running locally: `http://127.0.0.1:5000`

## Endpoints

| Method | Path | Purpose | Success | Errors |
|---|---|---|---|---|
| GET | `/api/kpis` | Takt KPIs (deliveries, average turnaround, compliance %, breached, at risk, on site) | 200 | — |
| GET | `/api/deliveries` | List deliveries with pagination and filters | 200 | 400 |
| GET | `/api/deliveries/<id>` | One delivery | 200 | 404 |
| PATCH | `/api/deliveries/<id>` | Log an exception note (reason for a breach) | 200 | 400, 404 |
| POST | `/api/scan-events` | Record an RFID scan (opens, updates or closes a delivery) | 201 | 400 |
| GET | `/api/trucks` | Trucks with their carrier names | 200 | — |

Status codes: **200** OK · **201** Created (new record) · **400** Bad Request (invalid input, with an `error` message) · **404** Not Found · **500** server error (details only in `logs/app.log`).

All errors have the same shape:
```json
{"error": "'size' must be between 1 and 100."}
```

## Query parameters for `GET /api/deliveries`

| Parameter | Type | Default | Rule | Example |
|---|---|---|---|---|
| `page` | whole number | 1 | 1 to 10000 | `?page=2` |
| `size` | whole number | 20 | 1 to 100 | `?size=50` |
| `q` | text | — | part of a truck code | `?q=TRK-02` |
| `carrier` | whole number | — | carrier id | `?carrier=2` |
| `status` | text | — | `On track`, `At risk`, `Breached` or `On site` | `?status=Breached` |

Results are sorted newest first (by gate-in time).

## Examples

**List, filtered and paged:** `GET /api/deliveries?status=Breached&size=1`
```json
{
  "page": 1,
  "size": 1,
  "total": 30,
  "items": [
    {
      "id": 111,
      "delivery_code": "DEL-0111",
      "truck_code": "TRK-06",
      "carrier": "Unitrans",
      "dock": "DOCK-B",
      "gate_in_at": "2026-10-03T12:06:00",
      "gate_out_at": "2026-10-03T13:51:00",
      "turnaround_min": 105,
      "status": "Breached",
      "exception_note": null
    }
  ]
}
```

**One delivery:** `GET /api/deliveries/2` returns one delivery object in the same shape (DEL-0002, TRK-09, 103 min, Breached).
`GET /api/deliveries/9999` returns 404 with `{"error": "Delivery not found."}`.

**Log a reason for a breach:** `PATCH /api/deliveries/2`
Request body:
```json
{"exception_note": "Dock not ready"}
```
Response (200):
```json
{"message": "Exception logged for DEL-0002.", "delivery": {"id": 2, "exception_note": "Dock not ready"}}
```
(The `delivery` object contains all the fields shown above; it is shortened here.)
An empty note, or one over 255 characters, returns 400.

**Record an RFID scan:** `POST /api/scan-events`
Request body:
```json
{"truck_code": "TRK-02", "location": "GATE-IN", "reader_id": "hpc-reader-01"}
```
Response (201):
```json
{"message": "TRK-02 gated in. DEL-0119 opened.", "delivery": {"id": 119, "status": "On site"}}
```
Rules: `GATE-IN` opens a delivery; `DOCK-A` / `DOCK-B` record the dock; `GATE-OUT` closes it.
A second `GATE-IN` while the truck is on site, or a scan for an unknown truck, returns 400.
Every scan received is written to `logs/app.log`.

## Trying it

In a browser (GET only): open `http://127.0.0.1:5000/api/kpis`

From Windows PowerShell:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/scan-events -ContentType "application/json" -Body '{"truck_code": "TRK-02", "location": "GATE-IN", "reader_id": "hpc-reader-01"}'
```

From macOS / Linux:
```bash
curl -X POST http://127.0.0.1:5000/api/scan-events -H "Content-Type: application/json" -d '{"truck_code": "TRK-02", "location": "GATE-IN", "reader_id": "hpc-reader-01"}'
```

Automated tests: `tests/test_api.py` (run `python init_db.py --reset`, then `pytest -v`).

## Connecting the RFID gateway

HPC's gateway (`hpc-rfid-gateway`, Node.js) can POST each scan to a webhook URL.
Pointing it at `POST /api/scan-events` lets live reader data flow straight into this app.
The gateway's payload uses `location` and `truck_id`, so a small mapping step is needed;
the gateway also sends no API key, so this endpoint should be protected before going live.
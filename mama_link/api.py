"""Loopback-only synthetic demo API; not an authenticated production service."""
import os
import secrets
import time
import json
import sqlite3
from uuid import uuid4
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .core import DATA, ROOT, assess_case, get_case, load_cases, read_json, screen
from .schemas import AssessmentInput, ConsentInput, SYMPTOMS
from .storage import Store
from .education import ARTICLES
from .__main__ import evaluate
from . import telemetry
from . import accounts, chat
from .registry import search as search_registry
from .schemas import (Registration, Credentials, Profile, DeviceConsent, DeviceImport, ChatInput,
                      AppointmentInput, AppointmentStatusInput, FollowUpInput, FollowUpStatusInput)


def create_app(db_path=None):
    telemetry_enabled = telemetry.configure()
    app = FastAPI(title="MAMA-Link synthetic demo", version="0.3.0")
    store = Store(db_path or os.getenv("MAMA_LINK_DB", str(ROOT / ".local/mama-link.sqlite3")))
    accounts.initialize(store)
    attempts = {}

    def user(request, admin=False):
        identity = request.state.identity
        if not identity:
            raise HTTPException(401, 'Please sign in first')
        if admin and identity['role'] != 'admin':
            raise HTTPException(403, 'Administrator access required')
        return identity

    def limit(request, operation, count=20):
        key = (request.client.host if request.client else 'local', operation)
        now = time.monotonic()
        recent = [t for t in attempts.get(key, []) if now - t < 60]
        if len(recent) >= count:
            raise HTTPException(429, 'Please wait a minute before trying again')
        attempts[key] = recent + [now]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def local_session(request: Request, call_next):
        started = time.perf_counter()
        if request.method in {"POST", "DELETE", "PUT", "PATCH"}:
            origin = request.headers.get("origin")
            if origin and urlsplit(origin).netloc != request.headers.get("host"):
                telemetry.record("http_request", "rejected", started)
                return JSONResponse({"detail": "Cross-origin writes are not allowed"}, status_code=403)
            if request.headers.get("x-mama-link") != "local-demo":
                telemetry.record("http_request", "rejected", started)
                return JSONResponse({"detail": "Missing local demo request header"}, status_code=403)
        owner = request.cookies.get("mama_session", "")
        fresh = len(owner) != 64 or any(c not in "0123456789abcdef" for c in owner)
        request.state.owner = secrets.token_hex(32) if fresh else owner
        request.state.identity = accounts.identity(store, request.cookies.get('mama_auth', ''))
        expected_account = request.headers.get('x-mama-account')
        if expected_account and (not request.state.identity or request.state.identity['id'] != expected_account):
            return JSONResponse({'detail': 'The signed-in account changed. Reloading your private space.'}, status_code=401)
        if request.state.identity:
            request.state.owner = request.state.identity['id']
        response = await call_next(request)
        if fresh:
            response.set_cookie("mama_session", request.state.owner, httponly=True, samesite="strict")
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        telemetry.record("http_request", "ok" if response.status_code < 400 else "error", started)
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "synthetic_local_simulation", "foundry_connected": False,
                "telemetry_enabled": telemetry_enabled}

    @app.get('/api/me')
    def me(request: Request):
        return {'user': request.state.identity, 'chat': chat.configuration()}

    def signed_in(uid, request):
        accounts.revoke(store, request.cookies.get('mama_auth', ''))
        token = accounts.session(store, uid)
        response = JSONResponse({'user': accounts.identity(store, token)})
        response.set_cookie('mama_auth', token, httponly=True, samesite='strict', max_age=43200)
        return response

    @app.post('/api/register')
    def register(body: Registration, request: Request):
        limit(request, 'auth')
        try:
            uid = accounts.register(store, body.username, body.password, body.profile.model_dump())
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'Choose another username')
        return signed_in(uid, request)

    @app.post('/api/login')
    def login(body: Credentials, request: Request):
        limit(request, 'auth')
        uid = accounts.login(store, body.username, body.password)
        if not uid:
            raise HTTPException(401, 'Username or password was not recognized')
        return signed_in(uid, request)

    @app.post('/api/logout')
    def logout(request: Request):
        accounts.revoke(store, request.cookies.get('mama_auth', ''))
        response = JSONResponse({'signed_out': True})
        response.delete_cookie('mama_auth')
        return response

    @app.put('/api/profile')
    def profile(body: Profile, request: Request):
        identity = user(request)
        with store.connect() as db:
            db.execute('UPDATE users SET profile=? WHERE id=?', (body.model_dump_json(), identity['id']))
        return {'profile': body.model_dump()}

    @app.get('/api/device')
    def device(request: Request):
        identity = user(request)
        with store.connect() as db:
            enabled = db.execute('SELECT enabled FROM connections WHERE owner=?', (identity['id'],)).fetchone()
            rows = db.execute('SELECT id, payload FROM imports WHERE owner=? ORDER BY rowid DESC LIMIT 20', (identity['id'],)).fetchall()
        return {'enabled': bool(enabled and enabled[0]), 'imports': [{'id': r[0], **json.loads(r[1])} for r in rows], 'live_connection': False}

    @app.put('/api/device')
    def device_consent(body: DeviceConsent, request: Request):
        identity = user(request)
        with store.connect() as db:
            db.execute('INSERT OR REPLACE INTO connections VALUES (?, ?)', (identity['id'], int(body.enabled)))
            if not body.enabled:
                db.execute('DELETE FROM imports WHERE owner=?', (identity['id'],))
        return {'enabled': body.enabled}

    @app.post('/api/device/import', status_code=201)
    def device_import(body: DeviceImport, request: Request):
        identity = user(request)
        if not device(request)['enabled']:
            raise HTTPException(403, 'Enable optional imports before adding readings')
        identifier = str(uuid4())
        with store.connect() as db:
            db.execute('INSERT INTO imports VALUES (?, ?, ?)', (identifier, identity['id'], body.model_dump_json()))
        return {'id': identifier, **body.model_dump()}

    @app.post('/api/chat')
    def chat_message(body: ChatInput, request: Request):
        identity = user(request)
        limit(request, 'chat', 10)
        return chat.answer(body.message, identity['profile'], store.history(identity['id']), body.share_context,
                           [turn.model_dump() for turn in body.conversation])

    @app.get("/api/cases")
    def cases(request: Request):
        user(request, admin=True)
        return load_cases()

    @app.get("/api/options")
    def options():
        locations = read_json(DATA / "data/nigeria_locations.json")["states"]
        curated = read_json(DATA / "data/facilities.json")["facilities"]
        directory = curated[:]
        known_places = {(f["state"], f["lga"]) for f in curated}
        for location in locations:
            for place in location["places"]:
                if (location["name"], place) in known_places:
                    continue
                directory.append({
                    "facility_id": f"DIR-{location['name'].replace(' ', '-').upper()}-{place.replace(' ', '-').upper()}",
                    "name": f"{place} health facility directory entry",
                    "facility_type": "health_facility_directory",
                    "state": location["name"], "lga": place,
                    "community": "Not supplied", "capabilities": [],
                    "status": "verify_with_registry", "directory_entry": True
                })
        return {"symptoms": SYMPTOMS,
                "facilities": directory,
                "locations": locations,
                "national_services": read_json(DATA / "data/national_services.json")}

    @app.get("/api/facilities")
    def facilities(state: str = Query(default="", max_length=80),
                   lga: str = Query(default="", max_length=80),
                   limit: int = Query(default=100, ge=1, le=250),
                   verified_only: bool = True):
        return search_registry(state, lga, limit, verified_only)

    @app.get("/api/hotspots")
    def hotspots(request: Request):
        user(request, admin=True)
        rows = {}
        for case in load_cases():
            # Benchmark fixtures retain their clinical workflow location while
            # hotspot_location supplies the evidence-informed synthetic map sample.
            map_location = case.get("hotspot_location", case.get("location", {}))
            state = map_location.get("state", "Unknown")
            lga = map_location.get("lga", "Unknown")
            risk = screen(case)["classification"]
            state_row = rows.setdefault(state, {"state": state, "total": 0, "critical": 0,
                                                "warning": 0, "unassessed": 0, "places": {}})
            state_row["total"] += 1
            state_row[risk] += 1
            place = state_row["places"].setdefault(lga, {"place": lga, "total": 0, "critical": 0, "warning": 0})
            place["total"] += 1
            if risk in {"critical", "warning"}:
                place[risk] += 1
        result = []
        for row in rows.values():
            row["places"] = sorted(row["places"].values(), key=lambda item: (-item["critical"], -item["warning"], item["place"]))
            result.append(row)
        return {"scope": "100 evidence-informed synthetic scenario cases; not observed counts or prevalence evidence",
                "states": sorted(result, key=lambda item: (-item["critical"], -item["warning"], item["state"]))}

    @app.post("/api/assessments", status_code=201)
    def assessment(body: AssessmentInput, request: Request):
        identity = user(request, admin=bool(body.case_id))
        try:
            case = get_case(body.case_id) if body.case_id else body.case.to_case()
        except ValueError:
            raise HTTPException(404, "Demo case not found")
        provenance = {k: {'source': 'manual_entry', 'reviewed': True} for k in case.get('readings', {})}
        if body.case_id:
            provenance = {k: {'source': 'admin_fixture', 'reviewed': True} for k in case.get('readings', {})}
        if body.import_id:
            if body.case_id:
                raise HTTPException(422, 'Imports cannot be mixed with demo fixtures')
            if not device(request)['enabled']:
                raise HTTPException(403, 'Device import consent was withdrawn')
            with store.connect() as db:
                row = db.execute('SELECT payload FROM imports WHERE id=? AND owner=?', (body.import_id, identity['id'])).fetchone()
            if not row:
                raise HTTPException(404, 'Import not found')
            try:
                imported = DeviceImport.model_validate_json(row[0])
            except ValueError:
                raise HTTPException(422, 'Imported readings are now too old; import recent readings')
            for reading in imported.measurements:
                if reading.metric not in case['readings']:
                    case['readings'][reading.metric] = {'value': reading.value}
                    provenance[reading.metric] = {'source': imported.source, 'provider': imported.provider, 'device': imported.device_name, 'unit': reading.unit, 'measured_at': reading.measured_at, 'reviewed': True, 'import_id': body.import_id}
        case['provenance'] = provenance
        prior = store.history(request.state.owner)
        return store.create(request.state.owner, case, assess_case(case, prior_records=prior))

    @app.get("/api/history")
    def history(request: Request):
        user(request)
        return store.history(request.state.owner)

    @app.delete("/api/history")
    def clear(request: Request):
        user(request)
        store.clear(request.state.owner)
        return {"cleared": True}

    @app.post("/api/assessments/{identifier}/consent")
    def consent(identifier: str, body: ConsentInput, request: Request):
        user(request)
        try:
            return store.consent(request.state.owner, identifier, body.facility_id)
        except LookupError:
            raise HTTPException(404, "Assessment not found")
        except ValueError as error:
            raise HTTPException(409, str(error))

    @app.post("/api/appointments", status_code=201)
    def create_appointment(body: AppointmentInput, request: Request):
        identity = user(request)
        if body.assessment_id and not store.get(identity["id"], body.assessment_id):
            raise HTTPException(404, "Assessment not found")
        return store.create_appointment(identity["id"], body.model_dump())

    @app.get("/api/appointments")
    def appointments(request: Request):
        identity = user(request)
        return store.list_coordination("appointments", identity["id"])

    @app.patch("/api/appointments/{identifier}")
    def update_appointment(identifier: str, body: AppointmentStatusInput, request: Request):
        identity = user(request)
        if not store.get_coordination("appointments", identity["id"], identifier):
            raise HTTPException(404, "Appointment not found")
        return store.update_coordination("appointments", identity["id"], identifier, body.status)

    @app.post("/api/appointments/{identifier}/acknowledge")
    def acknowledge_appointment(identifier: str, request: Request):
        identity = user(request)
        if not store.get_coordination("appointments", identity["id"], identifier):
            raise HTTPException(404, "Appointment not found")
        return store.update_coordination("appointments", identity["id"], identifier, "confirmed", acknowledged=True)

    @app.post("/api/follow-ups", status_code=201)
    def create_follow_up(body: FollowUpInput, request: Request):
        identity = user(request)
        if body.assessment_id and not store.get(identity["id"], body.assessment_id):
            raise HTTPException(404, "Assessment not found")
        return store.create_followup(identity["id"], body.model_dump())

    @app.get("/api/follow-ups")
    def follow_ups(request: Request):
        identity = user(request)
        return store.list_coordination("followups", identity["id"])

    @app.patch("/api/follow-ups/{identifier}")
    def update_follow_up(identifier: str, body: FollowUpStatusInput, request: Request):
        identity = user(request)
        if not store.get_coordination("followups", identity["id"], identifier):
            raise HTTPException(404, "Follow-up task not found")
        return store.update_coordination("followups", identity["id"], identifier, body.status)

    @app.post("/api/follow-ups/{identifier}/acknowledge")
    def acknowledge_follow_up(identifier: str, request: Request):
        identity = user(request)
        if not store.get_coordination("followups", identity["id"], identifier):
            raise HTTPException(404, "Follow-up task not found")
        return store.update_coordination("followups", identity["id"], identifier, "acknowledged", acknowledged=True)

    @app.get("/api/coordination/reminders")
    def reminders(request: Request):
        identity = user(request)
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        appointments = [item for item in store.list_coordination("appointments", identity["id"])
                        if item["status"] in {"requested", "confirmed"} and item["requested_for"] <= now]
        followups = [item for item in store.list_coordination("followups", identity["id"])
                     if item["status"] == "open" and item["due_at"] <= now]
        return {"appointments_due": appointments, "follow_ups_due": followups,
                "notification_sent": False}

    @app.get("/api/dashboard/coordination")
    def coordination_dashboard(request: Request):
        user(request, admin=True)
        appointments = store.list_coordination("appointments")
        followups = store.list_coordination("followups")
        return {"appointments": appointments, "follow_ups": followups,
                "outstanding_appointments": [x for x in appointments if x["status"] in {"requested", "confirmed"}],
                "outstanding_follow_ups": [x for x in followups if x["status"] == "open"],
                "notification_sent": False,
                "note": "Dashboard is a local coordination view; no partner or patient notification is sent."}

    @app.get("/api/evaluation")
    def evaluation(request: Request):
        user(request, admin=True)
        return evaluate()

    @app.get("/api/education")
    def education():
        return {"status": "public_source_learning_links_not_clinically_approved", "articles": ARTICLES}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "app/frontend/index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "app/frontend"), name="static")
    return app


app = create_app()

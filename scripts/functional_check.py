"""End-to-end functional check against a real app instance.

Exercises the flows a user actually performs — register, log in, reset a
password, upload a FHIR bundle, get gated as an unapproved researcher, then
build a cohort once approved — rather than asserting on code shape.

The unit and integration suites test units. This answers a different
question: does the product work when you use it?

Run: python scripts/functional_check.py
"""
import os, sys, tempfile
sys.path.insert(0, '/home/user/HealthDB')
os.environ.update(JWT_SECRET="functional-check", ENVIRONMENT="test",
                  ALLOW_SELF_SERVICE_REGISTRATION="true")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import api.main as main
from api.models import Base, User, PatientProfile, Consent
from datetime import datetime

fd, path = tempfile.mkstemp(suffix=".db"); os.close(fd)
engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(bind=engine)
S = sessionmaker(bind=engine)
def od():
    d = S()
    try: yield d
    finally: d.close()
main.app.dependency_overrides[main.get_db] = od
c = TestClient(main.app)

PW = "Str0ng!Passw0rd#2026"
results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  — ' + detail if detail and not ok else ''}")

# --- Registration + login ---
r = c.post("/api/auth/register", json={"email":"pt@example.com","password":PW,"name":"Pat","user_type":"patient"})
check("patient can register", r.status_code == 200, r.text[:90])
pt = {"Authorization": f"Bearer {r.json()['access_token']}"} if r.status_code==200 else {}

r = c.post("/api/auth/login", json={"email":"pt@example.com","password":PW})
check("patient can log in", r.status_code == 200, r.text[:90])

r = c.post("/api/auth/register", json={"email":"bad@example.com","password":PW,"name":"X","user_type":"admin"})
check("admin self-registration refused", r.status_code == 422)

# --- Patient surface ---
for ep in ["/api/patient/profile","/api/patient/consents","/api/patient/rewards","/api/patient/data-access-log"]:
    r = c.get(ep, headers=pt)
    check(f"patient reads {ep}", r.status_code == 200, f"{r.status_code} {r.text[:60]}")

# --- Password reset round trip ---
sent = {}
orig = main.deliver_notification
main.deliver_notification = lambda s,b: sent.setdefault("body", b)
try:
    c.post("/api/auth/request-password-reset", json={"email":"pt@example.com"})
finally:
    main.deliver_notification = orig
tok = sent.get("body","").split("token=")[-1].strip() if "token=" in sent.get("body","") else None
check("reset link is issued", bool(tok))
if tok:
    NEW = "Even5tronger!Pass#2026"
    r = c.post("/api/auth/reset-password", json={"token":tok,"new_password":NEW})
    check("password reset completes", r.status_code == 200, r.text[:80])
    check("new password works", c.post("/api/auth/login", json={"email":"pt@example.com","password":NEW}).status_code == 200)

# --- FHIR upload (needs consent) ---
s = S()
prof = s.query(PatientProfile).join(User).filter(User.email=="pt@example.com").first()
s.add(Consent(patient_id=prof.id, consent_type="research_data_sharing", status="active")); s.commit(); s.close()
BUNDLE = {"resourceType":"Bundle","entry":[
  {"resource":{"resourceType":"Patient","id":"p1","birthDate":"1970-05-12","name":[{"family":"Doe","given":["Jane"]}]}},
  {"resource":{"resourceType":"Condition","id":"c1","subject":{"reference":"Patient/p1"},
   "onsetDateTime":"2022-07-19","code":{"coding":[{"system":"http://snomed.info/sct","code":"254637007","display":"Lung carcinoma"}]}}}]}
r = c.post("/api/patient/connections/fhir", headers=pt, json={"source_name":"Test","bundle":BUNDLE})
check("FHIR bundle uploads", r.status_code == 200, r.text[:90])
r2 = c.get("/api/patient/extracted-data", headers=pt)
check("uploaded data readable", r2.status_code == 200)
check("no month/day in returned data",
      all(f not in r2.text for f in ["05-12","07-19","-05-","-07-"]), r2.text[:110])

# --- Researcher gating ---
r = c.post("/api/auth/register", json={"email":"res@example.com","password":PW,"name":"Res","user_type":"researcher"})
res = {"Authorization": f"Bearer {r.json()['access_token']}"}
check("unapproved researcher blocked", c.get("/api/researcher/studies", headers=res).status_code == 403)
check("patient cannot reach researcher routes", c.get("/api/researcher/studies", headers=pt).status_code == 403)

s = S(); s.query(User).filter(User.email=="res@example.com").update(
    {"is_verified": True, "researcher_approved_at": datetime.utcnow()}); s.commit(); s.close()
check("approved researcher allowed", c.get("/api/researcher/studies", headers=res).status_code == 200)

# --- Researcher workflow ---
r = c.post("/api/researcher/studies", headers=res,
           json={"name":"Functional check study","description":"","principal_investigator":""})
check("researcher creates a study", r.status_code == 200, r.text[:90])
r = c.get("/api/cohort/variables", headers=res)
check("variable inventory loads", r.status_code == 200, f"{r.status_code}")
r = c.post("/api/cohort/build", headers=res, json={"cancer_types":None})
check("cohort build runs", r.status_code == 200, f"{r.status_code} {r.text[:70]}")

# --- Public surface ---
for ep in ["/api/health","/api/stats/platform","/api/stats/cancer-types","/api/institutions"]:
    check(f"public {ep}", c.get(ep).status_code == 200)
check("seeded hospital names are gone",
      all(n not in c.get("/api/institutions").text for n in ["Stanford","Mayo Clinic","MD Anderson","Johns Hopkins"]))

failed = [n for n,ok,_ in results if not ok]
print(f"\n{len(results)-len(failed)}/{len(results)} functional checks passed")
if failed: print("FAILED:", failed)
os.unlink(path)
sys.exit(1 if failed else 0)

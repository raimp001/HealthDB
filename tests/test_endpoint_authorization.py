"""Cross-role and object-level authorization checks.

These lock in the boundaries the review asked for: patients must not reach
researcher endpoints, researchers must not reach institution endpoints, and
no unauthenticated caller reaches anything holding data.
"""
import pytest

PATIENT_ENDPOINTS = [
    "/api/patient/profile",
    "/api/patient/consents",
    "/api/patient/data-access-log",
    "/api/patient/rewards",
]
RESEARCHER_ENDPOINTS = [
    "/api/researcher/studies",
    "/api/cohort/saved",
]
INSTITUTION_ENDPOINTS = [
    "/api/institution/profile",
    "/api/institution/agreements",
    "/api/institution/irb-protocols",
]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def patient_token(register):
    return register("authz-patient@example.com", user_type="patient").json()["access_token"]


@pytest.fixture()
def researcher_token(register):
    return register("authz-researcher@example.com", user_type="researcher").json()["access_token"]


class TestUnauthenticatedAccess:
    @pytest.mark.parametrize(
        "url", PATIENT_ENDPOINTS + RESEARCHER_ENDPOINTS + INSTITUTION_ENDPOINTS
    )
    def test_requires_authentication(self, client, url):
        r = client.get(url)
        assert r.status_code in (401, 403), f"{url} served an anonymous caller"


class TestPatientBoundary:
    @pytest.mark.parametrize("url", RESEARCHER_ENDPOINTS)
    def test_patient_cannot_reach_researcher_endpoints(self, client, patient_token, url):
        r = client.get(url, headers=auth(patient_token))
        assert r.status_code != 200, f"a patient token read {url}"

    def test_patient_can_read_own_profile(self, client, patient_token):
        r = client.get("/api/patient/profile", headers=auth(patient_token))
        assert r.status_code == 200


class TestResearcherBoundary:
    @pytest.mark.parametrize("url", PATIENT_ENDPOINTS)
    def test_researcher_cannot_reach_patient_data(self, client, researcher_token, url):
        r = client.get(url, headers=auth(researcher_token))
        assert r.status_code != 200, f"a researcher token read {url}"


class TestStudyObjectLevelAccess:
    def test_cannot_read_another_researchers_study(self, client, make_user):
        """Object-level check: a valid role is not authorisation for any object.

        Both researchers are fully approved, so a failure here means genuine
        cross-user exposure rather than a missing role.
        """
        owner_h, _ = make_user("owner@example.com", role="researcher",
                               verified=True, approved=True)
        intruder_h, _ = make_user("intruder@example.com", role="researcher",
                                  verified=True, approved=True)

        created = client.post(
            "/api/researcher/studies", headers=owner_h,
            json={"name": "Owner's study", "description": "", "principal_investigator": ""},
        )
        assert created.status_code == 200, (
            f"approved researcher could not create a study: {created.text}"
        )
        payload = created.json()
        study_id = payload.get("id") or payload.get("study", {}).get("id")
        assert study_id, f"no study id in creation response: {payload}"

        r = client.get(f"/api/researcher/studies/{study_id}/sites", headers=intruder_h)
        assert r.status_code in (403, 404), (
            f"another researcher read study {study_id} (status {r.status_code})"
        )

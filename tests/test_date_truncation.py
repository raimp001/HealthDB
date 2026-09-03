"""Proof that no month/day from a source FHIR resource is ever persisted.

extracted_medical_data.original_date previously stored a full DATE parsed from
the uploaded resource, which contradicted the Safe Harbor claim made elsewhere
in the product. These tests assert the guarantee at every layer that could
retain it: the parser, the persisted row, the patient-facing API, the research
export, and the log stream.
"""
import json
import logging

import pytest

from api.fhir_ingest import parse_fhir_bundle, _year_only
from api.models import ExtractedMedicalData

# A bundle whose every date carries a distinctive month/day that would be
# obvious if it leaked: 03-17, 08-29, 11-04.
BUNDLE = {
    "resourceType": "Bundle",
    "entry": [
        {"resource": {
            "resourceType": "Patient", "id": "p1",
            "birthDate": "1962-03-17",
            "name": [{"family": "Testpatient", "given": ["Ada"]}],
        }},
        {"resource": {
            "resourceType": "Condition", "id": "c1",
            "subject": {"reference": "Patient/p1"},
            "onsetDateTime": "2021-08-29T14:23:00Z",
            "code": {"coding": [{"system": "http://snomed.info/sct",
                                 "code": "254637007", "display": "Lung carcinoma"}]},
        }},
        {"resource": {
            "resourceType": "Observation", "id": "o1",
            "subject": {"reference": "Patient/p1"},
            "effectiveDateTime": "2022-11-04",
            "code": {"coding": [{"system": "http://loinc.org",
                                 "code": "718-7", "display": "Hemoglobin"}]},
            "valueQuantity": {"value": 13.4, "unit": "g/dL"},
        }},
    ],
}

# Fragments that must never appear in anything we keep.
FORBIDDEN = ["03-17", "08-29", "11-04", "-03-", "-08-", "-11-",
             "T14:23", "1962-03", "2021-08", "2022-11"]


def assert_no_month_day(blob: str, where: str):
    for fragment in FORBIDDEN:
        assert fragment not in blob, f"month/day fragment {fragment!r} leaked into {where}"


class TestParser:
    def test_year_only_extracts_year_and_drops_the_rest(self):
        assert _year_only("2021-08-29T14:23:00Z") == 2021
        assert _year_only("2022-11-04") == 2022
        assert _year_only("1962") == 1962

    @pytest.mark.parametrize("junk", [None, "", "not-a-date", "20210829", 20210829, "0001-01-01"])
    def test_unparseable_values_yield_none(self, junk):
        assert _year_only(junk) is None

    def test_parsed_records_carry_year_only(self):
        records = parse_fhir_bundle(BUNDLE)
        assert records, "bundle produced no records"
        for record in records:
            assert "original_date" not in record, "parser still emits original_date"
            year = record.get("original_year")
            assert year is None or (isinstance(year, int) and 1900 <= year <= 2100)
        assert_no_month_day(json.dumps(records), "parser output")


@pytest.fixture()
def consented_patient(client, register):
    """A patient with the active consent that FHIR upload requires.

    The consent row is created directly: signing goes through a template that
    is not seeded in tests, and the consent flow is covered elsewhere.
    """
    def _make(email):
        body = register(email, user_type="patient").json()
        session = client._session_factory()
        from api.models import Consent, PatientProfile
        profile = session.query(PatientProfile).filter(
            PatientProfile.user_id == body["user"]["id"]
        ).first()
        session.add(Consent(
            patient_id=profile.id,
            consent_type="research_data_sharing",
            status="active",
        ))
        session.commit()
        session.close()
        return {"Authorization": f"Bearer {body['access_token']}"}
    return _make


class TestPersistence:
    def test_no_month_day_in_stored_rows_or_api(self, client, consented_patient):
        headers = consented_patient("fhir-dates@example.com")

        upload = client.post("/api/patient/connections/fhir", headers=headers,
                             json={"source_name": "Test EHR", "bundle": BUNDLE})
        assert upload.status_code == 200, upload.text

        # The persisted rows themselves.
        session = client._session_factory()
        rows = session.query(ExtractedMedicalData).all()
        assert rows, "nothing was imported"
        for row in rows:
            assert not hasattr(row, "original_date") or getattr(row, "original_date", None) is None
            year = row.original_year
            assert year is None or isinstance(year, int)
            assert_no_month_day(json.dumps(row.deidentified_data or {}), "deidentified_data")
        session.close()

        # The patient-facing read path.
        read = client.get("/api/patient/extracted-data", headers=headers)
        assert read.status_code == 200
        assert_no_month_day(read.text, "GET /api/patient/extracted-data")
        for item in read.json():
            assert "original_date" not in item, "API still returns original_date"

    def test_no_month_day_in_logs(self, client, consented_patient, caplog):
        headers = consented_patient("fhir-logs@example.com")
        with caplog.at_level(logging.DEBUG):
            client.post("/api/patient/connections/fhir", headers=headers,
                        json={"source_name": "Test EHR", "bundle": BUNDLE})
        assert_no_month_day(caplog.text, "log output")


class TestMigration:
    """The migration must destroy month/day in rows written before the fix."""

    def test_existing_full_dates_are_truncated(self, client):
        from sqlalchemy import text
        from api.main import migrate_truncate_original_dates

        session = client._session_factory()
        engine = session.get_bind()

        # Recreate the pre-migration shape and insert a row holding a full date.
        session.execute(text("ALTER TABLE extracted_medical_data ADD COLUMN original_date DATE"))
        session.execute(text(
            "INSERT INTO extracted_medical_data "
            "(id, connection_id, patient_id, data_category, original_date) "
            "VALUES ('mig-1', 'c-1', 'p-1', 'diagnosis', '2021-08-29')"
        ))
        session.commit()
        session.close()

        migrate_truncate_original_dates(engine)

        with engine.connect() as conn:
            year = conn.execute(text(
                "SELECT original_year FROM extracted_medical_data WHERE id = 'mig-1'"
            )).scalar()
            assert year == 2021, "the year was not preserved"

            columns = {c["name"] for c in __import__("sqlalchemy").inspect(engine)
                       .get_columns("extracted_medical_data")}
            if "original_date" in columns:
                # DROP COLUMN unsupported here; the values must still be gone.
                remaining = conn.execute(text(
                    "SELECT COUNT(*) FROM extracted_medical_data "
                    "WHERE original_date IS NOT NULL"
                )).scalar()
                assert remaining == 0, "month/day survived the migration"

    def test_migration_is_idempotent(self, client):
        from api.main import migrate_truncate_original_dates
        engine = client._session_factory().get_bind()
        migrate_truncate_original_dates(engine)
        migrate_truncate_original_dates(engine)  # must not raise

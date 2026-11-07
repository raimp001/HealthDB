"""Proof that no month/day from a source FHIR resource is ever persisted.

extracted_medical_data.original_date previously stored a full DATE parsed
from the uploaded resource, which contradicted the Safe Harbor language used
elsewhere in the product. These tests assert the guarantee at every layer
that could retain it: the parser, the persisted row, the patient-facing API,
and the log stream.
"""
import json
import logging
from datetime import datetime

import pytest

from api.fhir_ingest import parse_fhir_bundle, _year_only
from api.models import ExtractedMedicalData

# Every date carries a distinctive month/day that would be obvious if leaked.
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

FORBIDDEN = ["03-17", "08-29", "11-04", "-03-", "-08-", "-11-",
             "T14:23", "1962-03", "2021-08", "2022-11"]

# Timestamps this platform writes about its own processing. They are not
# source data and never derive from the bundle — see api/provenance.py, where
# ingested_at is datetime.utcnow().
#
# They have to come out before the scan, because the bare "-MM-" fragments
# above match any ISO date at all. Three months a year — March, August and
# November — an arrival timestamp contains one, and this test failed for the
# calendar rather than for a leak. A PHI test that cries wolf on a schedule
# is worse than no test: "the date tests are flaky" is exactly how a real
# leak gets waved through.
#
# Excluding them is only safe if they really are clocks, so
# assert_platform_timestamps_are_recent checks that before they are dropped.
# extracted_date is the row's own created-at (models.py: default=utcnow),
# not a clinical date from the bundle.
PLATFORM_TIMESTAMP_FIELDS = ("ingested_at", "extracted_date")


def strip_platform_timestamps(value):
    """The same structure with this platform's own timestamps removed."""
    if isinstance(value, dict):
        return {key: strip_platform_timestamps(item)
                for key, item in value.items()
                if key not in PLATFORM_TIMESTAMP_FIELDS}
    if isinstance(value, list):
        return [strip_platform_timestamps(item) for item in value]
    return value


def assert_platform_timestamps_are_recent(value, where: str):
    """Every excluded timestamp is a clock reading, not a date from the bundle.

    Without this the exclusion above would be a hole: a source date copied
    into ingested_at would be skipped by the scan precisely because it is
    named like a platform field.
    """
    now = datetime.utcnow()
    for field, stamp in _platform_timestamps(value):
        parsed = datetime.fromisoformat(str(stamp).replace("Z", ""))
        age = abs((now - parsed).total_seconds())
        assert age < 600, (
            f"{field} in {where} is {stamp}, which is not a clock reading — "
            "it may carry a date from the source bundle"
        )


def _platform_timestamps(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in PLATFORM_TIMESTAMP_FIELDS:
                yield f"{path}.{key}".lstrip("."), item
            else:
                yield from _platform_timestamps(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _platform_timestamps(item, f"{path}[{index}]")


def assert_no_month_day(blob: str, where: str):
    for fragment in FORBIDDEN:
        assert fragment not in blob, f"month/day fragment {fragment!r} leaked into {where}"


def assert_no_source_month_day(value, where: str):
    """Scan a structure for leaked source month/day, timestamps aside."""
    assert_platform_timestamps_are_recent(value, where)
    assert_no_month_day(json.dumps(strip_platform_timestamps(value)), where)


class TestParser:
    def test_year_only_extracts_year_and_drops_the_rest(self):
        assert _year_only("2021-08-29T14:23:00Z") == 2021
        assert _year_only("2022-11-04") == 2022
        assert _year_only("1962") == 1962

    @pytest.mark.parametrize("junk", [None, "", "not-a-date", "20210829", 20210829])
    def test_unparseable_values_yield_none(self, junk):
        assert _year_only(junk) is None

    def test_an_impossible_year_is_read_not_erased(self):
        """"No date was recorded" and "the date cannot be true" differ.

        Erasing an impossible year here would hide it behind the same None a
        genuinely undated record uses, so a researcher counting dated records
        gets a quietly wrong denominator and nobody ever learns the source
        was wrong. The parser reads what is there; ingest validation is what
        refuses it.
        """
        assert _year_only("0001-01-01") == 1
        assert _year_only("1782-01-01") == 1782

        from api.ingest_validation import check_record
        refused = check_record({"data_category": "diagnosis", "data_type": "condition",
                                "original_year": _year_only("1782-01-01"),
                                "data": {"display": "AML"}})
        assert refused and "1782" in refused

    def test_parsed_records_carry_year_only(self):
        records = parse_fhir_bundle(BUNDLE)
        assert records, "bundle produced no records"
        for record in records:
            assert "original_date" not in record, "parser still emits original_date"
            year = record.get("original_year")
            assert year is None or (isinstance(year, int) and 1900 <= year <= 2100)
        assert_no_source_month_day(records, "parser output")


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

        session = client._session_factory()
        rows = session.query(ExtractedMedicalData).all()
        assert rows, "nothing was imported"
        for row in rows:
            assert getattr(row, "original_date", None) is None
            year = row.original_year
            assert year is None or isinstance(year, int)
            assert_no_source_month_day(row.deidentified_data or {}, "deidentified_data")
            assert_no_source_month_day(row.provenance or {}, "provenance")
        session.close()

        read = client.get("/api/patient/extracted-data", headers=headers)
        assert read.status_code == 200
        assert_no_source_month_day(read.json(), "GET /api/patient/extracted-data")
        for item in read.json():
            assert "original_date" not in item, "API still returns original_date"

    def test_the_year_survives_and_is_the_source_year(self, client, consented_patient):
        """Truncating to a year must not amount to throwing the year away.

        Asserting only "None or an int" let a regression through in which the
        upload path re-parsed an already-parsed integer as if it were a
        string and stored None for every record. Nothing failed: the column
        is nullable, and a missing year is indistinguishable from a record
        whose source never carried a date. The effect was that everyone who
        uploaded dropped out of every date-scoped cohort. They had
        contributed, and were silently unreachable.
        """
        headers = consented_patient("fhir-year-kept@example.com")
        upload = client.post("/api/patient/connections/fhir", headers=headers,
                             json={"source_name": "Test EHR", "bundle": BUNDLE})
        assert upload.status_code == 200, upload.text

        session = client._session_factory()
        years = {(row.data_category, row.original_year)
                 for row in session.query(ExtractedMedicalData).all()}
        session.close()

        assert ("diagnosis", 2021) in years, years
        assert ("lab_results", 2022) in years, years

    def test_no_month_day_in_logs(self, client, consented_patient, caplog):
        headers = consented_patient("fhir-logs@example.com")
        with caplog.at_level(logging.DEBUG):
            client.post("/api/patient/connections/fhir", headers=headers,
                        json={"source_name": "Test EHR", "bundle": BUNDLE})
        assert_no_month_day(caplog.text, "log output")


class TestMigration:
    def test_existing_full_dates_are_truncated(self, client):
        from sqlalchemy import text, inspect
        from api.main import migrate_truncate_original_dates

        session = client._session_factory()
        engine = session.get_bind()
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

            columns = {c["name"] for c in inspect(engine).get_columns("extracted_medical_data")}
            if "original_date" in columns:
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


class TestTheLeakScanItself:
    """The scan excludes this platform's timestamps. That must not be a hole.

    These were added after the suite failed in November because an arrival
    timestamp contained "-11-". Excluding such fields fixes the false alarm
    and would, done carelessly, create a place a real source date could hide.
    """

    def test_a_real_leak_is_still_caught(self):
        leaked = [{"data": {"onset": "2022-11-04"}}]
        with pytest.raises(AssertionError, match="leaked into"):
            assert_no_source_month_day(leaked, "a record that leaked")

    def test_a_leak_nested_under_provenance_is_still_caught(self):
        leaked = [{"provenance": {"source_system": "x", "note": "1962-03-17"}}]
        with pytest.raises(AssertionError, match="leaked into"):
            assert_no_source_month_day(leaked, "provenance")

    def test_a_source_date_hidden_in_a_platform_field_is_caught(self):
        """The hole the exclusion would otherwise open.

        A field named like a clock is skipped by the fragment scan, so the
        scan has to prove it is a clock before skipping it.
        """
        disguised = [{"provenance": {"ingested_at": "1962-03-17T00:00:00"}}]
        with pytest.raises(AssertionError, match="not a clock reading"):
            assert_no_source_month_day(disguised, "disguised")

    def test_a_genuine_arrival_timestamp_passes_in_any_month(self):
        """Including March, August and November, when the old scan failed."""
        now = datetime.utcnow().isoformat()
        assert_no_source_month_day(
            [{"provenance": {"ingested_at": now}, "data": {"year": 2022}}],
            "a clean record")

    def test_the_stripper_leaves_everything_else_alone(self):
        record = {"a": 1, "provenance": {"ingested_at": "x", "source": "keep"},
                  "items": [{"ingested_at": "y", "z": 2}]}
        assert strip_platform_timestamps(record) == {
            "a": 1, "provenance": {"source": "keep"}, "items": [{"z": 2}]}

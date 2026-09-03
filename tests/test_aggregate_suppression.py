"""Small-cell suppression on public and researcher-visible aggregates.

A count of one or two over a rare cancer type can identify an individual.
/api/stats/cancer-types previously published every row with its exact count
and no threshold at all.
"""
import api.main as main
from api.models import CancerDiagnosis

THRESHOLD = main.MIN_AGGREGATE_CELL_SIZE


def seed_diagnoses(client, cancer_type, patient_count):
    session = client._session_factory()
    for i in range(patient_count):
        session.add(CancerDiagnosis(
            hashed_patient_id=f"{cancer_type}-patient-{i}",
            cancer_type=cancer_type,
        ))
    session.commit()
    session.close()


class TestHelper:
    def test_counts_at_or_above_the_threshold_pass_through(self):
        assert main.suppress_small_cell(THRESHOLD) == THRESHOLD
        assert main.suppress_small_cell(THRESHOLD + 500) == THRESHOLD + 500

    def test_counts_below_the_threshold_are_withheld(self):
        for n in range(1, THRESHOLD):
            assert main.suppress_small_cell(n) is None, f"count {n} was published"

    def test_zero_is_reported_as_zero(self):
        """Nobody reveals nothing, and suppressing it would misrepresent an empty pilot."""
        assert main.suppress_small_cell(0) == 0

    def test_none_stays_none(self):
        assert main.suppress_small_cell(None) is None


class TestCancerTypeEndpoint:
    def test_small_categories_are_omitted_entirely(self, client):
        """The category name alone would disclose that someone has that cancer."""
        seed_diagnoses(client, "Rare Sarcoma", 2)
        seed_diagnoses(client, "Common Carcinoma", THRESHOLD + 5)

        r = client.get("/api/stats/cancer-types")
        assert r.status_code == 200
        body = r.json()

        assert "Rare Sarcoma" not in r.text, (
            "a category below the threshold was named in the response"
        )
        names = [row["name"] for row in body["cancer_types"]]
        assert "Common Carcinoma" in names
        assert body["withheld_categories"] >= 1, "the omission was not disclosed"
        assert body["min_cell_size"] == THRESHOLD

    def test_reported_rows_are_all_at_or_above_the_threshold(self, client):
        seed_diagnoses(client, "Type A", 1)
        seed_diagnoses(client, "Type B", THRESHOLD)
        body = client.get("/api/stats/cancer-types").json()
        for row in body["cancer_types"]:
            assert row["patients"] >= THRESHOLD


class TestPlatformStatsEndpoint:
    def test_patient_counts_are_suppressed(self, client):
        seed_diagnoses(client, "Type C", 3)
        body = client.get("/api/stats/platform").json()
        assert body["total_patients"] is None, (
            f"a patient count of 3 was published as {body['total_patients']}"
        )
        assert body["min_cell_size"] == THRESHOLD

    def test_large_counts_are_reported(self, client):
        seed_diagnoses(client, "Type D", THRESHOLD + 3)
        body = client.get("/api/stats/platform").json()
        assert body["total_patients"] == THRESHOLD + 3

    def test_empty_platform_reports_zero_not_null(self, client):
        body = client.get("/api/stats/platform").json()
        assert body["total_patients"] == 0

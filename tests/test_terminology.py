"""Tests for diagnosis coding.

The risk with a terminology map is not that it fails to match — it is that it
matches the wrong thing and looks authoritative doing it. Most of these assert
that ambiguous input stays unmapped and that adding codes never narrows a
cohort that worked before.
"""
import pytest

from api.cohort_query import CohortCriteria, matching_patient_ids, text_matches
from api.models import ExtractedMedicalData
from api.terminology import (
    UNMAPPED_BY_DESIGN,
    annotate,
    resolve,
    same_concept,
)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "AML", "aml", "  AML  ", "Acute Myeloid Leukemia",
    "acute myelogenous leukemia", "C92.0", "c92.0", "AML (C92.0)",
])
def test_every_way_of_writing_one_disease_resolves_alike(text):
    assert resolve(text).code == "C92.0"


@pytest.mark.parametrize("text", ["", "   ", None, "not a disease at all"])
def test_unrecognized_input_resolves_to_nothing(text):
    assert resolve(text) is None


@pytest.mark.parametrize("term", sorted(UNMAPPED_BY_DESIGN))
def test_terms_left_unmapped_on_purpose_stay_unmapped(term):
    """A coder ruled these ambiguous. A synonym edit must not quietly undo it."""
    assert resolve(term) is None


def test_an_ambiguous_term_does_not_resolve_to_one_of_its_sites():
    """'colorectal' spans C18-C20; collapsing it would silently change cohorts."""
    assert resolve("colorectal cancer") is None
    assert same_concept("colorectal cancer", "C18.9") is False


def test_an_unknown_but_well_formed_code_is_carried_through():
    """A site's own coding is better kept than discarded."""
    concept = resolve("C99.9")
    assert concept.code == "C99.9"


def test_a_preset_label_defers_to_its_code():
    """In 'Label (CODE)' the code wins; the label is a human hint."""
    assert resolve("Anything At All (C90.0)").code == "C90.0"


def test_an_unmapped_label_with_no_valid_code_stays_unmapped():
    assert resolve("cancer (something)") is None


def test_same_concept_is_false_when_either_side_is_unmapped():
    """An unresolved term must fall back to text, not match everything."""
    assert same_concept("AML", "gibberish") is False
    assert same_concept("gibberish", "gibberish") is False


@pytest.mark.parametrize("left,right", [
    ("AML", "CLL"), ("DLBCL", "follicular lymphoma"),
    ("breast cancer", "lung cancer"), ("C90.0", "C92.0"),
])
def test_different_diseases_never_collide(left, right):
    assert same_concept(left, right) is False


# ---------------------------------------------------------------------------
# Annotation is additive
# ---------------------------------------------------------------------------

def test_annotation_keeps_the_source_wording():
    annotated = annotate({"display": "acute myeloid leukemia", "stage": "II"})
    assert annotated["display"] == "acute myeloid leukemia"
    assert annotated["stage"] == "II"
    assert annotated["icd10_code"] == "C92.0"
    assert annotated["coding_source"] == "healthdb-terminology-map"


def test_annotation_does_not_mutate_its_input():
    original = {"display": "AML"}
    annotate(original)
    assert original == {"display": "AML"}


def test_annotation_leaves_an_unmappable_record_alone():
    data = {"display": "some rare unnamed tumour"}
    assert annotate(data) == data


def test_annotation_never_overwrites_a_code_the_site_supplied():
    """A site's own coding outranks our mapping."""
    data = {"display": "AML", "icd10_code": "C92.5"}
    assert annotate(data)["icd10_code"] == "C92.5"


def test_annotation_tolerates_a_non_dict():
    assert annotate("not a dict") == "not a dict"


# ---------------------------------------------------------------------------
# Cohort matching
# ---------------------------------------------------------------------------

def test_two_sites_wording_a_disease_differently_land_in_one_cohort():
    """The whole point: cross-site cohorts stop being string matching."""
    records = [
        ExtractedMedicalData(patient_id="site-a", connection_id="c",
                             data_category="diagnosis", original_year=2020,
                             deidentified_data={"display": "AML"}),
        ExtractedMedicalData(patient_id="site-b", connection_id="c",
                             data_category="diagnosis", original_year=2020,
                             deidentified_data={"display": "Acute myelogenous leukemia"}),
        ExtractedMedicalData(patient_id="site-c", connection_id="c",
                             data_category="diagnosis", original_year=2020,
                             deidentified_data={"code": "C92.0"}),
    ]
    matched = matching_patient_ids(records, CohortCriteria(cancer_types=["AML"]))
    assert matched == {"site-a", "site-b", "site-c"}


def test_coding_does_not_pull_in_a_different_disease():
    records = [
        ExtractedMedicalData(patient_id="p1", connection_id="c",
                             data_category="diagnosis", original_year=2020,
                             deidentified_data={"display": "CLL"}),
    ]
    assert matching_patient_ids(records, CohortCriteria(cancer_types=["AML"])) == set()


def test_an_unmapped_diagnosis_still_matches_its_own_text():
    """Adding terminology must not break cohorts that already worked."""
    records = [
        ExtractedMedicalData(patient_id="p1", connection_id="c",
                             data_category="diagnosis", original_year=2020,
                             deidentified_data={"display": "Rare unnamed sarcoma"}),
    ]
    matched = matching_patient_ids(
        records, CohortCriteria(cancer_types=["Rare unnamed sarcoma"]))
    assert matched == {"p1"}


def test_terminology_only_widens_matching_never_narrows_it():
    """Anything that matched as a string must still match."""
    for value in ["Multiple Myeloma", "Stage IV", "Rare unnamed sarcoma"]:
        assert text_matches(value, value, "diagnosis") is True


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------

def test_a_parsed_fhir_diagnosis_arrives_coded():
    from api.fhir_ingest import parse_fhir_bundle

    bundle = {"entry": [{"resource": {
        "resourceType": "Condition",
        "code": {"text": "Acute myeloid leukemia"},
        "onsetDateTime": "2020-05-04",
    }}]}
    diagnoses = [r for r in parse_fhir_bundle(bundle) if r["data_category"] == "diagnosis"]
    assert diagnoses, "the bundle should yield a diagnosis record"
    assert diagnoses[0]["data"]["icd10_code"] == "C92.0"
    # Coding must not resurrect the discarded month and day.
    assert diagnoses[0]["original_year"] == 2020
    assert "original_date" not in diagnoses[0]

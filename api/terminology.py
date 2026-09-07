"""Resolve free-text diagnoses to a coded concept.

Cohorts match on strings today. "AML", "acute myeloid leukemia" and "C92.0"
are the same disease and three different cohorts, which is fine inside one
site typing consistently and useless across two. Multi-institution research
is the product, so string matching is the thing standing in front of it.

This maps text to ICD-10-CM. It is deliberately small and deliberately
conservative:

* **A concept is added only when the mapping is unambiguous.** A term that
  could reasonably resolve to two codes is left unmapped, because a cohort
  built on a wrong code is worse than one built on a string — it looks
  authoritative.
* **Nothing is overwritten.** Normalization annotates a record with a code
  and keeps the original text beside it. The source system's wording is
  evidence; a mapping is an interpretation.
* **Unmapped is a normal outcome, not an error.** `resolve` returns None and
  callers fall back to text matching.

**This starter set has not been reviewed by a clinical coder.** It covers
common adult oncology and is enough to make cross-site cohorts work in the
pilot. Before real data, a coder should review the map, decide the site-level
vs. subtype-level granularity, and rule on the terms deliberately omitted
below. `UNMAPPED_BY_DESIGN` records those decisions so they are not silently
re-added by whoever edits this next.
"""
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class Concept:
    """One coded disease concept."""
    code: str
    display: str
    system: str = "http://hl7.org/fhir/sid/icd-10-cm"

    def as_dict(self) -> dict:
        return {"code": self.code, "display": self.display, "system": self.system}


# code -> (canonical display, synonyms). Synonyms are matched case- and
# punctuation-insensitively; see `_key`.
_CONCEPTS: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    # Haematological
    "C90.0": ("Multiple myeloma", ("multiple myeloma", "myeloma", "mm", "plasma cell myeloma")),
    "C92.0": ("Acute myeloblastic leukemia", ("acute myeloid leukemia", "acute myeloblastic leukemia", "aml", "acute myelogenous leukemia")),
    "C92.1": ("Chronic myeloid leukemia, BCR/ABL-positive", ("chronic myeloid leukemia", "cml", "chronic myelogenous leukemia")),
    # "ALL" is the established abbreviation and the cohort builder's preset
    # label, so it is mapped. It is also an ordinary English word: a free-text
    # field containing only "all" would mis-code. Annotation only reads
    # diagnosis-named fields, which keeps the blast radius small, but a coder
    # reviewing this map should decide whether the abbreviation stays.
    "C91.0": ("Acute lymphoblastic leukemia", ("acute lymphoblastic leukemia", "all", "acute lymphocytic leukemia")),
    "C91.1": ("Chronic lymphocytic leukemia of B-cell type", ("chronic lymphocytic leukemia", "cll")),
    "C83.3": ("Diffuse large B-cell lymphoma", ("diffuse large b cell lymphoma", "dlbcl", "diffuse large b-cell lymphoma")),
    "C82.9": ("Follicular lymphoma, unspecified", ("follicular lymphoma",)),
    "C81.9": ("Hodgkin lymphoma, unspecified", ("hodgkin lymphoma", "hodgkins lymphoma", "hodgkin's lymphoma", "hodgkin disease")),
    # Solid tumours, site-level
    "C50.919": ("Malignant neoplasm of unspecified site of unspecified female breast", ("breast cancer", "breast carcinoma", "carcinoma of breast")),
    "C34.90": ("Malignant neoplasm of unspecified part of unspecified bronchus or lung", ("lung cancer", "lung carcinoma", "bronchogenic carcinoma")),
    "C18.9": ("Malignant neoplasm of colon, unspecified", ("colon cancer", "colon carcinoma", "colonic carcinoma")),
    "C20": ("Malignant neoplasm of rectum", ("rectal cancer", "rectum cancer", "carcinoma of rectum")),
    "C61": ("Malignant neoplasm of prostate", ("prostate cancer", "prostatic carcinoma", "carcinoma of prostate")),
    "C25.9": ("Malignant neoplasm of pancreas, unspecified", ("pancreatic cancer", "pancreas cancer", "carcinoma of pancreas")),
    "C43.9": ("Malignant melanoma of skin, unspecified", ("melanoma", "malignant melanoma", "cutaneous melanoma")),
    "C56.9": ("Malignant neoplasm of unspecified ovary", ("ovarian cancer", "ovary cancer", "carcinoma of ovary")),
    "C22.0": ("Liver cell carcinoma", ("hepatocellular carcinoma", "hcc", "liver cell carcinoma")),
    "C64.9": ("Malignant neoplasm of unspecified kidney, except renal pelvis", ("kidney cancer", "renal cell carcinoma", "rcc")),
    "C67.9": ("Malignant neoplasm of bladder, unspecified", ("bladder cancer", "carcinoma of bladder")),
    "C71.9": ("Malignant neoplasm of brain, unspecified", ("brain cancer", "brain tumor", "brain tumour")),
    "C73": ("Malignant neoplasm of thyroid gland", ("thyroid cancer", "thyroid carcinoma")),
    "C16.9": ("Malignant neoplasm of stomach, unspecified", ("gastric cancer", "stomach cancer", "carcinoma of stomach")),
    "C15.9": ("Malignant neoplasm of esophagus, unspecified", ("esophageal cancer", "oesophageal cancer")),
}

# Terms a coder must rule on, kept here so the reasoning is not lost.
UNMAPPED_BY_DESIGN = {
    "colorectal cancer": "Spans C18-C20. Site matters for cohorts; do not collapse.",
    "leukemia": "Too broad. Acute vs chronic and lineage change the cohort entirely.",
    "lymphoma": "Too broad. Hodgkin and non-Hodgkin are different diseases.",
    "glioblastoma": "C71.9 loses the histology that defines it. Needs a morphology axis.",
    "triple negative breast cancer": "A receptor status, not an ICD-10 code. Belongs in molecular markers.",
    "nsclc": "Histology within C34; the code does not carry it.",
    "sclc": "Histology within C34; the code does not carry it.",
    "carcinoma": "A morphology, not a site.",
    "cancer": "Not a diagnosis.",
}


def _key(value) -> str:
    """Fold case, punctuation and spacing so lookups survive real-world text."""
    text = re.sub(r"[^a-z0-9 ]+", " ", str(value).strip().lower())
    return re.sub(r"\s+", " ", text).strip()


_BY_SYNONYM: Dict[str, Concept] = {}
for _code, (_display, _synonyms) in _CONCEPTS.items():
    _concept = Concept(_code, _display)
    _BY_SYNONYM[_key(_code)] = _concept
    _BY_SYNONYM[_key(_display)] = _concept
    for _synonym in _synonyms:
        _BY_SYNONYM[_key(_synonym)] = _concept

_BY_CODE: Dict[str, Concept] = {code: Concept(code, display) for code, (display, _) in _CONCEPTS.items()}

# "AML (C92.0)" — the shape the cohort builder's presets use.
_PRESET = re.compile(r"^(?P<label>.*?)\s*\((?P<code>[A-Za-z]\d[\w.]*)\)\s*$")
_BARE_CODE = re.compile(r"^[A-Za-z]\d{2}(?:\.[\dA-Za-z]{1,4})?$")


def resolve(value) -> Optional[Concept]:
    """Return the concept `value` names, or None when it is not unambiguous.

    Accepts a code, a canonical display, a known synonym, or the
    "Label (CODE)" preset shape. A term listed in UNMAPPED_BY_DESIGN always
    returns None, even if a future synonym edit would otherwise catch it.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    if _key(text) in UNMAPPED_BY_DESIGN:
        return None

    preset = _PRESET.match(text)
    if preset:
        # The code is authoritative; the label beside it is a human hint.
        coded = resolve(preset.group("code"))
        if coded:
            return coded
        text = preset.group("label").strip()
        if _key(text) in UNMAPPED_BY_DESIGN:
            return None

    direct = _BY_SYNONYM.get(_key(text))
    if direct:
        return direct

    # An unknown but well-formed ICD-10 code is still a code. Carrying it
    # through unmapped is better than discarding a site's own coding.
    if _BARE_CODE.match(text):
        code = text.upper()
        return _BY_CODE.get(code) or Concept(code, code)
    return None


def same_concept(left, right) -> bool:
    """True when both sides resolve to the same code.

    False when either is unmapped: an unresolved term must fall back to text
    matching rather than silently matching everything.
    """
    a, b = resolve(left), resolve(right)
    return bool(a and b and a.code == b.code)


def annotate(data: dict) -> dict:
    """Add a coded concept to a diagnosis payload without altering it.

    Returns a new dict. The source wording stays exactly as the site sent it;
    `icd10_code` and `icd10_display` are added beside it, and a `coding_source`
    marks this as a derived mapping rather than something the site asserted.
    """
    if not isinstance(data, dict):
        return data
    if data.get("icd10_code"):
        return dict(data)

    for field in ("code", "icd_code", "display", "cancer_type", "diagnosis"):
        concept = resolve(data.get(field))
        if concept:
            return dict(
                data,
                icd10_code=concept.code,
                icd10_display=concept.display,
                coding_source="healthdb-terminology-map",
            )
    return dict(data)

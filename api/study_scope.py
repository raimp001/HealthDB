"""What a patient agreed to, and whether it is still that.

Somebody joins a study about remission duration in myeloma. Months later the
purpose is rewritten, the population is redrawn, or the variables collected
grow to include their molecular profile. Nobody asks them again. Their
agreement is now attached to something that no longer exists, and the system
carries on as though nothing happened — which is the quietest way a research
platform becomes extractive.

Consent attaches to a purpose, not to a study id. So the material parts of a
study are fingerprinted, that fingerprint is recorded against the enrolment
when the person joins, and a mismatch afterwards means the study has moved
away from what they agreed to.

WHAT COUNTS AS MATERIAL
-----------------------
This is a judgement, and stating it is part of the work.

Material, because a patient's answer could reasonably differ:

* **purpose** — the study description. What is being asked.
* **eligibility** — who it is for. Being told a study is for people like you
  is part of why you say yes.
* **variables** — what will actually be taken. Agreeing to share a diagnosis
  is not agreeing to share a molecular profile.
* **population** — the cohort definition, by digest. Redrawing who is in the
  study changes the study.

Deliberately *not* material:

* **name** — a rename is not a change of purpose.
* **principal investigator** — a patient consents to a research purpose under
  governance, not to a person; staffing changes go through IRB amendment.
  Re-asking on every personnel change would produce fatigue, and consent
  fatigue erodes consent far more effectively than it protects it.
* **status, recruiting flag, patient count** — bookkeeping.

The bias throughout is toward exclusion. When a study has moved and the
person has not re-affirmed, their records leave the eligible pool until they
say otherwise. Silence is not consent, and a system that treats it as consent
is not asking a question — it is announcing a decision.
"""
from typing import Any, Mapping, Optional

from .release_manifest import criteria_digest

# The fields a change to which should send someone back to the question.
MATERIAL_FIELDS = ("purpose", "eligibility", "variables", "population")


def scope_of(study, cohort=None) -> dict:
    """The parts of a study a patient's answer could reasonably depend on."""
    return {
        "purpose": (study.description or "").strip(),
        "eligibility": (study.eligibility_summary or "").strip(),
        # Sorted: reordering a selection is not a change to it.
        "variables": sorted(study.selected_variables or []),
        "population": criteria_digest(cohort.criteria) if cohort else None,
    }


def scope_digest(study, cohort=None) -> str:
    return criteria_digest(scope_of(study, cohort))


def describe_change(before: Optional[Mapping[str, Any]],
                    after: Mapping[str, Any]) -> list:
    """Plain sentences for what moved, for the person being asked again.

    Says which parts changed, not the old and new text side by side. A
    re-consent screen is a question, not a diff review; someone deciding
    whether to stay in a study needs to know what kind of thing changed and
    then read the study as it now stands.
    """
    if not before:
        return ["This study changed, but what it looked like when you joined "
                "was not recorded."]
    labels = {
        "purpose": "What the study is trying to find out has changed.",
        "eligibility": "Who the study is for has changed.",
        "variables": "The information the study would collect has changed.",
        "population": "The group of participants the study draws on has changed.",
    }
    return [labels[field] for field in MATERIAL_FIELDS
            if before.get(field) != after.get(field)]

PHI_DETECTION_RULES = {
    "entities": ["PERSON", "DATE", "LOCATION", "PHONE_NUMBER"],
    "threshold": 0.85,  # Confidence threshold
    "context": ["patient", "medical", "diagnosis"]
}

DEIDENTIFICATION_METHODS = {
    "PERSON": "replace",
    "DATE": "mask",
    "LOCATION": "replace",
    "PHONE_NUMBER": "replace"
}
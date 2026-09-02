"""
Hardcoded reference ranges for common lab tests.
Each test maps to: unit, normal range, and a 'critical' band beyond which
a result is life-threatening (not just abnormal).

Values outside [low, high] but inside the critical band => WARNING
Values outside the critical band => CRITICAL
"""

REFERENCE_RANGES = {
    "hemoglobin":      {"unit": "g/dL",   "low": 12.0,  "high": 16.0,  "critical_low": 7.0,   "critical_high": 20.0},
    "wbc":             {"unit": "10^3/uL","low": 4.0,   "high": 11.0,  "critical_low": 2.0,   "critical_high": 30.0},
    "platelet_count":  {"unit": "10^3/uL","low": 150,   "high": 450,   "critical_low": 20,    "critical_high": 1000},
    "glucose":         {"unit": "mg/dL",  "low": 70,    "high": 100,   "critical_low": 40,    "critical_high": 400},
    "creatinine":      {"unit": "mg/dL",  "low": 0.6,   "high": 1.3,   "critical_low": 0.2,   "critical_high": 4.0},
    "sodium":          {"unit": "mmol/L", "low": 135,   "high": 145,   "critical_low": 120,   "critical_high": 160},
    "potassium":       {"unit": "mmol/L", "low": 3.5,   "high": 5.1,   "critical_low": 2.5,   "critical_high": 6.5},
    "alt":             {"unit": "U/L",    "low": 7,     "high": 56,    "critical_low": 0,     "critical_high": 200},
    "ast":             {"unit": "U/L",    "low": 10,    "high": 40,    "critical_low": 0,     "critical_high": 200},
    "total_cholesterol":{"unit": "mg/dL", "low": 125,   "high": 200,   "critical_low": 50,    "critical_high": 300},
    "tsh":             {"unit": "mIU/L",  "low": 0.4,   "high": 4.0,   "critical_low": 0.01,  "critical_high": 20.0},
    "crp":             {"unit": "mg/L",   "low": 0,     "high": 10,    "critical_low": 0,     "critical_high": 100},
}


def normalize_test_name(name: str) -> str:
    """'Hemoglobin (Hb)' -> 'hemoglobin' so lookups are forgiving."""
    return (
        name.strip().lower()
        .replace(" ", "_")
        .split("(")[0]
        .strip("_")
    )

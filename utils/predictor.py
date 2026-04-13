"""
predictor.py
Loads the trained model + scaler, preprocesses raw user input,
returns risk score, risk label, and per-feature contributions.

FIXES:
 - Added input validation with clamping to prevent out-of-range crashes
 - MODEL_PATH / SCALER_PATH now work from any working directory via __file__
 - _get_contributions: guarded against zero std (already present, kept)
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
MODEL_PATH  = BASE_DIR / "models" / "best_model.pkl"
SCALER_PATH = BASE_DIR / "models" / "scaler.pkl"

FEATURES = [
    'age', 'gender', 'height', 'weight', 'ap_hi', 'ap_lo',
    'cholesterol', 'gluc', 'smoke', 'alco', 'active',
    'bmi', 'pulse_pressure', 'map', 'hypertension', 'obese', 'age_group'
]

FEATURE_LABELS = {
    'age':            'Age',
    'gender':         'Gender',
    'height':         'Height (cm)',
    'weight':         'Weight (kg)',
    'ap_hi':          'Systolic BP',
    'ap_lo':          'Diastolic BP',
    'cholesterol':    'Cholesterol',
    'gluc':           'Glucose',
    'smoke':          'Smoker',
    'alco':           'Alcohol use',
    'active':         'Physically active',
    'bmi':            'BMI',
    'pulse_pressure': 'Pulse pressure',
    'map':            'Mean arterial pressure',
    'hypertension':   'Hypertension flag',
    'obese':          'Obesity flag',
    'age_group':      'Age group',
}

NORMAL_RANGES = {
    'ap_hi':          (90,  120),
    'ap_lo':          (60,  80),
    'bmi':            (18.5, 24.9),
    'pulse_pressure': (30,  50),
    'map':            (70,  100),
}

_model  = None
_scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        _model  = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)


def validate_inputs(raw: dict) -> dict:
    """
    ✅ NEW: Clamp / correct obviously invalid input values before feature
    engineering so the model never receives garbage.
    Returns the sanitised dict (does not mutate the original).
    """
    r = dict(raw)
    r['age']    = max(18,  min(100, int(r.get('age', 45))))
    r['height'] = max(130, min(220, int(r.get('height', 165))))
    r['weight'] = max(30,  min(200, float(r.get('weight', 70))))
    r['ap_hi']  = max(80,  min(250, int(r.get('ap_hi', 120))))
    r['ap_lo']  = max(40,  min(200, int(r.get('ap_lo', 80))))
    # Ensure systolic > diastolic (prevents negative pulse pressure)
    if r['ap_hi'] <= r['ap_lo']:
        r['ap_hi'] = r['ap_lo'] + 10
    r['cholesterol'] = max(1, min(3, int(r.get('cholesterol', 1))))
    r['gluc']        = max(1, min(3, int(r.get('gluc', 1))))
    r['smoke']  = int(bool(r.get('smoke', 0)))
    r['alco']   = int(bool(r.get('alco', 0)))
    r['active'] = int(bool(r.get('active', 1)))
    r['gender'] = max(1, min(2, int(r.get('gender', 1))))
    return r


def engineer_features(raw: dict) -> dict:
    """
    Takes raw user inputs and returns a dict with all engineered features.
    """
    age    = raw['age']
    height = raw['height']
    weight = raw['weight']
    ap_hi  = raw['ap_hi']
    ap_lo  = raw['ap_lo']

    bmi            = round(weight / ((height / 100) ** 2), 2)
    pulse_pressure = ap_hi - ap_lo
    map_val        = round(ap_lo + pulse_pressure / 3, 2)
    hypertension   = int(ap_hi >= 140 or ap_lo >= 90)
    obese          = int(bmi >= 30)

    if age < 40:
        age_group = 0
    elif age < 50:
        age_group = 1
    elif age < 60:
        age_group = 2
    else:
        age_group = 3

    return {
        'age':            age,
        'gender':         raw['gender'],
        'height':         height,
        'weight':         weight,
        'ap_hi':          ap_hi,
        'ap_lo':          ap_lo,
        'cholesterol':    raw['cholesterol'],
        'gluc':           raw['gluc'],
        'smoke':          raw['smoke'],
        'alco':           raw['alco'],
        'active':         raw['active'],
        'bmi':            bmi,
        'pulse_pressure': pulse_pressure,
        'map':            map_val,
        'hypertension':   hypertension,
        'obese':          obese,
        'age_group':      age_group,
    }


def predict(raw: dict) -> dict:
    """
    Main prediction function.

    Parameters
    ----------
    raw : dict  — raw user inputs (age in years, etc.)

    Returns
    -------
    dict with keys:
        risk_score    : float  0–100
        risk_label    : str    'Low' | 'Moderate' | 'High'
        risk_color    : str    hex color for UI
        probability   : float  0–1
        engineered    : dict   all features after engineering
        contributions : list   [{'feature', 'label', 'value', 'contribution', 'direction'}]
        flagged       : list   features outside normal range
    """
    _load()

    # ✅ FIX: validate inputs before engineering
    raw = validate_inputs(raw)

    eng = engineer_features(raw)
    X   = pd.DataFrame([eng])[FEATURES].values

    prob = _model.predict_proba(X)[0][1]
    risk_score = round(prob * 100, 1)

    if prob < 0.35:
        risk_label = 'Low'
        risk_color = '#1D9E75'
    elif prob < 0.60:
        risk_label = 'Moderate'
        risk_color = '#EF9F27'
    else:
        risk_label = 'High'
        risk_color = '#E24B4A'

    contributions = _get_contributions(eng)

    flagged = []
    for feat, (lo, hi) in NORMAL_RANGES.items():
        val = eng.get(feat)
        if val is not None and (val < lo or val > hi):
            flagged.append({
                'feature': feat,
                'label':   FEATURE_LABELS[feat],
                'value':   val,
                'normal':  f'{lo}–{hi}',
            })

    return {
        'risk_score':    risk_score,
        'risk_label':    risk_label,
        'risk_color':    risk_color,
        'probability':   round(prob, 4),
        'engineered':    eng,
        'contributions': contributions,
        'flagged':       flagged,
    }


def _get_contributions(eng: dict) -> list:
    """
    Compute per-feature risk contributions using tree feature importances.
    """
    _load()
    importances = _model.feature_importances_

    POP_MEANS = {
        'age': 53.0, 'gender': 1.35, 'height': 164.4, 'weight': 74.2,
        'ap_hi': 126.2, 'ap_lo': 81.5, 'cholesterol': 1.37, 'gluc': 1.23,
        'smoke': 0.088, 'alco': 0.054, 'active': 0.80,
        'bmi': 27.4, 'pulse_pressure': 44.7, 'map': 96.5,
        'hypertension': 0.48, 'obese': 0.26, 'age_group': 1.6,
    }
    POP_STDS = {
        'age': 7.1, 'gender': 0.48, 'height': 8.8, 'weight': 14.4,
        'ap_hi': 17.2, 'ap_lo': 10.8, 'cholesterol': 0.68, 'gluc': 0.57,
        'smoke': 0.28, 'alco': 0.23, 'active': 0.40,
        'bmi': 5.4, 'pulse_pressure': 13.1, 'map': 11.2,
        'hypertension': 0.50, 'obese': 0.44, 'age_group': 0.84,
    }

    contributions = []
    for i, feat in enumerate(FEATURES):
        val  = eng[feat]
        mean = POP_MEANS.get(feat, 0)
        std  = POP_STDS.get(feat, 1) or 1
        z    = (val - mean) / std
        contrib = float(importances[i] * z)

        contributions.append({
            'feature':      feat,
            'label':        FEATURE_LABELS[feat],
            'value':        val,
            'contribution': round(contrib, 4),
            'direction':    'risk' if contrib > 0 else 'protective',
        })

    contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
    return contributions[:10]

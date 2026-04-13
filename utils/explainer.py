"""
explainer.py
Two responsibilities:
  1. Format feature contributions into human-readable explanations
  2. Generate personalised follow-up recommendations based on risk + flagged features

FIXES:
  - BUG: BMI 'high' template had an f-string inside a .format() string:
      "{'overweight' if val < 30 else 'obese'}"
    This is invalid — .format() cannot evaluate Python expressions.
    FIX: use a plain function call instead to compute the category string.
"""

# ─────────────────────────────────────────────────────────────
# 1.  EXPLANATION TEXTS
# ─────────────────────────────────────────────────────────────

def _bmi_category(val: float) -> str:
    """Return BMI category label."""
    if val < 18.5:
        return 'underweight'
    elif val < 25:
        return 'healthy weight'
    elif val < 30:
        return 'overweight'
    else:
        return 'obese'


_EXPLAIN = {
    'ap_hi': {
        'high': (
            "Your systolic blood pressure ({val} mmHg) is above the healthy range (90–120 mmHg). "
            "Elevated systolic pressure means your heart is pumping harder than ideal, "
            "which stresses artery walls over time."
        ),
        'low': "Your systolic BP ({val} mmHg) is within or below the normal range — this is a positive sign.",
    },
    'ap_lo': {
        'high': (
            "Your diastolic blood pressure ({val} mmHg) is elevated (normal: 60–80 mmHg). "
            "This represents the pressure in your arteries between beats."
        ),
        'low': "Your diastolic BP ({val} mmHg) looks healthy.",
    },
    'bmi': {
        # ✅ FIX: removed broken f-string-inside-format expression;
        # _bmi_category() is called separately and injected as {cat}
        'high': (
            "Your BMI of {val} falls in the {cat} range. "
            "Higher BMI increases strain on the cardiovascular system."
        ),
        'low': "Your BMI of {val} is within the healthy range (18.5–24.9).",
    },
    'pulse_pressure': {
        'high': (
            "Your pulse pressure ({val} mmHg) is above the ideal range (30–50 mmHg). "
            "A wide pulse pressure can indicate arterial stiffness."
        ),
        'low': "Your pulse pressure ({val} mmHg) is within a healthy range.",
    },
    'cholesterol': {
        'high': (
            "Your cholesterol level is recorded as above normal. "
            "High LDL cholesterol contributes to arterial plaque buildup."
        ),
        'low': "Your cholesterol appears to be at a normal level.",
    },
    'gluc': {
        'high': (
            "Your glucose level is above normal. Persistent high blood sugar "
            "damages blood vessels and raises cardiovascular risk."
        ),
        'low': "Your glucose level appears normal.",
    },
    'smoke': {
        'high': (
            "You are a smoker. Smoking is one of the strongest modifiable risk factors "
            "for heart disease — it damages vessel walls and reduces oxygen delivery."
        ),
        'low': "You are a non-smoker, which is a significant protective factor.",
    },
    'active': {
        'high': "You are physically active, which is a strong protective factor for heart health.",
        'low': (
            "Physical inactivity increases cardiovascular risk. Even moderate exercise "
            "(30 min/day, 5 days/week) significantly reduces risk."
        ),
    },
    'age': {
        'high': "Age ({val} years) is a non-modifiable risk factor. Risk increases naturally with age.",
        'low':  "At {val} years old, age is less of a contributing factor currently.",
    },
    'hypertension': {
        'high': (
            "Your blood pressure readings meet the clinical threshold for hypertension. "
            "This is a major independent risk factor for heart disease and stroke."
        ),
        'low': "No hypertension detected based on your blood pressure readings.",
    },
    'obese': {
        'high': (
            "Your BMI classifies you as obese (≥30). Obesity significantly increases "
            "the workload on your heart and raises inflammation markers."
        ),
        'low': "Your weight does not fall in the obese range — good.",
    },
    'map': {
        'high': (
            "Your mean arterial pressure ({val} mmHg) is above the healthy range (70–100 mmHg). "
            "MAP reflects average pressure throughout the cardiac cycle."
        ),
        'low': "Your mean arterial pressure ({val} mmHg) is within a normal range.",
    },
}


def explain_contributions(contributions: list) -> list:
    """
    Takes the contributions list from predictor.predict() and returns
    an enriched list with human-readable explanation text added.
    """
    enriched = []
    for item in contributions:
        feat      = item['feature']
        val       = item['value']
        direction = item['direction']

        explanation = ''
        if feat in _EXPLAIN:
            key           = 'high' if direction == 'risk' else 'low'
            text_template = _EXPLAIN[feat].get(key, '')
            if text_template:
                try:
                    # ✅ FIX: pass 'cat' kwarg for BMI template
                    explanation = text_template.format(val=val, cat=_bmi_category(val))
                except Exception:
                    explanation = text_template

        enriched.append({**item, 'explanation': explanation})

    return enriched


# ─────────────────────────────────────────────────────────────
# 2.  RECOMMENDATION ENGINE
# ─────────────────────────────────────────────────────────────

def get_recommendations(result: dict) -> dict:
    """
    Generates personalised recommendations based on:
    - risk_label (Low / Moderate / High)
    - flagged features (outside healthy range)
    - lifestyle flags (smoke, alco, active)
    """
    eng        = result['engineered']
    label      = result['risk_label']
    flagged_fs = {f['feature'] for f in result['flagged']}

    actions = []

    # ── Lifestyle ──
    if eng['smoke']:
        actions.append({
            'category': 'Lifestyle',
            'title':    'Quit smoking',
            'detail':   (
                'Smoking cessation is the single most impactful change you can make. '
                'Risk drops significantly within 1 year of quitting.'
            ),
            'priority': 'high',
        })
    if eng['alco']:
        actions.append({
            'category': 'Lifestyle',
            'title':    'Reduce alcohol intake',
            'detail':   (
                'Limit to ≤1 drink/day for women, ≤2 for men. '
                'Excess alcohol raises blood pressure and triglycerides.'
            ),
            'priority': 'medium',
        })
    if not eng['active']:
        actions.append({
            'category': 'Lifestyle',
            'title':    'Increase physical activity',
            'detail':   (
                'Target 150 min/week of moderate aerobic exercise (brisk walking, cycling, swimming). '
                'Start with 10–15 min/day if currently inactive.'
            ),
            'priority': 'high',
        })
    else:
        actions.append({
            'category': 'Lifestyle',
            'title':    'Maintain physical activity',
            'detail':   (
                'Keep up your current activity level. Consider adding resistance training '
                '2×/week for additional cardiovascular benefit.'
            ),
            'priority': 'low',
        })

    # ── Blood pressure ──
    if 'ap_hi' in flagged_fs or 'ap_lo' in flagged_fs:
        actions.append({
            'category': 'Blood pressure',
            'title':    'Monitor and manage blood pressure',
            'detail':   (
                f"Your BP reading ({eng['ap_hi']}/{eng['ap_lo']} mmHg) is above normal. "
                "Reduce sodium intake (<2g/day), avoid caffeine before readings, "
                "and consult a doctor about medication if lifestyle changes are insufficient."
            ),
            'priority': 'high',
        })

    # ── Weight / BMI ──
    if 'bmi' in flagged_fs:
        target_weight = round(24.9 * (eng['height'] / 100) ** 2, 1)
        diff = round(eng['weight'] - target_weight, 1)
        actions.append({
            'category': 'Weight',
            'title':    'Work towards a healthier weight',
            'detail':   (
                f"Your current BMI is {eng['bmi']}. Losing ~{diff} kg would bring you "
                "into the healthy range. Focus on a calorie-controlled diet rich in "
                "vegetables, whole grains, and lean protein."
            ),
            'priority': 'medium',
        })

    # ── Cholesterol ──
    if eng['cholesterol'] > 1:
        actions.append({
            'category': 'Diet',
            'title':    'Improve cholesterol through diet',
            'detail':   (
                'Reduce saturated fats (red meat, full-fat dairy). Increase soluble fibre '
                '(oats, lentils, apples). Consider omega-3 rich foods (fish, flaxseed).'
            ),
            'priority': 'medium' if eng['cholesterol'] == 2 else 'high',
        })

    # ── Glucose ──
    if eng['gluc'] > 1:
        actions.append({
            'category': 'Blood sugar',
            'title':    'Address elevated blood glucose',
            'detail':   (
                'Reduce refined carbohydrates and sugary drinks. Regular exercise significantly '
                'improves insulin sensitivity. Request an HbA1c test from your doctor.'
            ),
            'priority': 'high',
        })

    # ── Mental health / stress ──
    actions.append({
        'category': 'Wellbeing',
        'title':    'Manage stress',
        'detail':   (
            'Chronic stress raises cortisol which elevates BP and promotes inflammation. '
            'Consider mindfulness, adequate sleep (7–9 hrs), and social connection.'
        ),
        'priority': 'low',
    })

    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    actions.sort(key=lambda x: priority_order.get(x['priority'], 3))

    if label == 'High':
        urgency       = 'urgent'
        urgency_color = '#E24B4A'
        message       = 'Your results indicate a high cardiovascular risk. Please consult a doctor soon.'
        followup = {
            'type':      'Medical consultation',
            'timeframe': 'Within 2 weeks',
            'tests':     [
                'Full lipid panel', 'HbA1c (blood sugar)', 'ECG / resting heart rate',
                'Kidney function (eGFR)', 'Blood pressure monitoring at home',
            ],
        }
    elif label == 'Moderate':
        urgency       = 'soon'
        urgency_color = '#EF9F27'
        message       = 'Your risk is moderate. Lifestyle changes now can significantly reduce your long-term risk.'
        followup = {
            'type':      'Routine check-up',
            'timeframe': 'Within 1–3 months',
            'tests':     ['Cholesterol panel', 'Fasting glucose', 'Blood pressure check'],
        }
    else:
        urgency       = 'routine'
        urgency_color = '#1D9E75'
        message       = 'Your cardiovascular risk appears low. Keep up the healthy habits!'
        followup = {
            'type':      'Annual check-up',
            'timeframe': 'In 12 months',
            'tests':     ['Annual physical', 'Cholesterol check', 'Blood pressure screening'],
        }

    return {
        'urgency':       urgency,
        'urgency_color': urgency_color,
        'message':       message,
        'actions':       actions,
        'followup':      followup,
    }


def get_daily_tips(eng: dict) -> list:
    """Returns 3–5 bite-sized daily monitoring tips personalised to the user."""
    tips = []

    if eng['ap_hi'] >= 130 or eng['ap_lo'] >= 80:
        tips.append({
            'icon':  '🩺',
            'title': 'Measure BP daily',
            'tip':   (
                'Check at the same time each morning, before eating or taking medication. '
                'Log both readings.'
            ),
        })

    if eng['bmi'] >= 25:
        tips.append({
            'icon':  '⚖️',
            'title': 'Weekly weigh-in',
            'tip':   'Weigh yourself once a week, same day, same time. Track the trend, not the daily noise.',
        })

    if not eng['active']:
        tips.append({
            'icon':  '🚶',
            'title': '10-minute walks',
            'tip':   (
                'Three 10-minute walks spread through the day count as 30 minutes. '
                'Start small and build up.'
            ),
        })

    if eng['smoke']:
        tips.append({
            'icon':  '🚭',
            'title': 'Track smoke-free hours',
            'tip':   (
                'Use an app to track hours smoke-free. Even 24 hours without smoking '
                'starts reducing heart rate and blood pressure.'
            ),
        })

    tips.append({
        'icon':  '💧',
        'title': 'Stay hydrated',
        'tip':   'Drink 6–8 glasses of water daily. Dehydration causes temporary BP spikes.',
    })

    tips.append({
        'icon':  '😴',
        'title': 'Prioritise sleep',
        'tip':   'Aim for 7–9 hours. Poor sleep is independently linked to higher cardiovascular risk.',
    })

    return tips[:5]

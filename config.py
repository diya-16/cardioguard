"""
config.py
App-wide constants, theme colours, and feature reference data.
Import this everywhere instead of hardcoding values.
"""

APP_TITLE    = "CardioGuard"
APP_ICON     = "❤️"
APP_VERSION  = "1.0.0"

# ── Risk colours ──────────────────────────────────────────────
RISK_COLORS = {
    'Low':      '#1D9E75',
    'Moderate': '#EF9F27',
    'High':     '#E24B4A',
}

RISK_BG = {
    'Low':      '#E1F5EE',
    'Moderate': '#FAEEDA',
    'High':     '#FCEBEB',
}

# ── Plotly / chart theme ──────────────────────────────────────
CHART_THEME = {
    'bg':          '#0f1117',
    'panel':       '#1a1d27',
    'text':        '#e8eaf0',
    'muted':       '#8b8fa8',
    'grid':        '#2a2d3a',
    'positive':    '#1D9E75',
    'warning':     '#EF9F27',
    'danger':      '#E24B4A',
    'info':        '#378ADD',
    'line_colors': ['#4d9de0', '#7ec8a4', '#e05c5c', '#f4a261', '#c77dff'],
}

# ── Healthy reference ranges (for display) ────────────────────
HEALTHY_RANGES = {
    'Systolic BP':   {'range': '90–120 mmHg', 'low': 90,  'high': 120},
    'Diastolic BP':  {'range': '60–80 mmHg',  'low': 60,  'high': 80},
    'BMI':           {'range': '18.5–24.9',   'low': 18.5,'high': 24.9},
    'Pulse pressure':{'range': '30–50 mmHg',  'low': 30,  'high': 50},
    'MAP':           {'range': '70–100 mmHg', 'low': 70,  'high': 100},
}

# ── Cholesterol labels ────────────────────────────────────────
CHOL_LABELS = {1: 'Normal', 2: 'Above normal', 3: 'Well above normal'}
GLUC_LABELS = {1: 'Normal', 2: 'Above normal', 3: 'Well above normal'}

# ── Sidebar input defaults ────────────────────────────────────
INPUT_DEFAULTS = {
    'age':         45,
    'gender':      1,
    'height':      165,
    'weight':      70.0,
    'ap_hi':       120,
    'ap_lo':       80,
    'cholesterol': 1,
    'gluc':        1,
    'smoke':       0,
    'alco':        0,
    'active':      1,
}

# ── Page names (used in st.page_link etc) ────────────────────
PAGES = {
    'predict':  'pages/01_predict.py',
    'history':  'pages/02_history.py',
    'followup': 'pages/03_followup.py',
}

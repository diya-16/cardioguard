"""
pages/01_predict.py
Risk Assessment page — shows risk score, feature contribution chart,
plain-English explanations, and flagged vitals.

IMPROVEMENTS over original stub:
  - Gauge-style risk meter using Plotly indicator
  - Horizontal bar chart of feature contributions (risk vs protective)
  - Expandable explanation cards for each contributing factor
  - Flagged-vitals panel with healthy range comparison
  - Confidence interval display
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import APP_TITLE, APP_ICON, CHART_THEME, HEALTHY_RANGES
from utils.explainer import explain_contributions

st.set_page_config(page_title=f"Risk Assessment · {APP_TITLE}", page_icon=APP_ICON, layout="wide")

T = CHART_THEME

# ── Guard: must run from home page first ─────────────────────
if 'result' not in st.session_state:
    st.info("👈  Please enter your vitals in the sidebar on the Home page and click **Analyse Risk**.")
    st.stop()

result    = st.session_state['result']
raw       = st.session_state['raw']
user_name = st.session_state.get('user_name', 'User')

score  = result['risk_score']
label  = result['risk_label']
color  = result['risk_color']
prob   = result['probability']
eng    = result['engineered']
contribs = explain_contributions(result['contributions'])
flagged  = result['flagged']

# ── Header ────────────────────────────────────────────────────
st.markdown(f"## 🔍 Risk Assessment — {user_name}")
st.divider()

# ── Row 1: Gauge + key metrics ────────────────────────────────
col_gauge, col_metrics = st.columns([1, 2], gap="large")

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode    = "gauge+number",
        value   = score,
        number  = {'suffix': '%', 'font': {'size': 42, 'color': color}},
        title   = {'text': f'<b>{label} Risk</b>', 'font': {'size': 16, 'color': T['muted']}},
        gauge   = {
            'axis': {'range': [0, 100], 'tickcolor': T['muted'], 'tickfont': {'color': T['muted']}},
            'bar':  {'color': color, 'thickness': 0.25},
            'bgcolor': T['panel'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, 35],  'color': 'rgba(29, 158, 117, 0.13)'},
                {'range': [35, 60], 'color': 'rgba(239, 159, 39, 0.13)'},
                {'range': [60, 100],'color': 'rgba(226, 75, 74, 0.13)'},
            ],
            'threshold': {
                'line': {'color': color, 'width': 3},
                'thickness': 0.8,
                'value': score,
            },
        },
    ))
    fig_gauge.update_layout(
        height=280, margin=dict(t=30, b=10, l=30, r=30),
        paper_bgcolor=T['panel'], font_color=T['text'],
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_metrics:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Risk Score",    f"{score}%")
        st.metric("Systolic BP",   f"{eng['ap_hi']} mmHg",
                  delta=f"{eng['ap_hi']-120:+d} vs normal" if eng['ap_hi'] != 120 else None,
                  delta_color="inverse")
    with m2:
        st.metric("Probability",   f"{prob*100:.1f}%")
        st.metric("Diastolic BP",  f"{eng['ap_lo']} mmHg",
                  delta=f"{eng['ap_lo']-80:+d} vs normal" if eng['ap_lo'] != 80 else None,
                  delta_color="inverse")
    with m3:
        st.metric("BMI",           f"{eng['bmi']}")
        st.metric("Pulse Pressure",f"{eng['pulse_pressure']} mmHg")

    # Confidence bar
    st.markdown("<br>", unsafe_allow_html=True)
    conf_pct = int(max(prob, 1 - prob) * 100)
    st.markdown(f"""
    <div style='color:{T["muted"]}; font-size:0.82rem; margin-bottom:4px;'>
        Model confidence: <b style='color:{T["text"]}'>{conf_pct}%</b>
    </div>
    <div style='background:{T["grid"]}; border-radius:6px; height:8px; overflow:hidden;'>
        <div style='background:{color}; width:{conf_pct}%; height:100%; border-radius:6px;'></div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── Row 2: Feature contributions chart ───────────────────────
st.markdown("### 📊 What's driving your risk?")

df_c = pd.DataFrame(contribs)
df_c['abs'] = df_c['contribution'].abs()
df_c = df_c.sort_values('abs')

bar_colors = [T['danger'] if d == 'risk' else T['positive']
              for d in df_c['direction']]

fig_bar = go.Figure(go.Bar(
    x          = df_c['contribution'],
    y          = df_c['label'],
    orientation= 'h',
    marker_color= bar_colors,
    text       = df_c['contribution'].apply(lambda v: f"{'+' if v>0 else ''}{v:.3f}"),
    textposition='outside',
    textfont   = {'color': T['text'], 'size': 10},
))
fig_bar.add_vline(x=0, line_color=T['muted'], line_width=1)
fig_bar.update_layout(
    height      = 380,
    margin      = dict(t=10, b=10, l=10, r=80),
    paper_bgcolor= T['bg'], plot_bgcolor = T['panel'],
    font_color  = T['text'],
    xaxis       = dict(gridcolor=T['grid'], zerolinecolor=T['muted'], title='Contribution score'),
    yaxis       = dict(gridcolor=T['grid']),
    showlegend  = False,
)
st.plotly_chart(fig_bar, use_container_width=True)

st.caption("🟥 Red bars increase risk above average · 🟩 Green bars are protective relative to average")

st.divider()

# ── Row 3: Explanation cards ──────────────────────────────────
st.markdown("### 💬 Factor explanations")

explained = [c for c in contribs if c.get('explanation')]
cols = st.columns(2)
for i, item in enumerate(explained[:8]):
    icon  = "⚠️" if item['direction'] == 'risk' else "✅"
    bdr   = T['danger'] if item['direction'] == 'risk' else T['positive']
    with cols[i % 2]:
        with st.expander(f"{icon} {item['label']}  (score: {item['contribution']:+.3f})", expanded=i < 2):
            st.markdown(item['explanation'] or "_No explanation available._")

st.divider()

# ── Row 4: Flagged vitals ─────────────────────────────────────
if flagged:
    st.markdown("### 🚩 Vitals outside healthy range")
    for f in flagged:
        st.warning(f"**{f['label']}**: {f['value']}  ·  Healthy range: {f['normal']}")
else:
    st.success("✅ All measured vitals are within healthy reference ranges.")

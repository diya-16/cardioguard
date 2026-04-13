"""
pages/02_history.py
Health History & Trends page.

IMPROVEMENTS:
  - Real multi-line trend charts for BP, BMI, risk score
  - Stats summary (total checks, avg risk, trend direction)
  - Alert banner when recent trend is worsening
  - Data table with colour-coded risk labels
  - Delete history button with confirmation
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from config import APP_TITLE, APP_ICON, CHART_THEME, RISK_COLORS
from utils.db import get_history, get_trend_data, get_stats, delete_history

st.set_page_config(page_title=f"My History · {APP_TITLE}", page_icon=APP_ICON, layout="wide")

T = CHART_THEME
user_name = st.session_state.get('user_name', 'User')

st.markdown(f"## 📈 My Health History — {user_name}")
st.divider()

df   = get_history(user_name=user_name)
trend = get_trend_data(user_name=user_name)
stats = get_stats(user_name=user_name)

if df.empty:
    st.info("No history yet. Run an analysis from the Home page and tick **Save to history**.")
    st.stop()

# ── Stats row ─────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
trend_arrow = {'improving': '📉', 'worsening': '📈', 'stable': '➡️'}.get(stats['trend'], '—')
with c1:
    st.metric("Total checks",   stats['total_checks'])
with c2:
    st.metric("Avg risk score", f"{stats['avg_risk']}%" if stats['avg_risk'] else "—")
with c3:
    st.metric("Trend",          f"{trend_arrow} {stats['trend'].capitalize()}" if stats['trend'] else "—")
with c4:
    st.metric("Last check",     stats['last_check'] or "—")

# Alert if worsening
if stats['trend'] == 'worsening':
    st.error("⚠️ Your cardiovascular risk has been **trending upward** across recent checks. "
             "Consider reviewing the Recommendations page and consulting your doctor.")
elif stats['trend'] == 'improving':
    st.success("🎉 Your cardiovascular risk has been **improving** — keep up the great work!")

st.divider()

# ── Trend charts ──────────────────────────────────────────────
st.markdown("### 📊 Trends over time")

if len(trend) >= 2:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Risk Score (%)', 'Blood Pressure (mmHg)', 'BMI', 'Pulse Pressure (mmHg)'],
        vertical_spacing=0.18, horizontal_spacing=0.1,
    )

    def line(fig, x, y, name, color, row, col, fill=False):
        fig.add_trace(go.Scatter(
            x=x, y=y, name=name, mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=6),
            fill='tozeroy' if fill else None,
            fillcolor=color.replace(')', ',0.08)').replace('rgb', 'rgba') if fill else None,
        ), row=row, col=col)

    line(fig, trend['timestamp'], trend['risk_score'],    'Risk %',       T['danger'],   1, 1, fill=True)
    line(fig, trend['timestamp'], trend['ap_hi'],         'Systolic',     T['danger'],   1, 2)
    line(fig, trend['timestamp'], trend['ap_lo'],         'Diastolic',    T['info'],     1, 2)
    line(fig, trend['timestamp'], trend['bmi'],           'BMI',          T['warning'],  2, 1, fill=True)
    line(fig, trend['timestamp'], trend['pulse_pressure'],'Pulse Pressure',T['line_colors'][4], 2, 2)

    # Reference lines
    fig.add_hline(y=35,  line_dash='dot', line_color=T['positive'], line_width=1, row=1, col=1,
                  annotation_text='Low threshold', annotation_font_color=T['muted'])
    fig.add_hline(y=60,  line_dash='dot', line_color=T['danger'],   line_width=1, row=1, col=1,
                  annotation_text='High threshold', annotation_font_color=T['muted'])
    fig.add_hline(y=120, line_dash='dot', line_color=T['muted'],    line_width=1, row=1, col=2)
    fig.add_hline(y=80,  line_dash='dot', line_color=T['muted'],    line_width=1, row=1, col=2)
    fig.add_hline(y=24.9,line_dash='dot', line_color=T['positive'], line_width=1, row=2, col=1)
    fig.add_hline(y=30,  line_dash='dot', line_color=T['danger'],   line_width=1, row=2, col=1)

    fig.update_layout(
        height=500,
        paper_bgcolor=T['bg'], plot_bgcolor=T['panel'],
        font_color=T['text'],
        legend=dict(bgcolor=T['panel'], bordercolor=T['grid']),
        margin=dict(t=40, b=20),
    )
    for i in fig['layout']['annotations']:
        i['font'] = dict(color=T['muted'], size=11)

    fig.update_xaxes(gridcolor=T['grid'], linecolor=T['grid'])
    fig.update_yaxes(gridcolor=T['grid'], linecolor=T['grid'])

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Need at least 2 saved checks to display trend charts.")

st.divider()

# ── History table ─────────────────────────────────────────────
st.markdown("### 🗂️ All records")

display_cols = ['timestamp', 'risk_score', 'risk_label', 'ap_hi', 'ap_lo', 'bmi', 'weight']
display_cols = [c for c in display_cols if c in df.columns]
df_show = df[display_cols].copy()
df_show['timestamp'] = df_show['timestamp'].dt.strftime('%d %b %Y %H:%M')
df_show.columns      = [c.replace('_', ' ').title() for c in df_show.columns]
df_show.index        = range(1, len(df_show) + 1)

st.dataframe(df_show, use_container_width=True)

st.divider()

# ── Delete history ────────────────────────────────────────────
with st.expander("⚠️ Danger zone"):
    st.warning("Deleting your history is **permanent** and cannot be undone.")
    confirm = st.checkbox("I understand, delete my history")
    if confirm and st.button("🗑️ Delete all my records", type="primary"):
        delete_history(user_name=user_name)
        st.success("History deleted.")
        st.rerun()

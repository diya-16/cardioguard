"""
pages/03_followup.py
Recommendations & PDF Report page.

IMPROVEMENTS:
  - Urgency banner with colour coding
  - Action cards grouped by category with priority colouring
  - Follow-up tests checklist
  - Daily monitoring tips
  - PDF report generation and download
"""

import streamlit as st
from io import BytesIO
from datetime import datetime
from config import APP_TITLE, APP_ICON, CHART_THEME
from utils.explainer import get_recommendations, get_daily_tips

st.set_page_config(page_title=f"Recommendations · {APP_TITLE}", page_icon=APP_ICON, layout="wide")

T = CHART_THEME

if 'result' not in st.session_state:
    st.info("👈  Please run an analysis from the Home page first.")
    st.stop()

result    = st.session_state['result']
user_name = st.session_state.get('user_name', 'User')
eng       = result['engineered']

recs = get_recommendations(result)
tips = get_daily_tips(eng)

# ── Header ────────────────────────────────────────────────────
st.markdown(f"## 📋 Recommendations — {user_name}")
st.divider()

# ── Urgency banner ────────────────────────────────────────────
uc = recs['urgency_color']
st.markdown(f"""
<div style='padding:1rem 1.4rem; background:{uc}18; border-left:4px solid {uc};
            border-radius:8px; margin-bottom:1.5rem;'>
    <div style='font-size:1.05rem; font-weight:700; color:{uc};'>
        {recs['urgency'].capitalize()} — {recs['followup']['type']}
    </div>
    <div style='color:{T["text"]}; margin-top:4px;'>{recs['message']}</div>
    <div style='color:{T["muted"]}; font-size:0.85rem; margin-top:6px;'>
        Suggested timeline: <b style='color:{T["text"]}'>{recs['followup']['timeframe']}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Action items ──────────────────────────────────────────────
st.markdown("### ✅ Action plan")

priority_icons  = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
priority_colors = {'high': T['danger'], 'medium': T['warning'], 'low': T['positive']}

for action in recs['actions']:
    p    = action['priority']
    icon = priority_icons.get(p, '⚪')
    bc   = priority_colors.get(p, T['muted'])
    with st.expander(f"{icon} [{action['category']}] {action['title']}", expanded=(p == 'high')):
        st.markdown(action['detail'])
        st.caption(f"Priority: **{p.capitalize()}**")

st.divider()

# ── Follow-up tests ───────────────────────────────────────────
st.markdown("### 🧪 Recommended tests")
for test in recs['followup']['tests']:
    st.checkbox(test, key=f"test_{test}")

st.divider()

# ── Daily tips ────────────────────────────────────────────────
st.markdown("### 💡 Daily monitoring tips")
cols = st.columns(len(tips))
for col, tip in zip(cols, tips):
    with col:
        st.markdown(f"""
        <div style='background:{T["panel"]}; border:1px solid {T["grid"]}; border-radius:10px;
                    padding:1rem; text-align:center; height:100%;'>
            <div style='font-size:2rem;'>{tip['icon']}</div>
            <div style='font-weight:600; color:{T["text"]}; margin:6px 0 4px;'>{tip['title']}</div>
            <div style='color:{T["muted"]}; font-size:0.82rem;'>{tip['tip']}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── PDF Report ────────────────────────────────────────────────
st.markdown("### 📄 Download report")
st.markdown("Generate a PDF summary you can bring to your doctor.")

if st.button("🖨️ Generate PDF Report", type="primary"):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('title', parent=styles['Title'],
                                     fontSize=20, textColor=colors.HexColor('#E24B4A'))
        h2_style    = ParagraphStyle('h2', parent=styles['Heading2'],
                                     textColor=colors.HexColor('#378ADD'))
        body_style  = styles['Normal']
        muted_style = ParagraphStyle('muted', parent=styles['Normal'],
                                     textColor=colors.grey, fontSize=9)

        story = []

        # Title
        story.append(Paragraph("❤️ CardioGuard — Health Report", title_style))
        story.append(Paragraph(
            f"Prepared for: <b>{user_name}</b> &nbsp;|&nbsp; {datetime.now().strftime('%d %B %Y, %H:%M')}",
            muted_style))
        story.append(Spacer(1, 0.4*cm))
        story.append(HRFlowable(width="100%", color=colors.HexColor('#2a2d3a')))
        story.append(Spacer(1, 0.4*cm))

        # Risk summary
        story.append(Paragraph("Risk Summary", h2_style))
        risk_data = [
            ['Risk Score', 'Risk Level', 'Probability', 'Systolic BP', 'Diastolic BP', 'BMI'],
            [
                f"{result['risk_score']}%",
                result['risk_label'],
                f"{result['probability']*100:.1f}%",
                f"{eng['ap_hi']} mmHg",
                f"{eng['ap_lo']} mmHg",
                str(eng['bmi']),
            ],
        ]
        risk_color = colors.HexColor(result['risk_color'])
        tbl = Table(risk_data, colWidths=[2.8*cm]*6)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1d27')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.HexColor('#8b8fa8')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#0f1117')),
            ('TEXTCOLOR',  (0,1), (-1,1), colors.white),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#0f1117')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.HexColor('#2a2d3a')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.5*cm))

        # Recommendations
        story.append(Paragraph("Recommended Actions", h2_style))
        for action in recs['actions']:
            p_label = action['priority'].upper()
            story.append(Paragraph(
                f"<b>[{p_label}] {action['category']}: {action['title']}</b>",
                body_style))
            story.append(Paragraph(action['detail'], body_style))
            story.append(Spacer(1, 0.25*cm))

        story.append(Spacer(1, 0.3*cm))

        # Follow-up
        story.append(Paragraph("Follow-up Tests", h2_style))
        story.append(Paragraph(
            f"<b>Type:</b> {recs['followup']['type']}  ·  "
            f"<b>Timeline:</b> {recs['followup']['timeframe']}", body_style))
        story.append(Spacer(1, 0.2*cm))
        for test in recs['followup']['tests']:
            story.append(Paragraph(f"☐  {test}", body_style))

        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", color=colors.HexColor('#2a2d3a')))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "This report is for informational purposes only and does not constitute medical advice. "
            "Always consult a qualified healthcare professional.",
            muted_style))

        doc.build(story)
        buf.seek(0)

        st.download_button(
            label     = "⬇️ Download PDF",
            data      = buf,
            file_name = f"cardioguard_report_{user_name.lower().replace(' ', '_')}.pdf",
            mime      = "application/pdf",
        )
        st.success("Report ready! Click the button above to download.")

    except ImportError:
        st.error("ReportLab is not installed. Run: `pip install reportlab`")
    except Exception as e:
        st.error(f"Could not generate PDF: {e}")

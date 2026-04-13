"""
app.py
CardioGuard — entry point.
Run with: streamlit run app.py
"""

import streamlit as st
from config import APP_TITLE, APP_ICON, INPUT_DEFAULTS, CHOL_LABELS, GLUC_LABELS
from utils.predictor import predict
from utils.db import save_prediction, init_db

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB on startup ────────────────────────────────────────
init_db()

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Sidebar width */
    [data-testid="stSidebar"] { min-width: 300px; max-width: 300px; }

    /* Remove default top padding */
    .block-container { padding-top: 1.5rem; }

    /* Risk badge */
    .risk-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
    }

    /* Metric card */
    .metric-card {
        background: #1a1d27;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        border: 1px solid #2a2d3a;
    }

    /* Section headers */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #8b8fa8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.5rem;
    }

    /* Action card colours by priority */
    .action-high   { border-left: 3px solid #E24B4A; padding-left: 10px; }
    .action-medium { border-left: 3px solid #EF9F27; padding-left: 10px; }
    .action-low    { border-left: 3px solid #1D9E75; padding-left: 10px; }

    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar — shared across all pages ─────────────────────────
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")
    st.markdown("*Personal Cardiac Risk Monitor*")
    st.divider()

    # User name
    user_name = st.text_input("Your name", value="User", key="user_name")

    st.divider()
    st.markdown("### Enter Your Vitals")

    age    = st.slider("Age (years)",     min_value=20, max_value=80,
                       value=INPUT_DEFAULTS['age'])
    gender = st.selectbox("Gender",       options=[1, 2],
                          format_func=lambda x: "Female" if x == 1 else "Male",
                          index=0)
    height = st.number_input("Height (cm)", min_value=130, max_value=220,
                             value=INPUT_DEFAULTS['height'])
    weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0,
                             value=INPUT_DEFAULTS['weight'], step=0.5)

    st.markdown("**Blood Pressure**")
    col1, col2 = st.columns(2)
    with col1:
        ap_hi = st.number_input("Systolic",  min_value=80,  max_value=250,
                                value=INPUT_DEFAULTS['ap_hi'],  key="ap_hi")
    with col2:
        ap_lo = st.number_input("Diastolic", min_value=40,  max_value=200,
                                value=INPUT_DEFAULTS['ap_lo'],  key="ap_lo")

    cholesterol = st.selectbox("Cholesterol", options=[1, 2, 3],
                               format_func=lambda x: CHOL_LABELS[x], index=0)
    gluc        = st.selectbox("Glucose",     options=[1, 2, 3],
                               format_func=lambda x: GLUC_LABELS[x], index=0)

    st.markdown("**Lifestyle**")
    smoke  = st.checkbox("Smoker",             value=bool(INPUT_DEFAULTS['smoke']))
    alco   = st.checkbox("Alcohol use",        value=bool(INPUT_DEFAULTS['alco']))
    active = st.checkbox("Physically active",  value=bool(INPUT_DEFAULTS['active']))

    st.divider()

    # ── Run prediction ─────────────────────────────────────────
    run = st.button("🔍 Analyse Risk", use_container_width=True, type="primary")
    save = st.checkbox("Save to history", value=True)

    if run:
        raw = {
            'age': age, 'gender': gender, 'height': height, 'weight': weight,
            'ap_hi': ap_hi, 'ap_lo': ap_lo, 'cholesterol': cholesterol,
            'gluc': gluc, 'smoke': int(smoke), 'alco': int(alco), 'active': int(active),
        }
        with st.spinner("Analysing..."):
            result = predict(raw)

        st.session_state['result']    = result
        st.session_state['raw']       = raw
        

        if save:
            save_prediction(result, raw, user_name)
            st.session_state['saved'] = True
        else:
            st.session_state['saved'] = False

        # Show quick risk badge in sidebar
        label = result['risk_label']
        color = result['risk_color']
        score = result['risk_score']
        st.markdown(f"""
        <div style='text-align:center; margin-top:12px;'>
            <div style='font-size:2rem; font-weight:700; color:{color};'>{score}%</div>
            <span class='risk-badge' style='background:{color}22; color:{color};'>{label} Risk</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Navigation ────────────────────────────────────────────
    st.markdown("### Navigation")
    st.page_link("app.py",               label="🏠 Home",            icon=None)
    st.page_link("pages/01_predict.py",  label="🔍 Risk Assessment", icon=None)
    st.page_link("pages/02_history.py",  label="📈 My History",      icon=None)
    st.page_link("pages/03_followup.py", label="📋 Recommendations", icon=None)


# ── Home page content ─────────────────────────────────────────
st.markdown(f"# {APP_ICON} {APP_TITLE}")
st.markdown("### Your personal cardiovascular risk monitor")
st.divider()

if 'result' not in st.session_state:
    # Welcome state
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='section-header'>Step 1</div>
            <h4>Enter your vitals</h4>
            <p style='color:#8b8fa8; font-size:0.9rem;'>
            Fill in your age, blood pressure, weight, and lifestyle details in the sidebar.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='section-header'>Step 2</div>
            <h4>Get your risk score</h4>
            <p style='color:#8b8fa8; font-size:0.9rem;'>
            Our Gradient Boosting model analyses 17 features and returns a 0–100 risk score
            with a full explanation of what's driving it.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='section-header'>Step 3</div>
            <h4>Track and act</h4>
            <p style='color:#8b8fa8; font-size:0.9rem;'>
            Save your results over time to monitor trends. Get personalised follow-up
            recommendations and download a PDF report for your doctor.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈  Enter your details in the sidebar and click **Analyse Risk** to get started.")

else:
    # Show summary of last result
    result = st.session_state['result']
    label  = result['risk_label']
    color  = result['risk_color']
    score  = result['risk_score']

    st.markdown(f"""
    <div style='padding:1.5rem; background:#1a1d27; border-radius:12px;
                border:1px solid #2a2d3a; margin-bottom:1.5rem;'>
        <div style='font-size:0.8rem; color:#8b8fa8; margin-bottom:4px;'>Current risk assessment</div>
        <div style='display:flex; align-items:baseline; gap:12px;'>
            <span style='font-size:3rem; font-weight:700; color:{color};'>{score}%</span>
            <span class='risk-badge' style='background:{color}22; color:{color};'>{label} Risk</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/01_predict.py", label="🔍 View full analysis & explanation")
    with col2:
        st.page_link("pages/02_history.py", label="📈 View my health trends")
    with col3:
        st.page_link("pages/03_followup.py", label="📋 View recommendations")

    if st.session_state.get('saved'):
        st.success("✅ Result saved to history.")

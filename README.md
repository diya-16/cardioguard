# ❤️ CardioGuard — Personal Cardiac Risk Monitor

A Streamlit dashboard for cardiovascular disease risk prediction, explanation, history tracking, and personalised recommendations.

**Best model: Gradient Boosting — ROC-AUC: 0.8021**

---

## 🐳 Run with Docker (Recommended)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed

### Quick start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/cardioguard.git
cd cardioguard

# 2. Build and run
docker compose up --build

# 3. Open in browser
# http://localhost:8501
```

To stop: `docker compose down`

---

## 🖥️ Run Locally (without Docker)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure

```
cardioguard/
├── app.py                  # Entry point + shared sidebar
├── config.py               # Constants and theme
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── models/
│   ├── best_model.pkl      # Trained Gradient Boosting model
│   └── scaler.pkl          # StandardScaler
├── pages/
│   ├── 01_predict.py       # Risk assessment + SHAP explanation
│   ├── 02_history.py       # Trend monitoring + alerts
│   └── 03_followup.py      # Recommendations + PDF report
├── utils/
│   ├── predictor.py        # Feature engineering + prediction
│   ├── explainer.py        # Explanation + recommendation engine
│   └── db.py               # SQLite history storage
└── data/
    └── pipeline_summary.json
```

---

## ✨ Features

- **Risk score** (0–100%) with confidence probability
- **Feature contribution chart** — shows which vitals drive your risk
- **Plain-English explanations** for each contributing factor
- **History tracking** — saves every assessment to SQLite
- **Trend charts** — BP, BMI, risk score over time with alerts
- **Personalised recommendations** — lifestyle, diet, medical follow-up
- **PDF report** — downloadable summary for your doctor

---

## 📊 Dataset

Trained on the [Cardiovascular Disease dataset](https://www.kaggle.com/datasets/sulianova/cardiovascular-disease-dataset) (70,000 records).

---

## ⚠️ Disclaimer

This tool is for informational and educational purposes only. It does not constitute medical advice.

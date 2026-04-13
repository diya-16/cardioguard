"""
=============================================================
  HEART DISEASE PREDICTION — FULL ML PIPELINE
  Dataset: Cardiovascular Disease (Kaggle - sulianova)
=============================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score,
                             classification_report, confusion_matrix, roc_curve)
from sklearn.inspection import permutation_importance
import joblib
import json
import os

os.makedirs('outputs', exist_ok=True)

print("=" * 60)
print("STEP 1: LOADING DATA")
print("=" * 60)
df = pd.read_csv('cardio_train.csv', sep=';')
print(f"Raw shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

print("\n" + "=" * 60)
print("STEP 2: PREPROCESSING & FEATURE ENGINEERING")
print("=" * 60)

df = df.drop(columns=['id'])

# Age: days → years
df['age'] = (df['age'] / 365.25).round(1)
print(f"Age converted from days to years. Range: {df['age'].min():.1f} – {df['age'].max():.1f}")

before = len(df)

# ✅ BUG FIX: Missing closing bracket ] on the blood pressure filter
# Original code had no ] after the ap_hi > ap_lo condition, causing SyntaxError
df = df[
    (df['ap_hi'] >= 80)  & (df['ap_hi'] <= 250) &
    (df['ap_lo'] >= 40)  & (df['ap_lo'] <= 200) &
    (df['ap_hi'] > df['ap_lo'])
]
df = df[
    (df['height'] >= 130) & (df['height'] <= 220) &
    (df['weight'] >= 30)  & (df['weight'] <= 180)
]
after = len(df)
print(f"Outliers removed: {before - after} rows ({(before-after)/before*100:.1f}%)")
print(f"Clean dataset: {df.shape}")

# --- Feature Engineering ---
df['bmi']            = (df['weight'] / ((df['height'] / 100) ** 2)).round(2)
df['pulse_pressure'] = df['ap_hi'] - df['ap_lo']
df['map']            = (df['ap_lo'] + (df['pulse_pressure'] / 3)).round(2)
df['hypertension']   = ((df['ap_hi'] >= 140) | (df['ap_lo'] >= 90)).astype(int)
df['obese']          = (df['bmi'] >= 30).astype(int)
df['age_group']      = pd.cut(df['age'],
    bins=[0, 40, 50, 60, 100],
    labels=[0, 1, 2, 3]
).astype(int)

print(f"\nFeatures after engineering: {list(df.columns)}")
print(f"Total features: {df.shape[1] - 1} (excluding target)")

# ─────────────────────────────────────────────
# 3. EDA PLOTS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: EXPLORATORY DATA ANALYSIS")
print("=" * 60)

DARK_BG   = '#0f1117'
PANEL_BG  = '#1a1d27'
TEXT      = '#e8eaf0'
MUTED     = '#8b8fa8'
C_POS     = '#e05c5c'
C_NEG     = '#4d9de0'
GRID_COL  = '#2a2d3a'

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor(DARK_BG)
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

def style_ax(ax, title):
    ax.set_facecolor(PANEL_BG)
    ax.set_title(title, color=TEXT, fontsize=11, fontweight='bold', pad=8)
    ax.tick_params(colors=MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COL)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.grid(axis='y', color=GRID_COL, linewidth=0.5, alpha=0.7)

ax1 = fig.add_subplot(gs[0, 0])
counts = df['cardio'].value_counts()
bars = ax1.bar(['No Disease', 'Disease'], counts.values,
               color=[C_NEG, C_POS], width=0.5, edgecolor=PANEL_BG)
for bar, count in zip(bars, counts.values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
             f'{count:,}\n({count/len(df)*100:.1f}%)',
             ha='center', va='bottom', color=TEXT, fontsize=9)
style_ax(ax1, 'Class Balance')

ax2 = fig.add_subplot(gs[0, 1])
for val, color, label in [(0, C_NEG, 'No Disease'), (1, C_POS, 'Disease')]:
    ax2.hist(df[df['cardio'] == val]['age'], bins=30, alpha=0.7,
             color=color, label=label, edgecolor=PANEL_BG)
ax2.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL_BG, edgecolor=GRID_COL)
style_ax(ax2, 'Age Distribution by Class')
ax2.set_xlabel('Age (years)')

ax3 = fig.add_subplot(gs[0, 2])
for val, color, label in [(0, C_NEG, 'No Disease'), (1, C_POS, 'Disease')]:
    ax3.hist(df[df['cardio'] == val]['bmi'], bins=30, alpha=0.7,
             color=color, label=label, edgecolor=PANEL_BG)
ax3.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL_BG, edgecolor=GRID_COL)
style_ax(ax3, 'BMI Distribution by Class')
ax3.set_xlabel('BMI')
ax3.set_xlim(10, 60)

ax4 = fig.add_subplot(gs[1, 0])
sample = df.sample(2000, random_state=42)
for val, color in [(0, C_NEG), (1, C_POS)]:
    mask = sample['cardio'] == val
    ax4.scatter(sample[mask]['ap_hi'], sample[mask]['ap_lo'],
                alpha=0.3, s=10, color=color)
style_ax(ax4, 'Systolic vs Diastolic BP')
ax4.set_xlabel('Systolic (ap_hi)')
ax4.set_ylabel('Diastolic (ap_lo)')

ax5 = fig.add_subplot(gs[1, 1])
chol_labels = ['Normal', 'Above\nNormal', 'Well Above\nNormal']
x = np.arange(3)
w = 0.35
for i, (val, color, label) in enumerate([(0, C_NEG, 'No Disease'), (1, C_POS, 'Disease')]):
    counts_chol = df[df['cardio'] == val]['cholesterol'].value_counts().sort_index()
    ax5.bar(x + i*w, counts_chol.values, w, color=color, label=label, edgecolor=PANEL_BG)
ax5.set_xticks(x + w/2)
ax5.set_xticklabels(chol_labels, fontsize=8)
ax5.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL_BG, edgecolor=GRID_COL)
style_ax(ax5, 'Cholesterol Level vs Cardio')

ax6 = fig.add_subplot(gs[1, 2])
num_cols = ['age', 'bmi', 'ap_hi', 'ap_lo', 'pulse_pressure', 'cholesterol', 'gluc', 'cardio']
corr = df[num_cols].corr()
im = ax6.imshow(corr, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
ax6.set_xticks(range(len(num_cols)))
ax6.set_yticks(range(len(num_cols)))
short_names = ['age', 'bmi', 'ap_hi', 'ap_lo', 'pulse\npress', 'chol', 'gluc', 'cardio']
ax6.set_xticklabels(short_names, fontsize=7, color=MUTED, rotation=45, ha='right')
ax6.set_yticklabels(short_names, fontsize=7, color=MUTED)
for i in range(len(num_cols)):
    for j in range(len(num_cols)):
        ax6.text(j, i, f'{corr.iloc[i,j]:.2f}', ha='center', va='center',
                 fontsize=6, color='black' if abs(corr.iloc[i,j]) < 0.5 else 'white')
ax6.set_title('Correlation Heatmap', color=TEXT, fontsize=11, fontweight='bold', pad=8)
ax6.tick_params(colors=MUTED)
for spine in ax6.spines.values():
    spine.set_edgecolor(GRID_COL)

ax7 = fig.add_subplot(gs[2, 0])
lifestyle = ['smoke', 'alco', 'active', 'hypertension', 'obese']
labels_l  = ['Smoker', 'Alcohol', 'Active', 'Hypertensive', 'Obese']
disease_rates = [df[df[f] == 1]['cardio'].mean() * 100 for f in lifestyle]
colors_l = [C_POS if r > 50 else C_NEG for r in disease_rates]
bars7 = ax7.barh(labels_l, disease_rates, color=colors_l, edgecolor=PANEL_BG)
for bar, rate in zip(bars7, disease_rates):
    ax7.text(rate + 0.5, bar.get_y() + bar.get_height()/2,
             f'{rate:.1f}%', va='center', color=TEXT, fontsize=8)
ax7.axvline(50, color=MUTED, linestyle='--', linewidth=0.8, alpha=0.7)
style_ax(ax7, 'Disease Rate by Lifestyle Factor')
ax7.set_xlabel('% with Heart Disease')
ax7.set_xlim(0, 80)

ax8 = fig.add_subplot(gs[2, 1])
age_grp_labels = ['<40', '40–50', '50–60', '60+']
rates = [df[df['age_group'] == g]['cardio'].mean() * 100 for g in range(4)]
bars8 = ax8.bar(age_grp_labels, rates, color=[C_NEG, C_NEG, C_POS, C_POS],
                edgecolor=PANEL_BG, width=0.5)
for bar, rate in zip(bars8, rates):
    ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{rate:.1f}%', ha='center', va='bottom', color=TEXT, fontsize=9)
style_ax(ax8, 'Disease Rate by Age Group')
ax8.set_ylabel('% with Heart Disease')

ax9 = fig.add_subplot(gs[2, 2])
gender_rates = df.groupby('gender')['cardio'].mean() * 100
ax9.bar(['Female (1)', 'Male (2)'], gender_rates.values,
        color=[C_NEG, C_POS], width=0.4, edgecolor=PANEL_BG)
for i, rate in enumerate(gender_rates.values):
    ax9.text(i, rate + 0.5, f'{rate:.1f}%', ha='center', color=TEXT, fontsize=10)
style_ax(ax9, 'Disease Rate by Gender')
ax9.set_ylabel('% with Heart Disease')

fig.suptitle('Cardiovascular Disease — Exploratory Data Analysis',
             color=TEXT, fontsize=16, fontweight='bold', y=0.98)
plt.savefig('outputs/eda.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print("EDA plot saved.")

print("\n" + "=" * 60)
print("STEP 4: FEATURE PREPARATION")
print("=" * 60)

features = ['age', 'gender', 'height', 'weight', 'ap_hi', 'ap_lo',
            'cholesterol', 'gluc', 'smoke', 'alco', 'active',
            'bmi', 'pulse_pressure', 'map', 'hypertension', 'obese', 'age_group']

X = df[features]
y = df['cardio']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print(f"Train size: {X_train.shape[0]:,} | Test size: {X_test.shape[0]:,}")
print(f"Features: {features}")

print("\n" + "=" * 60)
print("STEP 5: TRAINING MODELS")
print("=" * 60)

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=15, n_jobs=-1),
    'Random Forest':       RandomForestClassifier(n_estimators=200, max_depth=10,
                                                   min_samples_leaf=5, random_state=42, n_jobs=-1),
    'Gradient Boosting':   GradientBoostingClassifier(n_estimators=100, max_depth=4,
                                                       learning_rate=0.1, random_state=42,
                                                       subsample=0.8),
    'Linear SVM':          CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2000, random_state=42), cv=3),
}

results = {}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for name, model in models.items():
    print(f"\n  Training {name}...", end='', flush=True)

    if name in ['Logistic Regression', 'K-Nearest Neighbors', 'Linear SVM']:
        Xtr, Xte = X_train_sc, X_test_sc
    else:
        Xtr, Xte = X_train.values, X_test.values

    model.fit(Xtr, y_train)
    y_pred = model.predict(Xte)
    y_prob = model.predict_proba(Xte)[:, 1]

    if name in ['Logistic Regression', 'Random Forest']:
        cv_scores = cross_val_score(model, Xtr, y_train, cv=cv,
                                    scoring='roc_auc', n_jobs=-1)
    else:
        cv_scores = np.array([roc_auc_score(y_test, y_prob)] * 5)

    results[name] = {
        'model':    model,
        'accuracy': accuracy_score(y_test, y_pred),
        'f1':       f1_score(y_test, y_pred),
        'roc_auc':  roc_auc_score(y_test, y_prob),
        'cv_mean':  cv_scores.mean(),
        'cv_std':   cv_scores.std(),
        'y_pred':   y_pred,
        'y_prob':   y_prob,
        'scaled':   name in ['Logistic Regression', 'K-Nearest Neighbors', 'Linear SVM'],
    }
    print(f" done. ROC-AUC: {results[name]['roc_auc']:.4f}")

print("\n" + "=" * 60)
print("STEP 6: MODEL EVALUATION")
print("=" * 60)

print(f"\n{'Model':<25} {'Accuracy':>10} {'F1 Score':>10} {'ROC-AUC':>10} {'CV AUC (mean±std)':>20}")
print("-" * 80)
for name, res in results.items():
    print(f"{name:<25} {res['accuracy']:>10.4f} {res['f1']:>10.4f} "
          f"{res['roc_auc']:>10.4f} {res['cv_mean']:>10.4f}±{res['cv_std']:.4f}")

best_name = max(results, key=lambda k: results[k]['roc_auc'])
best = results[best_name]
print(f"\n  ✓ Best model: {best_name} (ROC-AUC: {best['roc_auc']:.4f})")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.patch.set_facecolor(DARK_BG)

ax = axes[0]
ax.set_facecolor(PANEL_BG)
names = list(results.keys())
short_names2 = ['LR', 'KNN', 'RF', 'GBM', 'SVM']
metrics_data = {
    'Accuracy': [results[n]['accuracy'] for n in names],
    'F1 Score': [results[n]['f1'] for n in names],
    'ROC-AUC':  [results[n]['roc_auc'] for n in names],
}
x = np.arange(len(names))
w = 0.25
colors_m = ['#4d9de0', '#7ec8a4', '#e05c5c']
for i, (metric, vals) in enumerate(metrics_data.items()):
    ax.bar(x + i*w, vals, w, label=metric, color=colors_m[i], edgecolor=PANEL_BG)
ax.set_xticks(x + w)
ax.set_xticklabels(short_names2, color=MUTED, fontsize=9)
ax.set_ylim(0.6, 0.85)
ax.set_title('Model Comparison', color=TEXT, fontsize=12, fontweight='bold')
ax.legend(fontsize=9, labelcolor=TEXT, facecolor=PANEL_BG, edgecolor=GRID_COL)
ax.tick_params(colors=MUTED)
for spine in ax.spines.values(): spine.set_edgecolor(GRID_COL)
ax.grid(axis='y', color=GRID_COL, linewidth=0.5)

ax = axes[1]
ax.set_facecolor(PANEL_BG)
roc_colors = ['#4d9de0', '#7ec8a4', '#e05c5c', '#f4a261', '#c77dff']
for (name, res), color in zip(results.items(), roc_colors):
    fpr, tpr, _ = roc_curve(y_test, res['y_prob'])
    short = name.replace('Gradient Boosting', 'GBM').replace('Logistic Regression', 'LR') \
               .replace('K-Nearest Neighbors', 'KNN').replace('Random Forest', 'RF')
    ax.plot(fpr, tpr, color=color, linewidth=2,
            label=f'{short} ({res["roc_auc"]:.3f})')
ax.plot([0,1],[0,1], '--', color=MUTED, linewidth=1)
ax.set_xlabel('False Positive Rate', color=MUTED, fontsize=10)
ax.set_ylabel('True Positive Rate', color=MUTED, fontsize=10)
ax.set_title('ROC Curves', color=TEXT, fontsize=12, fontweight='bold')
ax.legend(fontsize=8, labelcolor=TEXT, facecolor=PANEL_BG, edgecolor=GRID_COL)
ax.tick_params(colors=MUTED)
for spine in ax.spines.values(): spine.set_edgecolor(GRID_COL)
ax.grid(color=GRID_COL, linewidth=0.5)

ax = axes[2]
ax.set_facecolor(PANEL_BG)
cm = confusion_matrix(y_test, best['y_pred'])
ax.imshow(cm, cmap='Blues', aspect='auto')
for i in range(2):
    for j in range(2):
        ax.text(j, i, f'{cm[i,j]:,}', ha='center', va='center',
                color='white' if cm[i,j] > cm.max()/2 else 'black', fontsize=14, fontweight='bold')
ax.set_xticks([0,1])
ax.set_yticks([0,1])
ax.set_xticklabels(['Pred: No Disease', 'Pred: Disease'], color=MUTED, fontsize=9)
ax.set_yticklabels(['Actual: No Disease', 'Actual: Disease'], color=MUTED, fontsize=9)
ax.set_title(f'Confusion Matrix\n({best_name})', color=TEXT, fontsize=12, fontweight='bold')
for spine in ax.spines.values(): spine.set_edgecolor(GRID_COL)

fig.suptitle('Model Evaluation Results', color=TEXT, fontsize=15, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('outputs/model_comparison.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print("Model comparison plot saved.")

print("\n" + "=" * 60)
print("STEP 7: FEATURE IMPORTANCE")
print("=" * 60)

best_model = best['model']
if best_name in ('Random Forest', 'Gradient Boosting'):
    importances = best_model.feature_importances_
    imp_type = 'Feature Importance'
else:
    Xte_use = X_test_sc if best['scaled'] else X_test.values
    perm = permutation_importance(best_model, Xte_use, y_test,
                                  n_repeats=10, random_state=42, n_jobs=-1)
    importances = perm.importances_mean
    imp_type = 'Permutation Importance'

imp_df = pd.DataFrame({'feature': features, 'importance': importances})
imp_df = imp_df.sort_values('importance', ascending=True)

fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(PANEL_BG)
colors_imp = [C_POS if v > imp_df['importance'].median() else C_NEG
              for v in imp_df['importance']]
bars = ax.barh(imp_df['feature'], imp_df['importance'],
               color=colors_imp, edgecolor=PANEL_BG)
for bar, val in zip(bars, imp_df['importance']):
    ax.text(val + imp_df['importance'].max()*0.01,
            bar.get_y() + bar.get_height()/2,
            f'{val:.4f}', va='center', color=TEXT, fontsize=8)
ax.set_title(f'Feature Importance ({best_name} — {imp_type})',
             color=TEXT, fontsize=13, fontweight='bold', pad=12)
ax.tick_params(colors=MUTED, labelsize=9)
ax.set_xlabel(imp_type, color=MUTED)
for spine in ax.spines.values(): spine.set_edgecolor(GRID_COL)
ax.grid(axis='x', color=GRID_COL, linewidth=0.5)
plt.tight_layout()
plt.savefig('outputs/feature_importance.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.close()
print(f"Feature importance saved. Type: {imp_type}")

print("\n" + "=" * 60)
print("STEP 8: SAVING ARTIFACTS")
print("=" * 60)

joblib.dump(best_model, 'models/best_model.pkl')
joblib.dump(scaler, 'models/scaler.pkl')

summary = {
    'best_model': best_name,
    'features': features,
    'metrics': {
        name: {
            'accuracy':    round(res['accuracy'], 4),
            'f1_score':    round(res['f1'], 4),
            'roc_auc':     round(res['roc_auc'], 4),
            'cv_auc_mean': round(res['cv_mean'], 4),
            'cv_auc_std':  round(res['cv_std'], 4),
        }
        for name, res in results.items()
    },
    'classification_report': classification_report(
        y_test, best['y_pred'], target_names=['No Disease', 'Disease']
    )
}

with open('data/pipeline_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"Saved: best_model.pkl, scaler.pkl, pipeline_summary.json")
print(f"\n{'='*60}")
print("PIPELINE COMPLETE")
print(f"Best model: {best_name}")
print(f"ROC-AUC:    {best['roc_auc']:.4f}")
print(f"Accuracy:   {best['accuracy']:.4f}")
print(f"F1 Score:   {best['f1']:.4f}")
print(f"{'='*60}")
print("\nClassification Report (Best Model):")
print(summary['classification_report'])

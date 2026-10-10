import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import brier_score_loss, roc_auc_score, accuracy_score
import os

# 1. Generate Synthetic Dataset
np.random.seed(42)
n_samples = 2000

# Temporal dimension for chronological splitting
dates = pd.date_range(start="2023-01-01", periods=n_samples, freq="D")
clusters = np.random.choice(["price_cut", "product_launch", "expansion", "marketing_blitz"], n_samples)
evidence_count = np.random.poisson(lam=5, size=n_samples)
horizon_days = np.random.choice([7, 14, 30, 90], n_samples)

# True probabilities (hidden)
base_prob = np.where(clusters == "price_cut", 0.3, 
            np.where(clusters == "product_launch", 0.6,
            np.where(clusters == "expansion", 0.4, 0.5)))
base_prob += (evidence_count * 0.05)
base_prob -= (horizon_days * 0.002)
base_prob = np.clip(base_prob, 0.01, 0.99)

# Actual observed outcome
outcomes = np.random.binomial(1, base_prob)

df = pd.DataFrame({
    "date": dates,
    "cluster": clusters,
    "evidence_count": evidence_count,
    "horizon_days": horizon_days,
    "outcome": outcomes
})
df = df.sort_values("date").reset_index(drop=True)

# 2. Preprocessing
# One-hot encode clusters
df_encoded = pd.get_dummies(df, columns=["cluster"], drop_first=True)
features = [c for c in df_encoded.columns if c not in ("date", "outcome")]

X = df_encoded[features]
y = df_encoded["outcome"]

# 3. Leakage-safe Splitting (Chronological)
tscv = TimeSeriesSplit(n_splits=5)
for train_index, test_index in tscv.split(X):
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]

# 4. Training
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train, y_train)

# 5. Evaluation
y_pred_prob = model.predict_proba(X_test)[:, 1]
y_pred = model.predict(X_test)

brier = brier_score_loss(y_test, y_pred_prob)
auc = roc_auc_score(y_test, y_pred_prob)
accuracy = accuracy_score(y_test, y_pred)

print("Evaluation Metrics (Test Set):")
print(f"Brier Score: {brier:.4f}")
print(f"ROC AUC:     {auc:.4f}")
print(f"Accuracy:    {accuracy:.4f}")

# 6. Serialization
os.makedirs("models", exist_ok=True)
model_path = "models/forecasting_model.pkl"
joblib.dump(model, model_path)
print(f"Model saved to {model_path}")

# 7. Metadata (for loading/preprocessing)
metadata = {
    "features": features,
    "version": "1.0.0",
    "metrics": {
        "brier_score": float(brier),
        "roc_auc": float(auc),
        "accuracy": float(accuracy)
    }
}
import json
with open("models/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
print("Metadata saved to models/metadata.json")

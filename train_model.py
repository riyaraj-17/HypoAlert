import pandas as pd
import random
from sklearn.ensemble import RandomForestClassifier
import joblib

data = []

# Generate realistic synthetic patient data
for _ in range(5000):

    glucose = random.randint(60, 200)      # mg/dL
    hours = random.randint(0, 8)          # hours since meal
    activity = random.choice([0, 1, 2])   # 0=low, 1=medium, 2=high
    insulin = random.randint(0, 6)        # hours since insulin

    # simulate previous glucose to calculate trend (slope)
    prev_glucose = glucose + random.randint(-25, 25)
    slope = glucose - prev_glucose

    # ---------------------------------------
    # REALISTIC 3-LEVEL HYPOGLYCEMIA RISK
    # ---------------------------------------
    # 0 = LOW, 1 = MEDIUM, 2 = HIGH
    risk = 0

    # -------- HIGH RISK --------
    if glucose < 70:
        risk = 2
    elif slope < -20 and glucose < 100:
        risk = 2
    elif insulin < 2 and glucose < 100:
        risk = 2
    elif hours > 6 and glucose < 90:
        risk = 2

    # -------- MEDIUM RISK --------
    elif glucose < 90:
        risk = 1
    elif hours > 4:
        risk = 1
    elif activity == 2 and glucose < 120:
        risk = 1
    elif slope < -10:
        risk = 1

    # -------- LOW RISK --------
    else:
        risk = 0

    data.append([glucose, hours, activity, insulin, slope, risk])

# Create DataFrame
df = pd.DataFrame(
    data,
    columns=["glucose", "hours", "activity", "insulin", "slope", "risk"]
)

# Features and label
X = df[["glucose", "hours", "activity", "insulin", "slope"]]
y = df["risk"]

# Train model
model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42
)
model.fit(X, y)

# Save model
joblib.dump(model, "model.pkl")

print("✅ 3-Class Hypoglycemia Risk Model trained and saved as model.pkl")

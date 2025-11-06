import pandas as pd

import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.utils.class_weight import compute_sample_weight

# --- Configuration ---
INPUT_CSV = "dataset/Final_dataset/model_training_dataset_FINAL10.csv"
OUTPUT_DIR = "dataset/visuals"
MODEL_DIR = "dataset/models"
TARGET_COLUMN = 'Day1_collection_cr'

try:
    df = pd.read_csv(INPUT_CSV)
    df.dropna(subset=[TARGET_COLUMN], inplace=True)
    print(f"Number rows:{len(df)}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    # prepare the data
    bins = [-1, 5, 20, 1000]
    labels = ['Low (< 5Cr)', 'Medium (5-20Cr)', 'High (> 20Cr)']
    df['Category'] = pd.cut(df[TARGET_COLUMN], bins=bins, labels=labels)

    le = LabelEncoder()
    df['Category_Encoded'] = le.fit_transform(df['Category'])


    joblib.dump(le, os.path.join(MODEL_DIR, 'label_encoder.pkl'))
    joblib.dump(labels, os.path.join(MODEL_DIR, 'category_labels.pkl'))
    y = df['Category_Encoded']
    X = df.drop(columns=[TARGET_COLUMN, 'Category', 'Category_Encoded'])
    joblib.dump(X.columns.tolist(), os.path.join(MODEL_DIR, 'feature_names.pkl'))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    joblib.dump(scaler, os.path.join(MODEL_DIR, 'scaler.pkl'))

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    rf_model.fit(X_train, y_train)

    sample_weights = compute_sample_weight(class_weight='balanced', y=y_train)
    xgb_model = XGBClassifier(n_estimators=100, random_state=42, eval_metric='mlogloss')
    xgb_model.fit(X_train, y_train, sample_weight=sample_weights)

    lgbm_model = LGBMClassifier(n_estimators=100, random_state=42, class_weight='balanced', verbose=-1)
    lgbm_model.fit(X_train, y_train)

    print("\n--- Model Comparison ---")
    models = {'Random Forest': rf_model, 'XGBoost': xgb_model, 'LightGBM': lgbm_model}
    results = []

    for name, model in models.items():
        y_pred = model.predict(X_test)
        results.append({
            'Model': name,
            'Accuracy': accuracy_score(y_test, y_pred),
            'F1-Score (W)': f1_score(y_test, y_pred, average='weighted'),
            'Precision (W)': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'Recall (W)': recall_score(y_test, y_pred, average='weighted')
        })
        joblib.dump(model, os.path.join(MODEL_DIR, f'{name.lower().replace(" ", "_")}_model.pkl'))

    results_df = pd.DataFrame(results)
    print(results_df)
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'model_comparison_results.csv'), index=False)
    print(f"\n✅ Training complete. Artifacts saved to '{MODEL_DIR}' and '{OUTPUT_DIR}'.")

except Exception as e:
    print(f"An error occurred: {e}")
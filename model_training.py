import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn import metrics
import joblib  # <-- IMPORTED JOBLIB

# --- Configuration ---
INPUT_CSV = "dataset/Final_dataset/model_training_dataset_FINAL.csv"
OUTPUT_DIR = "dataset/visuals"
MODEL_DIR = "dataset/models"  # <-- NEW: Folder to save models
TARGET_COLUMN = 'Day1_collection_cr'

try:
    df = pd.read_csv(INPUT_CSV)
    df.dropna(subset=[TARGET_COLUMN], inplace=True)
    print(f"Loaded {len(df)} rows of clean data for training.")

    # Create output directories
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)  # <-- NEW: Create model folder

    # ==============================================================================
    # 1. Prepare Data for Modeling (X/y Split)
    # ==============================================================================

    y = df[TARGET_COLUMN]
    X = df.drop(columns=[TARGET_COLUMN])

    # --- NEW: Save the list of feature names ---
    joblib.dump(X.columns.tolist(), os.path.join(MODEL_DIR, 'feature_names.pkl'))
    print(f"Features (X): {len(X.columns)} columns. Names saved.")

    # ==============================================================================
    # 2. Create Training and Testing Sets
    # ==============================================================================

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # ==============================================================================
    # 3. Initialize and Train All Models
    # ==============================================================================

    # --- Model 1: Linear Regression ---
    print("\nTraining Linear Regression model...")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)

    # --- Model 2: Random Forest ---
    print("\nTraining Random Forest model...")
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # --- Model 3: XGBoost ---
    print("\nTraining XGBoost model...")
    xgb_model = XGBRegressor(n_estimators=100, random_state=42, objective='reg:squarederror')
    xgb_model.fit(X_train, y_train)
    print("All models trained.")

    # ==============================================================================
    # 4. Evaluate Model Performance (The "Leaderboard")
    # ==============================================================================

    y_pred_lr = lr_model.predict(X_test)
    y_pred_rf = rf_model.predict(X_test)
    y_pred_xgb = xgb_model.predict(X_test)

    print("\n--- Model Performance Metrics (on Test Set) ---")

    results = {
        'Model': ['Linear Regression', 'Random Forest', 'XGBoost'],
        'R-squared ($R^2$)': [
            metrics.r2_score(y_test, y_pred_lr),
            metrics.r2_score(y_test, y_pred_rf),
            metrics.r2_score(y_test, y_pred_xgb)
        ],
        'Mean Absolute Error (MAE)': [
            metrics.mean_absolute_error(y_test, y_pred_lr),
            metrics.mean_absolute_error(y_test, y_pred_rf),
            metrics.mean_absolute_error(y_test, y_pred_xgb)
        ],
        'Root Mean Squared Error (RMSE)': [
            np.sqrt(metrics.mean_squared_error(y_test, y_pred_lr)),
            np.sqrt(metrics.mean_squared_error(y_test, y_pred_rf)),
            np.sqrt(metrics.mean_squared_error(y_test, y_pred_xgb))
        ]
    }

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # --- NEW: Save the results table ---
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'model_performance_metrics.csv'), index=False)
    print("\nModel performance metrics saved.")

    # ==============================================================================
    # 5. --- NEW: SAVE THE TRAINED MODELS ---
    # ==============================================================================

    joblib.dump(lr_model, os.path.join(MODEL_DIR, 'linear_regression_model.pkl'))
    joblib.dump(rf_model, os.path.join(MODEL_DIR, 'random_forest_model.pkl'))
    joblib.dump(xgb_model, os.path.join(MODEL_DIR, 'xgboost_model.pkl'))

    print(f"\nAll 3 models have been saved to the '{MODEL_DIR}' folder.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
import streamlit as st
import pandas as pd
import joblib
import os

# --- Configuration ---
MODEL_DIR = "dataset/models"
VISUALS_DIR = "dataset/visuals"

# --- Page Setup ---
st.set_page_config(page_title="Box Office Prediction", layout="wide")
st.title("🎬 Hindi Movie Day 1 Box Office Predictor")


# --- Helper Function to Load Models ---
@st.cache_resource
def load_models_and_data():
    """Loads all models and data from disk, caching them."""
    try:
        lr = joblib.load(os.path.join(MODEL_DIR, 'linear_regression_model.pkl'))
        rf = joblib.load(os.path.join(MODEL_DIR, 'random_forest_model.pkl'))
        xgb = joblib.load(os.path.join(MODEL_DIR, 'xgboost_model.pkl'))
        features = joblib.load(os.path.join(MODEL_DIR, 'feature_names.pkl'))
        metrics = pd.read_csv(os.path.join(VISUALS_DIR, 'model_performance_metrics.csv'))
        return lr, rf, xgb, features, metrics
    except FileNotFoundError:
        return None, None, None, None, None


# --- Load Data ---
lr_model, rf_model, xgb_model, feature_names, metrics_df = load_models_and_data()

if lr_model is None:
    st.error("Error: Models not found. Please run the 'train_and_save_models.py' script first.")
else:
    # ==============================================================================
    # --- Prediction Sidebar (The "Predictor") ---
    # ==============================================================================
    st.sidebar.header("Make a Prediction!")

    # Create sliders and inputs for the most important features
    # These are based on your feature importance list

    st.sidebar.markdown("**Important!** These predictions are for demonstration *only*. The model is not accurate.")

    likeCount = st.sidebar.number_input("Trailer Like Count", min_value=0, value=10000)
    commentCount = st.sidebar.number_input("Trailer Comment Count", min_value=0, value=1000)
    runtime = st.sidebar.slider("Runtime (min)", min_value=60, max_value=240, value=150)
    viewCount = st.sidebar.number_input("Trailer View Count", min_value=0, value=1000000)
    day_of_week = st.sidebar.slider("Release Day of Week (0=Mon, 4=Fri)", min_value=0, max_value=6, value=4)
    median_sentiment = st.sidebar.slider("Median Sentiment", min_value=-1.0, max_value=1.0, value=0.1, step=0.01)
    avg_sentiment = st.sidebar.slider("Average Sentiment", min_value=-1.0, max_value=1.0, value=0.1, step=0.01)
    promotion_days = st.sidebar.slider("Promotion Days (Trailer to Release)", min_value=0, max_value=365, value=45)
    release_month = st.sidebar.slider("Release Month", min_value=1, max_value=12, value=1)
    prod_score = st.sidebar.slider("Production House Score", min_value=0.0, max_value=100.0, value=50.0, step=0.1)

    # --- Create the input DataFrame ---
    # We must create a DataFrame with all 19 features, in the correct order
    input_data = pd.DataFrame(columns=feature_names)
    input_data.loc[0] = 0  # Initialize all columns with 0

    # Update the DataFrame with values from the sliders
    input_data['likeCount'] = likeCount
    input_data['commentCount'] = commentCount
    input_data['Runtime (min)'] = runtime
    input_data['viewCount'] = viewCount
    input_data['Release_Day_of_Week'] = day_of_week
    input_data['median_sentiment'] = median_sentiment
    input_data['avg_sentiment'] = avg_sentiment
    input_data['Promotion_Duration_Days'] = promotion_days
    input_data['Release_Month'] = release_month
    input_data['Production_House_Score'] = prod_score
    # Other features (like Director_Score, Genres) are left as 0 for this demo

    # --- Make Predictions ---
    pred_lr = lr_model.predict(input_data)[0]
    pred_rf = rf_model.predict(input_data)[0]
    pred_xgb = xgb_model.predict(input_data)[0]

    st.sidebar.subheader("Predicted Day 1 Collection (in Crores):")
    st.sidebar.metric("Random Forest", f"{pred_rf:.2f} Cr", f"{pred_rf - pred_xgb:.2f} Cr vs XGB")
    st.sidebar.metric("XGBoost", f"{pred_xgb:.2f} Cr", f"{pred_xgb - pred_rf:.2f} Cr vs RF")
    st.sidebar.metric("Linear Regression", f"{pred_lr:.2f} Cr")

    # ==============================================================================
    # --- Main Page (Charts and Comparisons) ---
    # ==============================================================================

    st.header("Model Performance Comparison")
    st.markdown(
        "Here is how the three models performed on the test data. **The R-squared is very low, indicating a poor model fit.**")

    # Show the metrics table
    st.dataframe(metrics_df)

    # Show a bar chart of the metrics
    metrics_melted = metrics_df.melt('Model', var_name='Metric', value_name='Value')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("$R^2$ (Higher is Better)")
        r2_chart = sns.barplot(data=metrics_melted[metrics_melted['Metric'] == 'R-squared ($R^2$)'],
                               x='Model', y='Value', hue='Model')
        st.pyplot(r2_chart.figure)

    with col2:
        st.subheader("MAE (Lower is Better)")
        mae_chart = sns.barplot(data=metrics_melted[metrics_melted['Metric'] == 'Mean Absolute Error (MAE)'],
                                x='Model', y='Value', hue='Model')
        st.pyplot(mae_chart.figure)

    st.header("Exploratory Data Analysis (EDA) & Feature Importance")
    st.markdown("These charts show which features the models found most important.")

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("XGBoost Feature Importance")
        st.image(os.path.join(VISUALS_DIR, 'feature_importance_xgb.png'))
    with col4:
        st.subheader("Top 15 Directors")
        st.image(os.path.join(VISUALS_DIR, 'director_top15_barplot.png'))

    col5, col6 = st.columns(2)
    with col5:
        st.subheader("Top 15 Production Houses")
        st.image(os.path.join(VISUALS_DIR, 'production_top15_barplot.png'))
    with col6:
        st.subheader("Genre Distribution")
        st.image(os.path.join(VISUALS_DIR, 'genre_top6_piechart.png'))
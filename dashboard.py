import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns


MODEL_DIR = "dataset/models"
VISUALS_DIR = "dataset/visuals"

st.set_page_config(page_title="Box Office Predictor", layout="wide")


#Load Assets
@st.cache_resource
def load_assets():
    try:
        assets = {}
        assets['rf'] = joblib.load(os.path.join(MODEL_DIR, 'random_forest_model.pkl'))
        assets['xgb'] = joblib.load(os.path.join(MODEL_DIR, 'xgboost_model.pkl'))
        assets['lgbm'] = joblib.load(os.path.join(MODEL_DIR, 'lightgbm_model.pkl'))
        assets['le'] = joblib.load(os.path.join(MODEL_DIR, 'label_encoder.pkl'))
        assets['features'] = joblib.load(os.path.join(MODEL_DIR, 'feature_names.pkl'))
        assets['metrics'] = pd.read_csv(os.path.join(VISUALS_DIR, 'model_comparison_results.csv'))
        return assets
    except FileNotFoundError:
        return None


assets = load_assets()

if assets is None:
    st.error("System Error: Models not found. Please run the training script first.")
    st.stop()

#Sidebar params
st.sidebar.header("🎬 Movie Details Predictor")

# Create inputs for all features
score_prod = st.sidebar.slider("Production House Score", 0, 100, 50)
score_dir = st.sidebar.slider("Director Score", 0, 100, 50)
runtime = st.sidebar.number_input("Runtime (mins)", 60, 240, 150)
promo_days = st.sidebar.number_input("Promotion Days", 0, 365, 45)

st.sidebar.markdown("---")
st.sidebar.subheader("Release Details")
rel_year = st.sidebar.selectbox("Year", [2023, 2024, 2025])
rel_month = st.sidebar.selectbox("Month", range(1, 13), index=0)
# Map days to readable names for UI
day_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
rel_day_ui = st.sidebar.selectbox("Day of Week", list(day_map.values()), index=4)  # Default Friday
rel_day = [k for k, v in day_map.items() if v == rel_day_ui][0]

st.sidebar.markdown("---")
st.sidebar.subheader("Trailer & Sentiment")
views = st.sidebar.number_input("Trailer Views", 0, value=5000000, step=100000)
likes = st.sidebar.number_input("Trailer Likes", 0, value=100000, step=10000)
comments = st.sidebar.number_input("Trailer Comments", 0, value=5000, step=1000)
avg_sent = st.sidebar.slider("Avg Sentiment (-1 to 1)", -1.0, 1.0, 0.2, 0.01)
med_sent = st.sidebar.slider("Median Sentiment (-1 to 1)", -1.0, 1.0, 0.2, 0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("Genre (Select Primary)")
# Helper for genres
genre_options = ['Drama', 'Comedy', 'Action', 'Thriller', 'Romance', 'Crime', 'Other']
selected_genres = st.sidebar.multiselect("Select Genres", genre_options, default=['Action'])

#Main pg
st.title("📊 Box Office Prediction Dashboard")


tab1, tab2, tab3 = st.tabs(["🤖 Predictor", "📈 Model Comparison", "🖼️ EDA Visuals"])

#Predictor tab
with tab1:
    st.subheader("Predict Day 1 Collection Category")

    if st.button("Predict Results", type="primary", use_container_width=True):
        # 1. Build Input DataFrame
        input_data = pd.DataFrame(columns=assets['features'])
        input_data.loc[0] = 0  # Init with 0s

        # Fill numeric/score features
        input_data['Production_House_Score'] = score_prod
        input_data['Director_Score'] = score_dir
        input_data['Runtime (min)'] = runtime
        input_data['Release_Year'] = rel_year
        input_data['Release_Month'] = rel_month
        input_data['Release_Day_of_Week'] = rel_day
        input_data['Promotion_Duration_Days'] = promo_days
        input_data['avg_sentiment'] = avg_sent
        input_data['median_sentiment'] = med_sent
        input_data['viewCount'] = views
        input_data['likeCount'] = likes
        input_data['commentCount'] = comments


        for genre in selected_genres:
            col_name = f'Genre_{genre}'
            if col_name in input_data.columns:
                input_data[col_name] = 1


        pred_rf = assets['rf'].predict(input_data)[0]
        pred_xgb = assets['xgb'].predict(input_data)[0]
        pred_lgbm = assets['lgbm'].predict(input_data)[0]

        #Decode labels
        label_rf = assets['le'].inverse_transform([pred_rf])[0]
        label_xgb = assets['le'].inverse_transform([pred_xgb])[0]
        label_lgbm = assets['le'].inverse_transform([pred_lgbm])[0]

        # sho the res
        c1, c2, c3 = st.columns(3)
        c1.metric("Random Forest", label_rf)
        c2.metric("XGBoost", label_xgb)
        c3.metric("LightGBM", label_lgbm)


        st.markdown("---")
        st.write("### Confidence Levels (Random Forest)")
        probs = assets['rf'].predict_proba(input_data)[0]
        prob_df = pd.DataFrame(probs, index=assets['le'].classes_, columns=['Probability'])
        st.bar_chart(prob_df)

# Tab for mdoel compraison
with tab2:
    st.header("Model Performance Leaderboard")
    st.dataframe(assets['metrics'].style.highlight_max(axis=0, color='lightgreen'), use_container_width=True)

    st.subheader("Metric Comparison Charts")
    col1, col2 = st.columns(2)



    def plot_metric(metric_name, color_palette):
        fig, ax = plt.subplots()
        sns.barplot(data=assets['metrics'], x='Model', y=metric_name, palette=color_palette, ax=ax)
        ax.set_title(f'{metric_name} by Model')
        ax.set_ylim(0, 1.0)
        return fig


    with col1:
        st.pyplot(plot_metric('Accuracy', 'viridis'))
    with col2:
        st.pyplot(plot_metric('F1-Score (W)', 'magma'))

    st.markdown("---")
    st.subheader("Confusion Matrix (Random Forest)")
    st.image(os.path.join(VISUALS_DIR, 'confusion_matrix_balanced.png'),
             caption="Where did the best model make mistakes?")

# Tab for EDA visuals display
with tab3:
    st.header("Exploratory Data Analysis")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 15 Directors")
        st.image(os.path.join(VISUALS_DIR, 'director_top15_barplot.png'))
        st.subheader("Genre Distribution")
        st.image(os.path.join(VISUALS_DIR, 'genre_top6_piechart.png'))

    with c2:
        st.subheader("Top 15 Production Houses")
        st.image(os.path.join(VISUALS_DIR, 'production_top15_barplot.png'))
        st.subheader("Correlation Heatmap")
        if os.path.exists(os.path.join(VISUALS_DIR, 'correlation_heatmap_full.png')):
            st.image(os.path.join(VISUALS_DIR, 'correlation_heatmap_full.png'))
        else:
            st.info("Full correlation heatmap not found.")
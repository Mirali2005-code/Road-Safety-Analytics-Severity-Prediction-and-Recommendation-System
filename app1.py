# =========================================
# 🚗 ADVANCED ACCIDENT DASHBOARD (STREAMLIT)
# =========================================

import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import numpy as np

# =========================================
# 📌 LOAD FILES
# =========================================
model = joblib.load("accident_model.pkl")
model_columns = joblib.load("model_columns.pkl")
df = pd.read_csv("road_cleaned_data.csv")

# =========================================
# 📌 PAGE CONFIG
# =========================================
st.set_page_config(page_title="Accident Dashboard", layout="wide")
st.title("🚗 Accident Severity Prediction Dashboard")

# =========================================
# 📌 SESSION STATE FOR HISTORY
# =========================================
if "history" not in st.session_state:
    st.session_state.history = []

# =========================================
# 📊 KPI SECTION
# =========================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Accidents", len(df))
#col2.metric("Slight", (df['Accident_severity'] == "Slight").sum())
#col3.metric("Serious", (df['Accident_severity'] == "Serious").sum())
#col4.metric("Fatal", (df['Accident_severity'] == "Fatal").sum())
col2.metric("Slight", df['Accident_severity'].str.contains("Slight", case=False).sum())
col3.metric("Serious", df['Accident_severity'].str.contains("Serious", case=False).sum())
col4.metric("Fatal", df['Accident_severity'].str.contains("Fatal", case=False).sum())

st.markdown("---")

# =========================================
# 🎛️ SIDEBAR INPUT
# =========================================
st.sidebar.header("🚦 Enter Conditions")


weather = st.sidebar.selectbox("Weather", df['Weather_conditions'].unique())
light = st.sidebar.selectbox("Light", df['Light_conditions'].unique())
road = st.sidebar.selectbox("Road", df['Road_surface_conditions'].unique())
cause = st.sidebar.selectbox("Cause", df['Cause_of_accident'].unique())
hour = st.sidebar.slider("Hour", 0, 23, 12)

# =========================================
# 📌 RECOMMENDATION FUNCTION
# =========================================
def get_recommendation(data, pred):
    rec = []

    if data['Hour'] >= 20 or data['Hour'] <= 5:
        rec.append("Increase lighting & patrol")

    if data['Weather_conditions'] in ["Rainy", "Fog"]:
        rec.append("Drive slowly")

    if data['Road_surface_conditions'] == "Wet":
        rec.append("Reduce speed")

    if data['Cause_of_accident'] == "Overspeed":
        rec.append("Control speed")

    if pred == 2:
        rec.append("🚨 High risk")
    elif pred == 1:
        rec.append("⚠ Moderate risk")

    return " | ".join(rec) if rec else "Normal"

# =========================================
# 🔮 PREDICTION (FIXED)
# =========================================
if st.sidebar.button("Predict Severity"):

    input_data = pd.DataFrame([{
        "Weather_conditions": weather,
        "Light_conditions": light,
        "Road_surface_conditions": road,
        "Cause_of_accident": cause,
        "Hour": hour
    }])

     # ✅ STANDARDIZE INPUT (CRITICAL FIX)
    for col in input_data.columns:
        if input_data[col].dtype == "object":
            input_data[col] = input_data[col].str.strip().str.title()
    
    #input_data = input_data.copy()
    #input_data['Weather_conditions'] = input_data['Weather_conditions'].str.strip()
    #input_data['Light_conditions'] = input_data['Light_conditions'].str.strip()
    #input_data['Road_surface_conditions'] = input_data['Road_surface_conditions'].str.strip()
    #input_data['Cause_of_accident'] = input_data['Cause_of_accident'].str.strip()

    input_encoded = pd.get_dummies(input_data)

    missing_cols = set(model_columns) - set(input_encoded.columns)
    for col in model_columns:
        if col not in input_encoded:
            input_encoded[col] = 0

    input_encoded = input_encoded[model_columns]

    # ✅ Get numeric prediction
    prediction = model.predict(input_encoded)[0]

    # If model gives probabilities (multi-class case)
    if isinstance(prediction, (list, np.ndarray)) and len(prediction) > 1:
        prediction = np.argmax(prediction)
    else:
        prediction = prediction


    # ✅ Map to label
    severity_map = {
        0: "🟢 Slight Injury",
        1: "🟡 Serious Injury",
        2: "🔴 Fatal Injury"
    }
    result = severity_map.get(prediction, severity_map.get(prediction, prediction))

    print("Prediction value:", prediction)
    print("Available keys:", severity_map.keys())

    ######

    # ✅ Pass numeric to recommendation
    rec = get_recommendation(input_data.iloc[0], prediction)

    # =========================================
    # SAVE HISTORY
    # =========================================
    record = input_data.copy()
    record['Prediction'] = result
    record['Recommendation'] = rec

    st.session_state.history.append(record)

    # =========================================
    # DISPLAY
    # =========================================
    st.subheader("🔮 Prediction Result")
    st.success(result)

    # ⭐ ADD THIS BLOCK HERE
    probs = model.predict_proba(input_encoded)[0]

    st.subheader("📊 Prediction Confidence")
    st.write({
        "Slight": f"{probs[0]*100:.2f}%",
        "Serious": f"{probs[1]*100:.2f}%",
        "Fatal": f"{probs[2]*100:.2f}%"
    })

    st.subheader("💡 Recommendation")
    st.info(rec)

# =========================================
# 📥 DOWNLOAD REPORT
# =========================================
if st.session_state.history:
    history_df = pd.concat(st.session_state.history, ignore_index=True)

    st.download_button(
        label="📥 Download Prediction Report",
        data=history_df.to_csv(index=False),
        file_name="prediction_report.csv",
        mime="text/csv"
    )

# =========================================
# 📋 PREDICTION HISTORY
# =========================================
st.markdown("## 📜 Prediction History")

if st.session_state.history:
    history_df = pd.concat(st.session_state.history, ignore_index=True)
    st.dataframe(history_df)
else:
    st.info("No predictions yet")

# =========================================
# 🗺️ MAP VISUALIZATION
# =========================================
st.markdown("## 📊 Risk Insights (No Location Data Available)")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Accidents by Weather")
    st.bar_chart(df['Weather_conditions'].value_counts())

with col2:
    st.subheader("Accidents by Cause")
    st.bar_chart(df['Cause_of_accident'].value_counts())

st.subheader("Severity vs Weather")
st.bar_chart(pd.crosstab(df['Weather_conditions'], df['Accident_severity']))

# =========================================
# 📊 CHARTS
# =========================================
st.markdown("## 📊 Insights")

# ⭐ ADD HERE
st.subheader("🔍 Important Factors")

importances = model.feature_importances_

feat_df = pd.DataFrame({
    "Feature": model_columns,
    "Importance": importances
}).sort_values(by="Importance", ascending=False).head(10)

st.bar_chart(feat_df.set_index("Feature"))

# EXISTING CHARTS
col1, col2 = st.columns(2)

# Hour chart
with col1:
    fig, ax = plt.subplots()
    df['Hour'].value_counts().sort_index().plot(kind='bar', ax=ax)
    ax.set_title("Accidents by Hour")
    st.pyplot(fig)

# Severity pie
with col2:
    fig, ax = plt.subplots()
    df['Accident_severity'].value_counts().plot(kind='pie', autopct='%1.1f%%', ax=ax)
    ax.set_ylabel("")
    ax.set_title("Severity Distribution")
    st.pyplot(fig)
# =========================================
# 📋 DATA PREVIEW
# =========================================
st.info("Model trained using SMOTE to handle class imbalance. Predictions may differ from real-world distribution.")
st.markdown("## 📄 Dataset Preview")
st.dataframe(df.head(50))
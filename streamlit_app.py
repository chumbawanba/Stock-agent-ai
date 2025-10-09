import streamlit as st
import pandas as pd

st.set_page_config(page_title="AlphaLayer - Augmented Market Insights", layout="wide")

st.title("📈 AlphaLayer")
st.markdown("**Augmented Market Insights** powered by historical data and technical indicators.")

# Load processed stock data
@st.cache_data
def load_data():
    return pd.read_csv("stock_analysis.csv")

df = load_data()

st.markdown("### 📊 Investment Opportunities")

for _, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 4])
    with col1:
        st.markdown(f"**[{row['Symbol']}](https://finance.yahoo.com/quote/{row['Symbol']})**")
    with col2:
        st.write(row["Action"])
    with col3:
        color = "green" if row["Action"] == "Buy" else "red"
        st.markdown(f"<span style='color:{color}; font-weight:bold'>{row['Action']}</span>", unsafe_allow_html=True)
    with col4:
        st.write(f"{row['Potential Return (%)']}%")
    with col5:
        st.write(row["Details"])

st.markdown("---")
st.caption("AlphaLayer © 2025 — Empowering smarter investing decisions")

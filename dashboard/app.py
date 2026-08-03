from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

DB = Path(__file__).resolve().parents[1] / "data" / "warehouse" / "procurement.duckdb"
st.set_page_config(page_title="UK Procurement Intelligence", page_icon="📊", layout="wide")
st.title("UK Public Procurement Intelligence")
st.caption("Supplier concentration, award trends, and explainable procurement-risk signals")

if not DB.exists():
    st.info("Run `python src/pipeline.py --fixture` to build the analytical warehouse.")
    st.stop()

with duckdb.connect(str(DB), read_only=True) as con:
    summary = con.execute("SELECT sum(award_value), count(*), count(DISTINCT supplier_sk), count(DISTINCT buyer_sk) FROM fact_award").fetchone()
    monthly = con.execute("SELECT * FROM mart_monthly_spend").df()
    risk = con.execute("SELECT * FROM mart_supplier_risk ORDER BY risk_score DESC").df()

cols = st.columns(4)
cols[0].metric("Awarded value", f"£{summary[0]:,.0f}")
cols[1].metric("Awards", f"{summary[1]:,}")
cols[2].metric("Suppliers", f"{summary[2]:,}")
cols[3].metric("Buyers", f"{summary[3]:,}")

left, right = st.columns((3, 2))
with left:
    st.plotly_chart(px.line(monthly, x="award_month", y="awarded_value", markers=True,
                            title="Monthly awarded value"), use_container_width=True)
with right:
    st.plotly_chart(px.bar(risk.head(10), x="risk_score", y="supplier_name", orientation="h",
                           title="Highest supplier risk signals", color="risk_score"), use_container_width=True)

st.subheader("Supplier risk register")
st.dataframe(risk, use_container_width=True, hide_index=True)
st.caption("Scores are transparent screening indicators and must be interpreted with procurement context.")


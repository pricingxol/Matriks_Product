import streamlit as st
import pandas as pd
import os

from loader import load_excel
from engine import lookup_rate
from validator import check_dependency
from formatter import pct

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Matriks Product – Bundling Rate",
    layout="wide"
)

st.title("📊 Matriks Product – Bundling Rate Calculator")
st.caption("Optimized Excel-Driven Pricing Engine")

# =========================
# FILE PATH
# =========================
FILE_PATH = "Template_Bundling_Rate_Streamlit_FULL.xlsx"

# =========================
# SAFE EXCEL LOADER (OPTIMIZED)
# =========================
@st.cache_data(show_spinner="📂 Loading pricing master...")
def load_excel_safe(path: str, last_modified: float):
    return load_excel(path)

if not os.path.exists(FILE_PATH):
    st.error("File Excel master tidak ditemukan di repository.")
    st.stop()

last_modified = os.path.getmtime(FILE_PATH)
sheets = load_excel_safe(FILE_PATH, last_modified)

# =========================
# LOAD MASTER
# =========================
if "COVERAGE_MASTER" not in sheets:
    st.error("Sheet COVERAGE_MASTER tidak ditemukan.")
    st.stop()

df_master = sheets["COVERAGE_MASTER"]
df_master.columns = df_master.columns.str.lower()
df_master = df_master[df_master["active"] == 1]

# =========================
# COVERAGE SELECTION
# =========================
st.subheader("Pilih Coverage")

coverage_map = {
    f"{r.coverage_code} - {r.coverage_name}": r.coverage_code
    for _, r in df_master.iterrows()
}

selected_names = st.multiselect(
    "Coverage Aktif",
    options=list(coverage_map.keys())
)

selected_codes = [coverage_map[n] for n in selected_names]

# =========================
# DEPENDENCY CHECK
# =========================
errors = check_dependency(selected_codes, df_master)
if errors:
    for e in errors:
        st.error(e)
    st.stop()

# =========================
# RATE CALCULATION
# =========================
st.subheader("Input Risiko & Perhitungan Rate")

rates = []
breakdown = []

for code in selected_codes:
    row = df_master[df_master.coverage_code == code].iloc[0]

    if row.rate_source == "flat":
        rate = 0.0
        rates.append(rate)
        breakdown.append((code, rate))
        continue

    sheet_name = row.rate_sheet

    if sheet_name not in sheets:
        st.error(f"Sheet rate '{sheet_name}' tidak ditemukan.")
        st.stop()

    df_rate = sheets[sheet_name]
    df_rate.columns = df_rate.columns.str.lower()

    risk_cols = [c for c in df_rate.columns if c != "rate"]
    risk_input = {}

    with st.expander(f"⚙️ {code}"):
        for c in risk_cols:
            risk_input[c] = st.selectbox(
                c.replace("_", " ").title(),
                df_rate[c].dropna().unique()
            )

    try:
        rate = lookup_rate(df_rate, risk_input) * float(row.weight)
    except ValueError as e:
        st.error(f"{code}: {e}")
        st.stop()

    rates.append(rate)
    breakdown.append((code, rate))

# =========================
# OUTPUT
# =========================
if rates:
    total_rate = sum(rates)

    st.subheader("Breakdown Rate")
    for c, r in breakdown:
        st.write(f"• **{c}** : {pct(r)}")

    st.subheader("Total Bundling Rate")
    st.metric("TOTAL RATE", pct(total_rate))
else:
    st.info("Silakan pilih minimal satu coverage.")

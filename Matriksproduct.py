import streamlit as st
from loader import load_excel
from engine import lookup_rate
from validator import check_dependency
from formatter import pct

# =====================
# CONFIG
# =====================
st.set_page_config(
    page_title="Bundling Rate Calculator",
    layout="wide"
)

st.title("📊 Bundling Rate Calculator")
st.caption("Generic Pricing Engine – Excel Driven")

FILE_PATH = "data/Template_Bundling_Rate_Streamlit_FULL.xlsx"

# =====================
# LOAD DATA
# =====================
sheets = load_excel(FILE_PATH)
df_master = sheets["COVERAGE_MASTER"]

df_master.columns = df_master.columns.str.lower()

df_master = df_master[df_master["active"] == 1]

# =====================
# COVERAGE SELECTION
# =====================
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

# =====================
# VALIDATION
# =====================
errors = check_dependency(selected_codes, df_master)
if errors:
    for e in errors:
        st.error(e)
    st.stop()

# =====================
# INPUT RISIKO (DYNAMIC)
# =====================
st.subheader("Input Risiko")

rates = []
breakdown = []

for code in selected_codes:
    row = df_master[df_master.coverage_code == code].iloc[0]

    if row.rate_source == "flat":
        rate = row.weight * 0
        rates.append(rate)
        breakdown.append((code, rate))
        continue

    df_rate = sheets[row.rate_sheet]
    df_rate.columns = df_rate.columns.str.lower()

    risk_cols = [c for c in df_rate.columns if c != "rate"]

    risk_input = {}

    with st.expander(f"⚙️ {code}"):
        for c in risk_cols:
            risk_input[c] = st.selectbox(
                f"{c.replace('_',' ').title()}",
                df_rate[c].dropna().unique()
            )

    rate = lookup_rate(df_rate, risk_input) * row.weight

    rates.append(rate)
    breakdown.append((code, rate))

# =====================
# OUTPUT
# =====================
if rates:
    total_rate = sum(rates)

    st.subheader("Breakdown Rate")

    for c, r in breakdown:
        st.write(f"- **{c}** : {pct(r)}")

    st.subheader("Total Bundling Rate")
    st.metric("TOTAL RATE", pct(total_rate))
else:
    st.info("Pilih minimal satu coverage.")

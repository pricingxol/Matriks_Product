import streamlit as st
import pandas as pd

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Bundling Rate Calculator",
    layout="wide"
)

st.title("📊 Bundling Rate Calculator")

# =====================================================
# LOAD DATA (CACHED)
# =====================================================
@st.cache_data(show_spinner="Loading rate matrix...")
def load_rate_matrix(path):
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()
    return df

df_rate = load_rate_matrix("rate_matrix_produk.xlsx")

# =====================================================
# CORE ENGINE (GENERIC & FUTURE-PROOF)
# =====================================================
def get_rate(df, coverage, subcover=None, selected_factors=None):

    if selected_factors is None:
        selected_factors = {}

    # Base filter
    q = df["Coverage"] == coverage

    if subcover:
        q &= df["Subcover"] == subcover

    # Dynamic factor filtering
    for col, val in selected_factors.items():
        if col not in df.columns:
            continue

        q &= (
            (df[col] == val) |
            (df[col].isna()) |
            (df[col] == "ALL")
        )

    result = df[q].copy()

    if result.empty:
        raise ValueError("Rate tidak ditemukan untuk kombinasi input tersebut")

    # Priority: paling spesifik (paling sedikit NaN)
    factor_cols = [
        c for c in df.columns
        if c not in ["Coverage", "Subcover", "Rate"]
    ]

    result["priority"] = result[factor_cols].isna().sum(axis=1)
    result = result.sort_values("priority")

    return float(result.iloc[0]["Rate"])


# =====================================================
# INPUT UI
# =====================================================
st.subheader("Input Risiko")

col1, col2 = st.columns(2)

with col1:
    coverage = st.selectbox(
        "Coverage",
        sorted(df_rate["Coverage"].dropna().unique())
    )

with col2:
    subcover_list = (
        df_rate[df_rate["Coverage"] == coverage]["Subcover"]
        .dropna()
        .unique()
    )

    subcover = None
    if len(subcover_list) > 0:
        subcover = st.selectbox("Subcover", sorted(subcover_list))

# Filter dataframe sesuai Coverage & Subcover
df_filtered = df_rate[df_rate["Coverage"] == coverage].copy()

if subcover:
    df_filtered = df_filtered[df_filtered["Subcover"] == subcover]

# =====================================================
# DYNAMIC FACTOR DROPDOWNS
# =====================================================
st.subheader("Faktor Risiko")

selected_factors = {}

factor_columns = [
    c for c in df_filtered.columns
    if c not in ["Coverage", "Subcover", "Rate"]
]

for col in factor_columns:

    values = (
        df_filtered[col]
        .dropna()
        .loc[~df_filtered[col].isin(["ALL"])]
        .unique()
    )

    if len(values) == 0:
        continue

    selected = st.selectbox(col, sorted(values))
    selected_factors[col] = selected


# =====================================================
# CALCULATION
# =====================================================
if st.button("Hitung Rate"):
    try:
        rate = get_rate(
            df=df_rate,
            coverage=coverage,
            subcover=subcover,
            selected_factors=selected_factors
        )

        st.success(f"✅ Rate ditemukan: **{rate:.4%}**")

    except Exception as e:
        st.error(str(e))


# =====================================================
# VIEW MATRIX (BOTTOM)
# =====================================================
st.divider()
st.subheader("📋 Rate Matrix (Read Only)")

st.dataframe(
    df_rate,
    use_container_width=True,
    hide_index=True
)

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
# CORE FUNCTION
# =====================================================
def get_rate(
    df,
    coverage,
    subcover=None,
    factor_1=None,
    factor_2=None,
    factor_3=None
):
    q = df["Coverage"] == coverage

    if subcover:
        q &= df["Subcover"] == subcover

    if factor_1 is not None:
        q &= (
            (df["Factor_1"] == factor_1) |
            (df["Factor_1"].isna()) |
            (df["Factor_1"] == "ALL")
        )

    if factor_2 is not None:
        q &= (
            (df["Factor_2"] == factor_2) |
            (df["Factor_2"].isna()) |
            (df["Factor_2"] == "ALL")
        )

    if factor_3 is not None:
        q &= (
            (df["Factor_3"] == factor_3) |
            (df["Factor_3"].isna()) |
            (df["Factor_3"] == "ALL")
        )

    result = df[q].copy()

    if result.empty:
        raise ValueError("Rate tidak ditemukan")

    # Prioritas paling spesifik
    result["priority"] = (
        result[["Factor_1", "Factor_2", "Factor_3"]]
        .isna()
        .sum(axis=1)
    )

    result = result.sort_values("priority")

    return float(result.iloc[0]["Rate"])


# =====================================================
# SIDEBAR INPUT
# =====================================================
st.sidebar.header("Input Risiko")

coverage = st.sidebar.selectbox(
    "Coverage",
    sorted(df_rate["Coverage"].dropna().unique())
)

subcover_list = (
    df_rate[df_rate["Coverage"] == coverage]["Subcover"]
    .dropna()
    .unique()
)

subcover = None
if len(subcover_list) > 0:
    subcover = st.sidebar.selectbox(
        "Subcover",
        sorted(subcover_list)
    )

factor_1 = st.sidebar.text_input("Factor 1 (mis: Kode Okupasi)")
factor_2 = st.sidebar.text_input("Factor 2 (mis: Kelas Konstruksi)")
factor_3 = st.sidebar.text_input("Factor 3 (mis: Zona Risiko)")

# =====================================================
# CALCULATION
# =====================================================
if st.sidebar.button("Hitung Rate"):
    try:
        rate = get_rate(
            df_rate,
            coverage=coverage,
            subcover=subcover,
            factor_1=factor_1 or None,
            factor_2=factor_2 or None,
            factor_3=factor_3 or None
        )

        st.success(f"✅ Rate ditemukan: **{rate:.4%}**")

    except Exception as e:
        st.error(str(e))

# =====================================================
# DEBUG (OPTIONAL)
# =====================================================
with st.expander("🔍 Lihat Rate Matrix"):
    st.dataframe(df_rate, use_container_width=True)

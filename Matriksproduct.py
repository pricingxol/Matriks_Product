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
# LOAD DATA
# =====================================================
@st.cache_data(show_spinner="Loading rate matrix...")
def load_rate_matrix(path):
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()
    return df

df_rate = load_rate_matrix("rate_matrix_produk.xlsx")

# =====================================================
# CORE ENGINE
# =====================================================
def get_rate(df, coverage, subcover=None, selected_factors=None):

    if selected_factors is None:
        selected_factors = {}

    q = df["Coverage"] == coverage

    if subcover:
        q &= df["Subcover"] == subcover

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
        raise ValueError("Rate tidak ditemukan")

    factor_cols = [
        c for c in df.columns
        if c not in ["Coverage", "Subcover", "Rate"]
    ]

    result["priority"] = result[factor_cols].isna().sum(axis=1)
    result = result.sort_values("priority")

    return float(result.iloc[0]["Rate"])


# =====================================================
# SESSION STATE INIT
# =====================================================
if "products" not in st.session_state:
    st.session_state.products = []

# =====================================================
# ADD PRODUCT FORM
# =====================================================
st.subheader("➕ Tambah Produk")

col1, col2 = st.columns(2)

with col1:
    coverage = st.selectbox(
        "Coverage",
        sorted(df_rate["Coverage"].dropna().unique()),
        key="new_coverage"
    )

with col2:
    subcover_list = (
        df_rate[df_rate["Coverage"] == coverage]["Subcover"]
        .dropna()
        .unique()
    )

    subcover = None
    if len(subcover_list) > 0:
        subcover = st.selectbox(
            "Subcover",
            sorted(subcover_list),
            key="new_subcover"
        )

df_filtered = df_rate[df_rate["Coverage"] == coverage].copy()
if subcover:
    df_filtered = df_filtered[df_filtered["Subcover"] == subcover]

st.markdown("**Faktor Risiko**")

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

    selected = st.selectbox(
        col,
        sorted(values),
        key=f"new_{col}"
    )

    selected_factors[col] = selected

# =====================================================
# ADD BUTTON
# =====================================================
if st.button("➕ Tambahkan ke Bundling"):
    try:
        rate = get_rate(
            df=df_rate,
            coverage=coverage,
            subcover=subcover,
            selected_factors=selected_factors
        )

        st.session_state.products.append({
            "Coverage": coverage,
            "Subcover": subcover,
            "Factors": selected_factors,
            "Rate": rate
        })

        st.success("Produk berhasil ditambahkan")

    except Exception as e:
        st.error(str(e))


# =====================================================
# BUNDLING TABLE
# =====================================================
st.divider()
st.subheader("📦 Daftar Produk Bundling")

if len(st.session_state.products) == 0:
    st.info("Belum ada produk yang dibundling")
else:
    rows = []
    total_rate = 0

    for i, p in enumerate(st.session_state.products):
        row = {
            "No": i + 1,
            "Coverage": p["Coverage"],
            "Subcover": p["Subcover"],
            "Rate": p["Rate"]
        }

        for k, v in p["Factors"].items():
            row[k] = v

        rows.append(row)
        total_rate += p["Rate"]

    df_bundle = pd.DataFrame(rows)
    st.dataframe(df_bundle, use_container_width=True)

    st.success(f"✅ **Total Bundling Rate: {total_rate:.4%}**")

# =====================================================
# RESET
# =====================================================
if st.button("🔄 Reset Bundling"):
    st.session_state.products = []
    st.experimental_rerun()


# =====================================================
# VIEW MATRIX
# =====================================================
st.divider()
st.subheader("📋 Rate Matrix (Read Only)")

st.dataframe(
    df_rate,
    use_container_width=True,
    hide_index=True
)

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
# CORE ENGINE (GENERIC)
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
            (df[col].astype(str) == str(val)) |
            (df[col].isna()) |
            (df[col] == "ALL")
        )

    result = df[q].copy()

    if result.empty:
        raise ValueError("Rate tidak ditemukan untuk kombinasi input tersebut")

    factor_cols = [
        c for c in df.columns
        if c not in ["Coverage", "Subcover", "Rate"]
    ]

    result["priority"] = result[factor_cols].isna().sum(axis=1)
    result = result.sort_values("priority")

    return float(result.iloc[0]["Rate"])


# =====================================================
# SESSION STATE
# =====================================================
if "products" not in st.session_state:
    st.session_state.products = []

# =====================================================
# INPUT PRODUK (HORIZONTAL)
# =====================================================
st.subheader("➕ Tambah Produk")

coverage = st.selectbox(
    "Coverage",
    sorted(df_rate["Coverage"].dropna().unique())
)

subcover_options = (
    df_rate[df_rate["Coverage"] == coverage]["Subcover"]
    .dropna()
    .unique()
)

cols = st.columns(max(1, len(st.session_state.products) + 1))

with cols[0]:
    new_subcover = st.selectbox(
        "Subcover",
        sorted(subcover_options),
        key="new_subcover"
    )

for i, p in enumerate(st.session_state.products):
    with cols[i + 1]:
        st.selectbox(
            "Subcover",
            [p["Subcover"]],
            disabled=True,
            key=f"locked_subcover_{i}"
        )

# =====================================================
# FAKTOR RISIKO (UNTUK PRODUK BARU)
# =====================================================
df_filtered = df_rate[
    (df_rate["Coverage"] == coverage) &
    (df_rate["Subcover"] == new_subcover)
]

st.subheader("Faktor Risiko")

selected_factors = {}

for col in df_filtered.columns:
    if col in ["Coverage", "Subcover", "Rate"]:
        continue

    values = (
        df_filtered[col]
        .dropna()
        .loc[~df_filtered[col].isin(["ALL"])]
        .astype(str)
        .unique()
    )

    if len(values) == 0:
        continue

    selected_factors[col] = st.selectbox(col, sorted(values))

# =====================================================
# ADD PRODUCT
# =====================================================
if st.button("➕ Tambah Produk"):
    try:
        rate = get_rate(
            df=df_rate,
            coverage=coverage,
            subcover=new_subcover,
            selected_factors=selected_factors
        )

        st.session_state.products.append({
            "Coverage": coverage,
            "Subcover": new_subcover,
            "Factors": selected_factors,
            "Rate": rate
        })

        st.success("Produk berhasil ditambahkan")
        st.experimental_rerun()

    except Exception as e:
        st.error(str(e))

# =====================================================
# BUNDLING RESULT
# =====================================================
st.divider()
st.subheader("📦 Bundling Product")

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
    st.dataframe(df_bundle, use_container_width=True, hide_index=True)

    st.success(f"✅ **Total Bundling Rate: {total_rate:.4%}**")

    # =================================================
    # CATATAN / DISCLAIMER (REQUEST KAMU)
    # =================================================
    st.warning(
        """
        **Catatan:**
        1. Maksimum akuisisi adalah **20%**, kecuali terdapat ketentuan lain dari **Regulator**.
        2. Untuk pemberian **rate di bawah rate acuan**, dapat dilakukan **perhitungan profitability checking**.
        """
    )

# =====================================================
# RESET
# =====================================================
if st.button("🔄 Reset Bundling"):
    st.session_state.products = []
    st.experimental_rerun()

# =====================================================
# VIEW RATE MATRIX
# =====================================================
st.divider()
st.subheader("📋 Rate Matrix (Read Only)")

st.dataframe(
    df_rate,
    use_container_width=True,
    hide_index=True
)

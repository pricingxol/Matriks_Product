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
def get_rate(df, coverage, subcover=None, f1=None, f2=None, f3=None):

    q = df["Coverage"] == coverage

    if subcover:
        q &= df["Subcover"] == subcover

    for col, val in zip(
        ["Factor_1", "Factor_2", "Factor_3"],
        [f1, f2, f3]
    ):
        if val is not None:
            q &= (
                (df[col] == val) |
                (df[col].isna()) |
                (df[col] == "ALL")
            )

    result = df[q].copy()

    if result.empty:
        raise ValueError("Rate tidak ditemukan untuk kombinasi tersebut")

    result["priority"] = (
        result[["Factor_1", "Factor_2", "Factor_3"]]
        .isna()
        .sum(axis=1)
    )

    result = result.sort_values("priority")

    return float(result.iloc[0]["Rate"])


# =====================================================
# MAIN INPUT UI
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
        subcover = st.selectbox(
            "Subcover",
            sorted(subcover_list)
        )

# Filter dataframe sesuai coverage & subcover
df_filtered = df_rate.copy()
df_filtered = df_filtered[df_filtered["Coverage"] == coverage]

if subcover:
    df_filtered = df_filtered[df_filtered["Subcover"] == subcover]

# =====================================================
# DYNAMIC FACTOR DROPDOWNS (SAFE)
# =====================================================
f1 = f2 = f3 = None

factor_config = [
    ("Factor_1", "Factor 1 (mis: Kode Okupasi)"),
    ("Factor_2", "Factor 2 (mis: Kelas Konstruksi)"),
    ("Factor_3", "Factor 3 (mis: Zona Risiko)")
]

for col, label in factor_config:

    # 🔒 SAFETY CHECK: kolom harus ada
    if col not in df_filtered.columns:
        continue

    values = (
        df_filtered[col]
        .dropna()
        .loc[~df_filtered[col].isin(["ALL"])]
        .unique()
    )

    # 🔒 SAFETY CHECK: harus ada value
    if len(values) == 0:
        continue

    selected = st.selectbox(label, sorted(values))

    if col == "Factor_1":
        f1 = selected
    elif col == "Factor_2":
        f2 = selected
    elif col == "Factor_3":
        f3 = selected


# =====================================================
# CALCULATION
# =====================================================
if st.button("Hitung Rate"):
    try:
        rate = get_rate(
            df_rate,
            coverage=coverage,
            subcover=subcover,
            f1=f1,
            f2=f2,
            f3=f3
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

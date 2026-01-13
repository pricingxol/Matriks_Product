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
def get_rate(df, coverage, subcover, selected_factors):

    q = (df["Coverage"] == coverage) & (df["Subcover"] == subcover)

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
        raise ValueError(f"Rate tidak ditemukan: {coverage} - {subcover}")

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
    st.session_state.products = [{}]

if "results" not in st.session_state:
    st.session_state.results = None


# =====================================================
# INPUT PRODUK (BARIS)
# =====================================================
st.subheader("Input Produk")

coverage_list = sorted(df_rate["Coverage"].dropna().unique())

for i, p in enumerate(st.session_state.products):

    st.markdown(f"### Produk {i + 1}")

    col1, col2, col3 = st.columns([3, 3, 1])

    with col1:
        p["Coverage"] = st.selectbox(
            "Coverage",
            coverage_list,
            key=f"coverage_{i}"
        )

    subcover_options = (
        df_rate[df_rate["Coverage"] == p["Coverage"]]["Subcover"]
        .dropna()
        .unique()
    )

    with col2:
        p["Subcover"] = st.selectbox(
            "Subcover",
            sorted(subcover_options),
            key=f"subcover_{i}"
        )

    with col3:
        if len(st.session_state.products) > 1:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.products.pop(i)
                st.session_state.results = None
                st.rerun()

    # =========================
    # Faktor Risiko
    # =========================
    df_filt = df_rate[
        (df_rate["Coverage"] == p["Coverage"]) &
        (df_rate["Subcover"] == p["Subcover"])
    ]

    factors = {}

    for col in df_filt.columns:
        if col in ["Coverage", "Subcover", "Rate"]:
            continue

        values = (
            df_filt[col]
            .dropna()
            .loc[~df_filt[col].isin(["ALL"])]
            .astype(str)
            .unique()
        )

        if len(values) == 0:
            continue

        factors[col] = st.selectbox(
            col,
            sorted(values),
            key=f"{col}_{i}"
        )

    p["Factors"] = factors

    st.divider()


# =====================================================
# TAMBAH PRODUK
# =====================================================
if st.button("➕ Tambah Produk"):
    st.session_state.products.append({})
    st.session_state.results = None
    st.rerun()


# =====================================================
# VALIDATION FUNCTION
# =====================================================
def validate_inputs(products):
    for idx, p in enumerate(products, start=1):
        if not p.get("Coverage"):
            return False, f"Produk {idx}: Coverage belum dipilih"
        if not p.get("Subcover"):
            return False, f"Produk {idx}: Subcover belum dipilih"
        if not p.get("Factors"):
            return False, f"Produk {idx}: Faktor risiko belum lengkap"
    return True, None


# =====================================================
# HITUNG RATE
# =====================================================
if st.button("Hitung Rate"):

    valid, msg = validate_inputs(st.session_state.products)

    if not valid:
        st.error(f"❌ {msg}")
    else:
        results = []
        total_rate = 0

        try:
            for p in st.session_state.products:
                rate = get_rate(
                    df_rate,
                    p["Coverage"],
                    p["Subcover"],
                    p["Factors"]
                )

                results.append({
                    "Coverage": p["Coverage"],
                    "Subcover": p["Subcover"],
                    **p["Factors"],
                    "Rate": rate
                })

                total_rate += rate

            st.session_state.results = (results, total_rate)

        except Exception as e:
            st.error(str(e))


# =====================================================
# OUTPUT (ONLY AFTER HITUNG RATE)
# =====================================================
if st.session_state.results:

    results, total_rate = st.session_state.results

    st.subheader("Bundling Product")

    df_out = pd.DataFrame(results)
    df_out.insert(0, "No", range(1, len(df_out) + 1))

    st.dataframe(df_out, use_container_width=True, hide_index=True)

    st.success(f"✅ **Total Bundling Rate: {total_rate:.4%}**")

    st.warning(
        """
        **Catatan:**
        1. Maksimum akuisisi adalah **20%**, kecuali terdapat ketentuan dari **Regulator**.
        2. Untuk pemberian **rate di bawah rate acuan**, dapat dilakukan **perhitungan profitability checking**.
        """
    )

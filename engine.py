def lookup_rate(df_rate, risk_input: dict):
    df = df_rate.copy()

    for col, val in risk_input.items():
        if col in df.columns:
            df = df[df[col] == val]

    if df.empty:
        raise ValueError("Rate tidak ditemukan untuk kombinasi risiko ini")

    return float(df.iloc[0]["rate"])

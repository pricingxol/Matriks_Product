def check_dependency(selected, df_master):
    errors = []

    for _, row in df_master.iterrows():
        if row["coverage_code"] in selected and isinstance(row["dependency"], str):
            dep = row["dependency"].strip()
            if dep and dep not in selected:
                errors.append(
                    f"Coverage {row['coverage_code']} membutuhkan {dep}"
                )
    return errors

import pandas as pd
import streamlit as st

@st.cache_data
def load_excel(path):
    xls = pd.ExcelFile(path)
    sheets = {s: pd.read_excel(xls, s) for s in xls.sheet_names}
    return sheets

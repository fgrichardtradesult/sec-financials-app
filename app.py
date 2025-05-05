import streamlit as st
import pandas as pd
import requests
import time

HEADERS = {
    "User-Agent": "Francois-Guy Richard (fgrichard@tradesult.com)"
}

def fetch_company_facts(cik):
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

def extract_financials(data, cik):
    if not data:
        return []

    results = []
    units = data.get("facts", {}).get("us-gaap", {})
    common_metrics = [
        "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
        "NetIncomeLoss", "OperatingIncomeLoss", "GrossProfit", "EarningsPerShareBasic",
        "EarningsPerShareDiluted", "Assets", "Liabilities", "StockholdersEquity",
        "CashAndCashEquivalentsAtCarryingValue", "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInInvestingActivities", "NetCashProvidedByUsedInFinancingActivities"
    ]

    for metric in common_metrics:
        metric_data = units.get(metric, {}).get("units", {}).get("USD", [])
        if metric_data:
            latest = sorted(metric_data, key=lambda x: x["end"], reverse=True)[0]
            results.append({
                "CIK": cik,
                "Metric": metric,
                "Value": latest["val"],
                "Start": latest.get("start", ""),
                "End": latest.get("end", "")
            })
    return results

st.title("SEC Financial Data Extractor")
uploaded_file = st.file_uploader("Upload Excel with CIKs", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if "CIK" not in df.columns:
        st.error("Excel file must contain a column named 'CIK'.")
    else:
        ciks = df["CIK"].dropna().astype(str).str.zfill(10).unique().tolist()
        output_data = []

        with st.spinner("Fetching data from SEC..."):
            for cik in ciks:
                time.sleep(0.5)
                data = fetch_company_facts(cik)
                output_data.extend(extract_financials(data, cik))

        if output_data:
            df_out = pd.DataFrame(output_data)
            st.success("Data retrieved successfully!")
            st.dataframe(df_out)

            # Download link
            csv = df_out.to_csv(index=False).encode("utf-8")
            st.download_button("Download as CSV", csv, "financials.csv", "text/csv")

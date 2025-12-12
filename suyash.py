import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

st.set_page_config(layout="wide", page_title="Excel-like Viewer")

st.title("Excel-jaisa Data Viewer / Editor")

# Upload CSV
uploaded = st.file_uploader("Upload CSV (supports large files)", type=["csv"])

df = None
if uploaded is not None:
    df = pd.read_csv(uploaded)
else:
    if st.button("Load demo 200k rows"):
        n = 200_000
        df = pd.DataFrame({
            "id": range(1, n + 1),
            "name": [f"name_{i}" for i in range(1, n + 1)],
            "value": [i % 100 for i in range(1, n + 1)],
        })
    else:
        st.info("Upload a CSV or load demo to start.")
        st.stop()

# Build AG Grid options
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, resizable=True, filter=True, sortable=True)
gb.configure_selection(selection_mode="multiple", use_checkbox=True)
gb.configure_grid_options(enableRowGroup=True, enableRangeSelection=True)
gb.configure_grid_options(enableClipboard=True)
grid_opts = gb.build()

# Global search
st.markdown("*Search / Filter:* use column filters or global search below.")
query = st.text_input("Global search (searches all string fields):")
if query:
    mask = pd.Series(False, index=df.index)
    for c in df.select_dtypes(include=['object', 'string']).columns:
        mask = mask | df[c].astype(str).str.contains(query, case=False, na=False)
    display_df = df[mask]
else:
    display_df = df

# Show grid
grid_response = AgGrid(
    display_df,
    gridOptions=grid_opts,
    height=600,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=False,
    enable_enterprise_modules=False,
)

# Get edited dataframe and selected rows safely
updated_df = grid_response["data"]
selected = grid_response.get("selected_rows", []) or []

st.markdown(f"*Selected rows:* {len(selected)}")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Add blank row"):
        new = pd.DataFrame({c: [None] for c in updated_df.columns})
        updated_df = pd.concat([updated_df, new], ignore_index=True)
        st.experimental_rerun()

with col2:
    if st.button("Delete selected rows"):
        if selected:
            if "id" in updated_df.columns:
                sel_ids = {r.get("id") for r in selected if r.get("id") is not None}
                updated_df = updated_df[~updated_df["id"].isin(sel_ids)]
                st.success(f"Deleted {len(sel_ids)} rows")
            else:
                st.warning("No 'id' column found to identify rows")
            st.experimental_rerun()
        else:
            st.warning("No rows selected")

with col3:
    if st.button("Prepare download"):
        st.download_button(
            "Download current table as CSV",
            data=updated_df.to_csv(index=False).encode("utf-8"),
            file_name="edited_table.csv",
            mime="text/csv",
        )

st.markdown("*Tip:* Use checkboxes + Ctrl+C to copy rows. Paste into Excel/Google Sheets works.")
"""Streamlit dashboard: filterable table view of production logs.

This UI fetches production logs from the service layer, converts them to a
`pandas.DataFrame`, and provides sidebar filters (line, shift leader, date
range, shipped, defective, and lot search). The table is interactive and can
be sorted by selected columns. Selecting a row shows detailed information.

Design notes:
- To avoid placing DB logic in the UI, we call `services.list_production_logs`
  which returns ORM objects. We convert those to plain Python values and
  build a DataFrame for filtering and display.
- Time complexity: fetching logs is O(n) where n is number of logs requested.
  Filtering is O(n) per user interaction. Sorting is O(n log n).
- Space complexity: O(n) to store the DataFrame in memory for the session.
"""

from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import sentry_sdk
import os

from src.services import services


@st.cache_data(ttl=300)
def fetch_logs(limit: int = 1000) -> List[Any]:
    """Fetch production logs from the service layer and cache results.

    Caching prevents repeated DB hits during interactive filtering. TTL=300s
    controls staleness; adjust according to AC12 (timely access vs freshness).

    Complexity: O(n) to fetch and materialize rows.
    """
    return services.list_production_logs(limit=limit)


def logs_to_dataframe(logs: List[Any]) -> pd.DataFrame:
    """Convert ORM `ProductionLog` objects to a flat DataFrame suitable for
    filtering and display.

    Each row contains key reporting fields and aggregated inspection/shipping
    indicators to support the summary queries described in the user story.

    Complexity: O(n * m) where m is average number of inspections per log for
    computing defect counts; typically m << n.
    """
    rows: List[Dict[str, Any]] = []
    for log in logs:
        # Access relationships that were eager-loaded in services to avoid
        # DetachedInstanceError; compute aggregates in-memory.
        inspections = getattr(log, "inspections", []) or []
        shipping = getattr(log, "shipping_manifest", None)

        defect_count = sum(1 for i in inspections if getattr(i, "is_defective", False))
        any_defective = defect_count > 0

        rows.append(
            {
                "production_log_id": getattr(log, "production_log_id", None),
                "lot_number": getattr(log, "lot_number", None),
                "production_date": getattr(log, "production_date", None),
                "line_number": getattr(log, "line_number", None),
                "shift_leader": getattr(log, "shift_leader", None),
                "destination": getattr(shipping, "destination", None)
                if shipping
                else None,
                "is_shipped": getattr(shipping, "is_shipped", False)
                if shipping
                else False,
                "defect_count": defect_count,
                "is_defective": any_defective,
            }
        )

    df = pd.DataFrame(rows)
    # Ensure production_date is a datetime/date type for proper filtering
    if not df.empty and df["production_date"].dtype == object:
        df["production_date"] = pd.to_datetime(df["production_date"]).dt.date
    return df


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters, apply them to `df`, and return filtered DF.

    Filtering UI and logic live together for clarity; each control reduces the
    displayed rows interactively.
    """
    st.sidebar.header("Filters")

    load_dotenv()

    # Configure Sentry
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        send_default_pii=False,
        traces_sample_rate=0.0,
        enable_logs=False,
    )
    # division_by_zero = 1 / 0  # Intentional error to test Sentry integration

    # Date range filter
    if df.empty:
        st.sidebar.write("No data available")
        return df

    min_date = df["production_date"].min()
    max_date = df["production_date"].max()
    date_range = st.sidebar.date_input(
        "Production date range", value=(min_date, max_date)
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[(df["production_date"] >= start) & (df["production_date"] <= end)]

    # Line number filter (multi-select)
    lines = sorted(df["line_number"].dropna().unique().tolist())
    selected_lines = st.sidebar.multiselect("Line number", options=lines, default=lines)
    if selected_lines:
        df = df[df["line_number"].isin(selected_lines)]

    # Shift leader filter
    leaders = sorted(df["shift_leader"].dropna().unique().tolist())
    leader = st.sidebar.selectbox("Shift leader", options=["All"] + leaders)
    if leader and leader != "All":
        df = df[df["shift_leader"] == leader]

    # Shipped filter
    shipped = st.sidebar.selectbox(
        "Shipped status", options=["All", "Shipped", "Not shipped"]
    )
    if shipped == "Shipped":
        df = df[df["is_shipped"]]
    elif shipped == "Not shipped":
        df = df[~df["is_shipped"]]

    # Defective filter
    defective = st.sidebar.selectbox(
        "Defective", options=["All", "Defective", "No defects"]
    )
    if defective == "Defective":
        df = df[df["is_defective"]]
    elif defective == "No defects":
        df = df[~df["is_defective"]]

    # Lot search
    search = st.sidebar.text_input("Search lot number")
    if search:
        df = df[df["lot_number"].str.contains(search, case=False, na=False)]

    return df


def main():

    st.set_page_config(page_title="Production Dashboard", layout="wide")
    st.title("Production Dashboard")

    logs = fetch_logs(limit=1000)
    df = logs_to_dataframe(logs)

    st.sidebar.markdown("Data rows: **%d**" % len(df))

    filtered = apply_filters(df)

    # Sorting control
    if not filtered.empty:
        sort_by = st.selectbox(
            "Sort by",
            options=["production_date", "line_number", "defect_count", "lot_number"],
            index=0,
        )
        ascending = st.checkbox("Ascending", value=False)
        try:
            filtered = filtered.sort_values(by=sort_by, ascending=ascending)
        except Exception:
            # Fail-safe: ignore sort if column missing or wrong type
            pass

    st.subheader("Production Logs Table")
    # Display as an interactive table; uses Streamlit's optimized renderer.
    st.dataframe(filtered)

    # Row detail: allow selecting a production_log_id to show inspections
    selected_id = st.selectbox(
        "Select production_log_id to show details",
        options=[None] + filtered["production_log_id"].tolist(),
    )
    if selected_id:
        detail = services.get_production_log_by_id(selected_id)
        if detail:
            st.subheader(f"Details for {detail.lot_number}")
            st.write("Line:", detail.line_number)
            st.write("Shift leader:", detail.shift_leader)
            st.write("Production date:", detail.production_date)
            if detail.shipping_manifest:
                st.write(
                    "Shipping:",
                    detail.shipping_manifest.destination,
                    "Shipped:",
                    detail.shipping_manifest.is_shipped,
                )
            inspections = services.list_inspections_for_log(detail.production_log_id)
            st.write("Inspections:")
            for ins in inspections:
                st.write(
                    f"- {ins.defect_type or 'None'} | Severity: {ins.defect_severity or 'N/A'} | Defective: {ins.is_defective}"
                )


if __name__ == "__main__":
    main()

"""ETL functions to ingest and consolidate spreadsheets into a unified
`pandas.DataFrame` representation.

This module provides helpers to:
 - read CSV/Excel files (production, quality, shipping)
 - align records by lot id and date
 - flag missing or inconsistent records
 - produce consolidated summaries suitable for reporting
 - filter/sort consolidated data and detect simple trend anomalies

Each function includes complexity notes and ensures resources (file handles)
are closed by relying on pandas' IO facilities.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def read_production_files(paths: List[str]) -> pd.DataFrame:
    """Read multiple production CSV/Excel files and concatenate them.

    Assumes each file contains at least: `lot_number`, `line_number`,
    `production_date`, `shift_leader`.

    Time complexity: O(n) where n is total rows across files.
    Space complexity: O(n) for the concatenated DataFrame.
    """
    frames = []
    for p in paths:
        if p.lower().endswith(".csv"):
            df = pd.read_csv(p)
        else:
            df = pd.read_excel(p)
        frames.append(df)
    if frames:
        return pd.concat(frames, ignore_index=True)
    else:
        return pd.DataFrame()


def consolidate_data(
    production: pd.DataFrame, quality: pd.DataFrame, shipping: pd.DataFrame
) -> pd.DataFrame:
    """Consolidate production, quality, and shipping tables into a single
    DataFrame keyed by `lot_number` and `production_date`.

    Rules implemented:
    - Left join production -> quality and production -> shipping so production
      rows are preserved.
    - Flag rows with mismatched or missing lot numbers.
    - Exclude rows that lack essential fields (AC4).

    Time complexity: O(n log n) for merges and sorts, dominated by DataFrame
    merge operations. Space complexity: O(n).
    """
    # Normalize column names to lower-case for robustness
    production = production.rename(columns=str.lower)
    quality = quality.rename(columns=str.lower)
    shipping = shipping.rename(columns=str.lower)

    # Ensure required fields exist
    required = {"lot_number", "production_date"}
    if not required.issubset(set(production.columns)):
        raise ValueError("Production data missing required columns")

    # Perform merges
    merged = production.merge(
        quality,
        how="left",
        on=["lot_number", "production_date"],
        suffixes=("", "_quality"),
    )
    merged = merged.merge(
        shipping,
        how="left",
        on=["lot_number", "production_date"],
        suffixes=("", "_shipping"),
    )

    # Flag missing or inconsistent data (AC3, AC9)
    merged["flag_missing_quality"] = merged.get("defect_type").isna()
    merged["flag_missing_shipping"] = merged.get("destination").isna()

    # Exclude irrelevant or incomplete (AC4): require lot_number and production_date
    merged = merged.dropna(subset=["lot_number", "production_date"])

    return merged


def summary_metrics(consolidated: pd.DataFrame) -> pd.DataFrame:
    """Produce summary metrics such as defect counts, issues per line, and
    shipped batches (AC5, AC6).

    Returns a DataFrame grouped by line_number with counts and defect rates.

    Time complexity: O(n) for groupby operations. Space complexity: O(k) for
    resulting grouped rows, where k is number of lines.
    """
    df = consolidated.copy()
    # Treat NaN in is_defective as False for metrics (where() avoids fillna FutureWarning)
    if "is_defective" in df.columns:
        ser = df["is_defective"]
        df["is_defective_bool"] = ser.where(ser.notna(), False).astype(bool)
    else:
        df["is_defective_bool"] = False

    grouped = (
        df.groupby("line_number")
        .agg(
            total_lots=("lot_number", "nunique"),
            defect_count=("is_defective_bool", "sum"),
            shipped_count=("is_shipped", lambda s: s.fillna(False).astype(bool).sum()),
        )
        .reset_index()
    )
    grouped["defect_rate"] = grouped["defect_count"] / grouped["total_lots"]
    return grouped


def filter_and_sort(
    consolidated: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None,
    ascending: bool = True,
) -> pd.DataFrame:
    """Return a filtered and sorted view of the consolidated DataFrame (AC7).

    - `filters` is a dict mapping column->value. Values can be list for inclusion.
    - `sort_by` is a column name to sort on.

    Time complexity: O(n) for filtering and O(n log n) for sorting. Space: O(n).
    """
    df = consolidated.copy()
    if filters:
        for col, val in filters.items():
            if isinstance(val, (list, tuple, set)):
                df = df[df[col].isin(val)]
            else:
                df = df[df[col] == val]
    if sort_by and sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    return df


def detect_trends(
    consolidated: pd.DataFrame, group_by: str = "line_number"
) -> pd.DataFrame:
    """Detect simple anomalies/trends by computing defect rates and flagging
    groups with unusually high defect rates (AC6).

    Algorithm: compute defect_rate per group and flag as anomaly if
    defect_rate > mean(defect_rate) + 2 * std(defect_rate).

    Time complexity: O(n) for groupby and statistics. Space complexity: O(k).
    """
    metrics = summary_metrics(consolidated)
    # Defensive: if only one group, std is NaN; no anomalies unless rate > mean
    mean_rate = metrics["defect_rate"].mean()
    std_rate = metrics["defect_rate"].std(ddof=0) if len(metrics) > 1 else 0.0
    threshold = mean_rate + 2 * (std_rate if not np.isnan(std_rate) else 0.0)
    metrics["is_anomaly"] = metrics["defect_rate"] > threshold
    return metrics

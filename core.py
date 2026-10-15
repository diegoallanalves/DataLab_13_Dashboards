"""Reusable, testable data operations for the DataLab 13 portfolio."""
from __future__ import annotations
import io
import sqlite3
import pandas as pd
import numpy as np


def sample_data(n: int = 240, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    segment = rng.choice(['Starter', 'Growth', 'Enterprise'], n, p=[.45, .4, .15])
    region = rng.choice(['Brazil', 'UK', 'USA', 'Germany'], n)
    spend = np.round(rng.gamma(3, 70, n), 2)
    visits = rng.integers(1, 28, n)
    probability = np.clip(.06 + visits * .014 + (segment == 'Enterprise') * .18, 0, .85)
    converted = rng.binomial(1, probability)
    return pd.DataFrame({'customer_id': range(1, n + 1), 'segment': segment,
        'region': region, 'spend': spend, 'visits': visits, 'converted': converted,
        'order_date': pd.date_range('2026-01-01', periods=n, freq='D')})


def quality_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name in df.columns:
        rows.append({'column': name, 'dtype': str(df[name].dtype),
            'nulls': int(df[name].isna().sum()), 'null_pct': round(df[name].isna().mean() * 100, 2),
            'distinct': int(df[name].nunique(dropna=True))})
    return pd.DataFrame(rows)


def clean_data(df: pd.DataFrame, drop_duplicates=True, strip_text=True) -> pd.DataFrame:
    out = df.copy()
    if strip_text:
        for col in out.select_dtypes(include='object').columns:
            out[col] = out[col].map(lambda x: x.strip() if isinstance(x, str) else x)
    if drop_duplicates:
        out = out.drop_duplicates()
    return out.reset_index(drop=True)


def customer_metrics(df: pd.DataFrame) -> pd.DataFrame:
    needed = {'segment', 'spend', 'converted'}
    if not needed.issubset(df.columns):
        raise ValueError('Dataset requires segment, spend, and converted columns')
    return df.groupby('segment', dropna=False).agg(customers=('converted', 'size'),
        revenue=('spend', 'sum'), conversions=('converted', 'sum'),
        conversion_rate=('converted', 'mean')).reset_index()


def uplift(test_conversions: int, test_total: int, control_conversions: int, control_total: int) -> dict:
    if min(test_total, control_total) <= 0 or min(test_conversions, control_conversions) < 0:
        raise ValueError('Totals must be positive and conversions non-negative')
    if test_conversions > test_total or control_conversions > control_total:
        raise ValueError('Conversions cannot exceed total observations')
    t = test_conversions / test_total
    c = control_conversions / control_total
    return {'test_rate': t, 'control_rate': c, 'absolute_lift_pp': (t-c)*100,
        'relative_uplift_pct': ((t-c)/c*100) if c else None}


def persist_sqlite(df: pd.DataFrame, db_path: str, table: str = 'customer_events') -> int:
    with sqlite3.connect(db_path) as conn:
        return int(df.to_sql(table, conn, if_exists='replace', index=False))


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')


def read_uploaded(upload) -> pd.DataFrame:
    if upload.name.lower().endswith('.csv'):
        return pd.read_csv(upload)
    if upload.name.lower().endswith('.json'):
        return pd.read_json(upload)
    raise ValueError('Only CSV and JSON supported in this starter')

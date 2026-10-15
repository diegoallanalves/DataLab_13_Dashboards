import sqlite3
import pandas as pd
import pytest
from core import sample_data, quality_report, clean_data, customer_metrics, uplift, persist_sqlite

def test_sample_reproducible():
    assert sample_data(10).equals(sample_data(10))

def test_quality_report():
    df = pd.DataFrame({'a': [1, None, 3]})
    assert quality_report(df).iloc[0]['nulls'] == 1

def test_clean_data():
    df = pd.DataFrame({'name': [' A ', ' A ', 'B']})
    assert clean_data(df)['name'].tolist() == ['A', 'B']

def test_metrics():
    assert customer_metrics(sample_data(30))['customers'].sum() == 30

def test_uplift():
    result = uplift(80, 1000, 50, 1000)
    assert result['absolute_lift_pp'] == pytest.approx(3)
    assert result['relative_uplift_pct'] == pytest.approx(60)

def test_uplift_rejects_bad_counts():
    with pytest.raises(ValueError): uplift(12, 10, 5, 10)

def test_sqlite(tmp_path):
    path = str(tmp_path / 'test.db')
    assert persist_sqlite(sample_data(7), path) == 7
    with sqlite3.connect(path) as conn:
        assert conn.execute('select count(*) from customer_events').fetchone()[0] == 7

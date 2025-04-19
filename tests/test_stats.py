import os
import sqlite3
import datetime
import importlib
import sys
import io
import pytest

def test_stats_main(tmp_path, monkeypatch, capsys):
    # Setup a temporary SQLite DB
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_file}")
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    # Create actions table and insert sample data
    cur.execute("CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY, date TEXT, type TEXT, success INTEGER)")
    today = datetime.date.today().isoformat()
    sample = [
        (today, 'invite', 1),
        (today, 'invite', 0),
        (today, 'like', 1),
        (today, 'comment', 1),
    ]
    for date, typ, success in sample:
        cur.execute("INSERT INTO actions(date, type, success) VALUES(?,?,?)", (date, typ, success))
    conn.commit()
    conn.close()

    # Reload stats module to pick up new env
    import stats as stats_module
    importlib.reload(stats_module)

    # Capture output
    stats_module.main()
    captured = capsys.readouterr()
    out = captured.out
    # Check counts
    assert 'invites: 2' in out
    assert 'likes: 1' in out
    assert 'comments: 1' in out
    # Check success rate
    assert 'Success rate: 75.00%' in out
    # Check recent actions table header
    assert 'Recent actions' in out 
import os
import sqlite3
import datetime
import importlib
import pytest
# Import the refactored orchestrator
from orchestrator import setup_db, caps_remaining, within_active_block


def test_caps_remaining(tmp_path, monkeypatch):
    # Setup temporary DB
    db_file = tmp_path / "orch_test.db"
    # Define test caps dictionary
    test_caps = {'invites': 30, 'likes': 40, 'comments': 12}
    # Ensure actions table exists
    conn = setup_db(str(db_file)) # Use setup_db
    cur = conn.cursor()
    # Insert entries equal to invite cap
    today = datetime.date.today().isoformat()
    cap = test_caps.get('invites', 0) # Use the test cap value
    for _ in range(cap):
        cur.execute("INSERT INTO actions(date, type, success) VALUES(?,?,?)", (today, 'invite', 1))
    conn.commit()
    # Should not allow invites when at cap (pass test_caps and fast_test_mode=False)
    assert caps_remaining(conn, 'invites', caps=test_caps, fast_test_mode=False) is False
    # Should allow invites when FAST_TEST=True, even at cap
    assert caps_remaining(conn, 'invites', caps=test_caps, fast_test_mode=True) is True
    # Remove one entry and test again (pass test_caps and fast_test_mode=False)
    cur.execute("DELETE FROM actions WHERE type='invite' LIMIT 1")
    conn.commit()
    assert caps_remaining(conn, 'invites', caps=test_caps, fast_test_mode=False) is True
    conn.close()


def test_within_active_block(monkeypatch):
    # Create a block covering current time
    now = datetime.datetime.now()
    start = (now - datetime.timedelta(minutes=1)).time()
    end = (now + datetime.timedelta(minutes=1)).time()
    monkeypatch.setattr("orchestrator.blocks", [(start, end)])
    assert within_active_block() is True
    # Create a block far in the past
    monkeypatch.setattr("orchestrator.blocks", [(datetime.time(0, 0), datetime.time(0, 1))])
    assert within_active_block() is False 
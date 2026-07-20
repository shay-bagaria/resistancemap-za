"""Tests for audit/log.py: chain verification and tamper detection (§13.2)."""
import sqlite3

from resistancemap.audit import log


def _fresh_conn():
    return log.connect(":memory:")


def _append_sample(conn, n=3):
    rows = []
    for i in range(n):
        rows.append(log.append_entry(
            conn,
            timestamp_utc=f"2026-01-0{i + 1}T00:00:00Z",
            patient_ref=f"PT-{i}",
            clinician_ref="DR-TEST",
            facility_code="TEST-FAC",
            inputs={"days_missed": i},
            outputs={"state": "FULL_SUPPRESSION"},
            ruleset_version="0.5.0",
            data_hashes={"drugs.yaml": "abc123"},
        ))
    return rows


def test_append_creates_valid_chain():
    conn = _fresh_conn()
    rows = _append_sample(conn, 3)
    assert [r["seq"] for r in rows] == [1, 2, 3]
    assert rows[0]["prev_hash"] == log.GENESIS_HASH
    assert rows[1]["prev_hash"] == rows[0]["entry_hash"]
    assert rows[2]["prev_hash"] == rows[1]["entry_hash"]


def test_verify_chain_ok_on_untouched_log():
    conn = _fresh_conn()
    _append_sample(conn, 5)
    ok, bad_seq = log.verify_chain(conn)
    assert ok is True
    assert bad_seq is None


def test_verify_chain_empty_log_is_ok():
    conn = _fresh_conn()
    ok, bad_seq = log.verify_chain(conn)
    assert ok is True
    assert bad_seq is None


def test_mutating_a_middle_row_is_detected():
    conn = _fresh_conn()
    _append_sample(conn, 5)
    # Directly tamper with row 3's inputs_json, bypassing the append-only API,
    # the way an actor with raw write access to the database file could.
    conn.execute("UPDATE audit_log SET inputs_json = ? WHERE seq = 3",
                 ('{"days_missed": 999}',))
    conn.commit()
    ok, bad_seq = log.verify_chain(conn)
    assert ok is False
    assert bad_seq == 3


def test_mutating_the_last_row_is_detected():
    conn = _fresh_conn()
    _append_sample(conn, 4)
    conn.execute("UPDATE audit_log SET patient_ref = 'TAMPERED' WHERE seq = 4")
    conn.commit()
    ok, bad_seq = log.verify_chain(conn)
    assert ok is False
    assert bad_seq == 4


def test_deterministic_hash_for_same_input():
    entry = {"a": 1, "b": 2}
    h1 = log.chain_entry(log.GENESIS_HASH, entry)
    h2 = log.chain_entry(log.GENESIS_HASH, entry)
    assert h1 == h2
    assert len(h1) == 64

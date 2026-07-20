"""Append-only audit log with a SHA-256 hash chain (methodology section 13.2).

Real cryptography, genuinely append-only SQLite storage. This replaces the
v4.0 `f"SHA256:{abs(hash(x)):#x}"` — Python's built-in hash() is non-cryptographic
and randomised per process by PYTHONHASHSEED, so the same input produced a
different value on every restart, and the "log" was rebuilt from scratch on
every rerun with synthetic `now - N seconds` timestamps rather than persisted.

This gives tamper EVIDENCE, not tamper PROOFING: altering any stored row
invalidates every entry_hash computed after it, which verify_chain() detects.
It does not prevent an actor with write access to the database from rebuilding
the whole chain from that point forward with self-consistent hashes. Genuine
tamper resistance would require publishing the chain head somewhere outside
this system's control (methodology section 13.2).
"""

import hashlib
import json
import sqlite3

GENESIS_HASH = "0" * 64

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    seq            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc  TEXT NOT NULL,
    patient_ref    TEXT NOT NULL,
    clinician_ref  TEXT NOT NULL,
    facility_code  TEXT NOT NULL,
    inputs_json    TEXT NOT NULL,
    outputs_json   TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    data_hashes    TEXT NOT NULL,
    prev_hash      TEXT NOT NULL,
    entry_hash     TEXT NOT NULL
);
"""


def chain_entry(prev_hash, entry):
    """SHA-256(prev_hash + canonical JSON of entry). See module docstring."""
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + payload).encode("utf-8")).hexdigest()


def connect(db_path):
    """Open (creating if necessary) the append-only audit database."""
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def _last_hash(conn):
    row = conn.execute(
        "SELECT entry_hash FROM audit_log ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else GENESIS_HASH


def append_entry(conn, *, timestamp_utc, patient_ref, clinician_ref, facility_code,
                  inputs, outputs, ruleset_version, data_hashes):
    """Append one assessment row to the chain. Returns the inserted row as a dict.

    inputs/outputs/data_hashes may be dicts (serialised to canonical JSON) or
    already-serialised strings.
    """
    def _json(v):
        return v if isinstance(v, str) else json.dumps(v, sort_keys=True, separators=(",", ":"))

    prev_hash = _last_hash(conn)
    fields = {
        "timestamp_utc": timestamp_utc,
        "patient_ref": patient_ref,
        "clinician_ref": clinician_ref,
        "facility_code": facility_code,
        "inputs_json": _json(inputs),
        "outputs_json": _json(outputs),
        "ruleset_version": ruleset_version,
        "data_hashes": _json(data_hashes),
        "prev_hash": prev_hash,
    }
    entry_hash = chain_entry(prev_hash, fields)
    cur = conn.execute(
        """INSERT INTO audit_log
           (timestamp_utc, patient_ref, clinician_ref, facility_code,
            inputs_json, outputs_json, ruleset_version, data_hashes,
            prev_hash, entry_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (fields["timestamp_utc"], fields["patient_ref"], fields["clinician_ref"],
         fields["facility_code"], fields["inputs_json"], fields["outputs_json"],
         fields["ruleset_version"], fields["data_hashes"], prev_hash, entry_hash),
    )
    conn.commit()
    row = fields.copy()
    row["seq"] = cur.lastrowid
    row["entry_hash"] = entry_hash
    return row


def read_all(conn):
    """All rows, oldest first, as a list of dicts."""
    cols = ["seq", "timestamp_utc", "patient_ref", "clinician_ref", "facility_code",
            "inputs_json", "outputs_json", "ruleset_version", "data_hashes",
            "prev_hash", "entry_hash"]
    rows = conn.execute(f"SELECT {', '.join(cols)} FROM audit_log ORDER BY seq ASC").fetchall()
    return [dict(zip(cols, r)) for r in rows]


def verify_chain(conn):
    """Recompute every row's hash from its stored fields and check the chain.

    Returns (ok, first_bad_seq). ok is True iff every row's stored entry_hash
    matches SHA-256(prev_hash + canonical JSON of its own fields), and every
    row's stored prev_hash matches the previous row's stored entry_hash (or
    GENESIS_HASH for the first row). first_bad_seq is the seq of the first row
    that fails either check, or None if ok.
    """
    rows = read_all(conn)
    expected_prev = GENESIS_HASH
    for row in rows:
        if row["prev_hash"] != expected_prev:
            return False, row["seq"]
        fields = {k: row[k] for k in
                  ("timestamp_utc", "patient_ref", "clinician_ref", "facility_code",
                   "inputs_json", "outputs_json", "ruleset_version", "data_hashes",
                   "prev_hash")}
        recomputed = chain_entry(row["prev_hash"], fields)
        if recomputed != row["entry_hash"]:
            return False, row["seq"]
        expected_prev = row["entry_hash"]
    return True, None

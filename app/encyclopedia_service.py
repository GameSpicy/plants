"""Read-only query helpers for the shared plant encyclopedia."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.encyclopedia_db import ENCYCLOPEDIA_DB_PATH


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or ENCYCLOPEDIA_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def _sources(conn: sqlite3.Connection, content_type: str, content_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT s.id, s.title, s.publisher, s.author, s.url, s.publication_date,
                  s.accessed_at, s.source_type, cr.claim
           FROM content_references cr
           JOIN sources s ON s.id=cr.reference_id
           WHERE cr.content_type=? AND cr.content_id=?
           ORDER BY s.publisher, s.title""",
        (content_type, content_id),
    ).fetchall()
    return [dict(row) for row in rows]


def _treatments(conn: sqlite3.Connection, table: str, key: str, content_id: str) -> list[dict[str, Any]]:
    # table/key are fixed internal identifiers selected only by this module.
    rows = conn.execute(
        f"""SELECT t.* FROM {table} link
            JOIN treatments t ON t.id=link.treatment_id
            WHERE link.{key}=? AND t.review_status != 'retired'
            ORDER BY link.sequence, t.title""",
        (content_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def list_problems(kind: str, q: str = "", limit: int = 50, path=None) -> list[dict[str, Any]]:
    if kind not in {"pests", "diseases"}:
        raise ValueError("Unsupported encyclopedia content type")
    conn = connect(path)
    try:
        if kind == "pests":
            fields = ("common_name", "scientific_name", "description", "symptoms")
        else:
            fields = ("common_name", "causal_agent", "description", "symptoms")
        where = "review_status != 'retired'"
        args: list[Any] = []
        if q.strip():
            where += " AND (" + " OR ".join(f"{field} LIKE ?" for field in fields) + ")"
            args.extend([f"%{q.strip()}%"] * len(fields))
        rows = conn.execute(
            f"SELECT * FROM {kind} WHERE {where} ORDER BY common_name COLLATE NOCASE LIMIT ?",
            (*args, max(1, min(int(limit), 100))),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_problem(kind: str, item_id: str, path=None) -> dict[str, Any] | None:
    if kind not in {"pests", "diseases"}:
        raise ValueError("Unsupported encyclopedia content type")
    conn = connect(path)
    try:
        row = conn.execute(
            f"SELECT * FROM {kind} WHERE id=? AND review_status != 'retired'",
            (item_id,),
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["treatments"] = _treatments(
            conn,
            "pest_treatments" if kind == "pests" else "disease_treatments",
            "pest_id" if kind == "pests" else "disease_id",
            item_id,
        )
        result["sources"] = _sources(conn, "pest" if kind == "pests" else "disease", item_id)
        return result
    finally:
        conn.close()


def list_treatments(q: str = "", limit: int = 50, path=None) -> list[dict[str, Any]]:
    conn = connect(path)
    try:
        where = "review_status != 'retired'"
        args: list[Any] = []
        if q.strip():
            where += " AND (title LIKE ? OR purpose LIKE ? OR instructions LIKE ?)"
            args.extend([f"%{q.strip()}%"] * 3)
        rows = conn.execute(
            f"SELECT * FROM treatments WHERE {where} ORDER BY title COLLATE NOCASE LIMIT ?",
            (*args, max(1, min(int(limit), 100))),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_treatment(item_id: str, path=None) -> dict[str, Any] | None:
    conn = connect(path)
    try:
        row = conn.execute(
            "SELECT * FROM treatments WHERE id=? AND review_status != 'retired'",
            (item_id,),
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["sources"] = _sources(conn, "treatment", item_id)
        return result
    finally:
        conn.close()

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
            args.extend([f"%{q.strip()}%"] * 5)
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


def get_taxon(item_id: str, path=None) -> dict[str, Any] | None:
    """Return a normalized plant profile with linked care, pests, diseases and media."""
    conn = connect(path)
    try:
        canonical_id = item_id
        alias = conn.execute(
            "SELECT taxon_id FROM taxon_id_aliases WHERE legacy_id=?", (canonical_id,)
        ).fetchone()
        if alias is not None:
            canonical_id = alias["taxon_id"]
        row = conn.execute(
            """SELECT t.*, GROUP_CONCAT(DISTINCT n.name) AS common_names
               FROM taxa t LEFT JOIN taxon_names n ON n.taxon_id=t.id
               WHERE t.id=? AND t.verification_status != 'deprecated'
               GROUP BY t.id""", (canonical_id,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["legacy_ids"] = [r["legacy_id"] for r in conn.execute(
            "SELECT legacy_id FROM taxon_id_aliases WHERE taxon_id=? ORDER BY legacy_id",
            (canonical_id,)
        )]
        result["names"] = [dict(r) for r in conn.execute(
            "SELECT name,language,name_type,preferred FROM taxon_names WHERE taxon_id=? ORDER BY preferred DESC,name",
            (canonical_id,)
        )]
        result["care"] = _dict(conn.execute(
            "SELECT * FROM care_profiles WHERE taxon_id=?", (canonical_id,)
        ).fetchone())
        result["fertilizer_guides"] = [dict(r) for r in conn.execute(
            "SELECT * FROM fertilizer_guides WHERE taxon_id=? ORDER BY title", (canonical_id,)
        )]
        result["pests"] = [dict(r) for r in conn.execute(
            """SELECT p.id,p.common_name,p.scientific_name,p.description,
                      tp.relationship,tp.notes,p.review_status
               FROM taxon_pests tp JOIN pests p ON p.id=tp.pest_id
               WHERE tp.taxon_id=? AND p.review_status!='retired'
               ORDER BY p.common_name""", (canonical_id,)
        )]
        result["diseases"] = [dict(r) for r in conn.execute(
            """SELECT d.id,d.common_name,d.causal_agent,d.description,
                      td.relationship,td.notes,d.review_status
               FROM taxon_diseases td JOIN diseases d ON d.id=td.disease_id
               WHERE td.taxon_id=? AND d.review_status!='retired'
               ORDER BY d.common_name""", (canonical_id,)
        )]
        result["media"] = [dict(r) for r in conn.execute(
            """SELECT m.id,m.url,m.caption,m.attribution,m.creator,m.license,m.source_url
               FROM taxon_media tm JOIN media m ON m.id=tm.media_id
               WHERE tm.taxon_id=? AND m.rights_status='approved'
               ORDER BY tm.is_primary DESC,tm.sort_order,m.id""", (canonical_id,)
        )]
        result["sources"] = _sources(conn, "taxon", canonical_id)
        for guide in result["fertilizer_guides"]:
            guide["sources"] = _sources(conn, "fertilizer", guide["id"])
        return result
    finally:
        conn.close()


def search_taxa(q: str = "", limit: int = 100, path=None) -> list[dict[str, Any]]:
    conn = connect(path)
    try:
        where = "t.verification_status != 'deprecated'"
        args: list[Any] = []
        if q.strip():
            where += " AND (t.scientific_name LIKE ? OR t.accepted_name LIKE ? OR t.parent_name LIKE ? OR t.category LIKE ? OR EXISTS "
            where += "(SELECT 1 FROM taxon_names n WHERE n.taxon_id=t.id AND n.name LIKE ?))"
            args.extend([f"%{q.strip()}%"] * 3)
        rows = conn.execute(
            f"""SELECT t.id,COALESCE(NULLIF(t.accepted_name,''),t.scientific_name) AS scientific_name,
                       t.accepted_name,t.rank,t.parent_name,t.cultivar_epithet,t.taxonomy_status,
                       t.category,t.verification_status,
                       (SELECT n.name FROM taxon_names n WHERE n.taxon_id=t.id
                        ORDER BY n.preferred DESC,n.name LIMIT 1) AS common_name
                FROM taxa t WHERE {where}
                ORDER BY common_name COLLATE NOCASE LIMIT ?""",
            (*args, max(1, min(int(limit), 500))),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

"""Exercise real Docker startup/migrations against isolated existing appdata fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_CREATOR = ROOT / "tests" / "docker_preservation_fixture.py"


def run(args: list[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=capture)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def check_fixture(image: str, schema: str) -> None:
    with tempfile.TemporaryDirectory(prefix=f"plants-preservation-{schema}-") as folder:
        data_dir = Path(folder).resolve()
        mount = f"{data_dir}:/app/data"
        run(["docker", "run", "--rm", "-v", mount, "-v", f"{FIXTURE_CREATOR}:/tmp/fixture.py:ro",
             "-e", "PLANTS_DATA_DIR=/app/data", "-e", "PLANTS_NOTIFY_WORKER=false", "-e", "PYTHONPATH=/app", image,
             "python", "/tmp/fixture.py", schema])
        expected_path = data_dir / ".preservation-expected.json"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        name = f"plants-preservation-{schema}-{uuid.uuid4().hex[:8]}"
        port = free_port()
        started = run(["docker", "run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:8000",
                       "-v", mount, "-e", "PLANTS_DATA_DIR=/app/data", "-e", "PLANTS_NOTIFY_WORKER=false",
                       "-e", "PLANTS_WEATHER_OFFLINE=true", image]).stdout.strip()
        if not started:
            raise AssertionError(f"Docker did not return a container id for {schema} fixture")

        failure: str | None = None
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=2) as response:
                        payload = json.loads(response.read())
                        assert response.status == 200, f"/api/status returned {response.status}"
                        assert payload.get("setup_required") is False, "existing user disappeared during startup"
                        break
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    time.sleep(0.5)
            else:
                raise AssertionError("container did not become healthy at /api/status")
        except Exception as exc:
            failure = str(exc)
        finally:
            run(["docker", "stop", name], check=False)
            logs = run(["docker", "logs", name], check=False).stdout
            run(["docker", "rm", name], check=False)
        if failure:
            raise AssertionError(f"{schema} fixture startup failed: {failure}\nContainer logs:\n{logs}")
        assert "Application startup complete" in logs, f"startup did not complete:\n{logs}"

        db_path = data_dir / "plants.db"
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        try:
            actual = {
                "tables": {},
                "sessions": [dict(row) for row in connection.execute("SELECT * FROM sessions ORDER BY token_hash")],
            }
            for table in ("users", "rooms", "plants", "tasks", "events", "settings"):
                order = "key" if table == "settings" else "id"
                actual["tables"][table] = [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY {order}")]
            assert actual["tables"] == expected["tables"], f"{schema}: personal records changed\nexpected={expected['tables']}\nactual={actual['tables']}"
            assert actual["sessions"] == expected["sessions"], f"{schema}: session behavior differs from migration policy"
            columns = {row[1] for row in connection.execute("PRAGMA table_info(plants)")}
            assert "info" in columns, f"{schema}: plants.info migration did not run"
            session_columns = {row[1] for row in connection.execute("PRAGMA table_info(sessions)")}
            assert "via_token" in session_columns, f"{schema}: sessions.via_token migration did not run"
            plant_photo = connection.execute("SELECT photo FROM plants WHERE id=73").fetchone()[0]
            event_photo = connection.execute("SELECT photo FROM events WHERE id=97").fetchone()[0]
            assert plant_photo == expected["photo_references"]["plant"]
            assert event_photo == expected["photo_references"]["event"]
        finally:
            connection.close()

        for filename, digest in expected["photo_hashes"].items():
            path = data_dir / "photos" / filename
            assert path.is_file(), f"{schema}: referenced photo missing: {filename}"
            actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual_digest == digest, f"{schema}: photo bytes changed: {filename}"
        print(f"PASS {schema} appdata: records, photo references/bytes and migration/session policy preserved")


def main() -> None:
    image = sys.argv[1] if len(sys.argv) > 1 else "plants-preservation-ci"
    if not shutil.which("docker"):
        raise SystemExit("Docker CLI is required for this smoke test")
    for schema in ("current", "legacy"):
        check_fixture(image, schema)


if __name__ == "__main__":
    main()

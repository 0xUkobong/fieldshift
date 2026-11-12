"""SQLite persistence for fields and extension rosters."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from rotation_explorer.models import Farm, FarmSetup

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fieldshift.db"


def _connect(path: Path | None = None) -> sqlite3.Connection:
    db = path or DB_PATH
    db.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            continent TEXT,
            country TEXT,
            country_code TEXT,
            state TEXT,
            lga TEXT,
            area TEXT,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            region TEXT,
            soil_note TEXT,
            typical_crop TEXT,
            local_tip TEXT,
            agrozone TEXT,
            crop TEXT,
            priorities TEXT,
            farmer_name TEXT,
            language TEXT,
            observed_yield REAL,
            soil_type TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS roster (
            id INTEGER PRIMARY KEY,
            farmer_name TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def farm_from_row(row: sqlite3.Row) -> Farm:
    return Farm(
        name=row["name"],
        lat=row["lat"],
        lon=row["lon"],
        region=row["region"] or "",
        soil_note=row["soil_note"] or "",
        typical_crop=row["typical_crop"] or row["crop"] or "",
        local_tip=row["local_tip"] or "",
        agrozone=row["agrozone"] or "",
        continent=row["continent"] or "",
        country=row["country"] or "",
        country_code=row["country_code"] or "",
        state=row["state"] or "",
        lga=row["lga"] or "",
        area=row["area"] or "",
    )


def setup_from_row(row: sqlite3.Row) -> FarmSetup:
    priorities = tuple(json.loads(row["priorities"] or "[]"))
    return FarmSetup(
        farm=farm_from_row(row),
        crop=row["crop"] or row["typical_crop"] or "",
        priorities=priorities,
        farmer_name=row["farmer_name"] or "",
        local_tip=row["local_tip"] or "",
        language=row["language"] or "en",
        observed_yield_t_ha=row["observed_yield"],
        soil_type=row["soil_type"] or "Loam",
    )


def save_field(setup: FarmSetup, path: Path | None = None) -> int:
    farm = setup.farm
    connection = _connect(path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO fields (
                name, continent, country, country_code, state, lga, area,
                lat, lon, region, soil_note, typical_crop, local_tip, agrozone,
                crop, priorities, farmer_name, language, observed_yield,
                soil_type, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                farm.name,
                farm.continent,
                farm.country,
                farm.country_code,
                farm.state,
                farm.lga,
                farm.area,
                farm.lat,
                farm.lon,
                farm.region,
                farm.soil_note,
                farm.typical_crop,
                setup.local_tip or farm.local_tip,
                farm.agrozone,
                setup.crop,
                json.dumps(list(setup.priorities)),
                setup.farmer_name,
                setup.language,
                setup.observed_yield_t_ha,
                setup.soil_type,
                _now(),
            ),
        )
        field_id = int(cursor.lastrowid)
        connection.execute(
            "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('last_field_id', ?)",
            (str(field_id),),
        )
        connection.commit()
        return field_id
    finally:
        connection.close()


def list_fields(path: Path | None = None) -> list[sqlite3.Row]:
    connection = _connect(path)
    try:
        return list(
            connection.execute(
                "SELECT * FROM fields ORDER BY updated_at DESC LIMIT 40"
            )
        )
    finally:
        connection.close()


def load_field(field_id: int, path: Path | None = None) -> FarmSetup | None:
    connection = _connect(path)
    try:
        row = connection.execute(
            "SELECT * FROM fields WHERE id = ?", (field_id,)
        ).fetchone()
        return setup_from_row(row) if row else None
    finally:
        connection.close()


def load_last_setup(path: Path | None = None) -> FarmSetup | None:
    connection = _connect(path)
    try:
        meta = connection.execute(
            "SELECT value FROM app_meta WHERE key = 'last_field_id'"
        ).fetchone()
        if not meta:
            return None
        row = connection.execute(
            "SELECT * FROM fields WHERE id = ?", (int(meta["value"]),)
        ).fetchone()
        return setup_from_row(row) if row else None
    finally:
        connection.close()


def save_roster_entry(record: dict, path: Path | None = None) -> None:
    connection = _connect(path)
    try:
        connection.execute(
            """
            INSERT INTO roster(farmer_name, payload, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(farmer_name) DO UPDATE SET
                payload = excluded.payload,
                updated_at = excluded.updated_at
            """,
            (record["farmer_name"], json.dumps(record), _now()),
        )
        connection.commit()
    finally:
        connection.close()


def load_roster(path: Path | None = None) -> list[dict]:
    connection = _connect(path)
    try:
        rows = connection.execute(
            "SELECT payload FROM roster ORDER BY updated_at DESC"
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]
    finally:
        connection.close()



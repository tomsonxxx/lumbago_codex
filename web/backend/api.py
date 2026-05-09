from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from lumbago_app.core.audio import apply_local_metadata, extract_metadata, iter_audio_files
from lumbago_app.core.config import load_settings
from lumbago_app.core.models import Track
from lumbago_app.data.db import get_session_factory
from lumbago_app.data.repository import delete_tracks_by_paths, init_db, upsert_tracks
from lumbago_app.data.schema import TrackOrm
from lumbago_app.services.analysis_engine import AI_FIELDS, AnalysisEngine, MergePolicy, ProviderConfig
from web.backend.db import (
    add_tag_history,
    connect,
    get_cache,
    get_setting,
    list_tag_history,
    migrate,
    set_cache,
    set_setting,
)


def _web_db_path() -> Path:
    configured = os.getenv("WEB_BACKEND_DB", "").strip()
    if configured:
        return Path(configured)
    return Path(".lumbago_data") / "web_backend.sqlite3"


def _web_conn() -> sqlite3.Connection:
    db_path = _web_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    migrate(conn, Path("web/backend/migrations"))
    return conn


class TrackUpdatePayload(BaseModel):
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    albumartist: str | None = None
    year: str | None = None
    genre: str | None = None
    tracknumber: str | None = None
    composer: str | None = None
    comment: str | None = None
    lyrics: str | None = None
    publisher: str | None = None
    bpm: float | None = None
    key: str | None = None
    mood: str | None = None
    energy: float | None = None


class SettingPayload(BaseModel):
    value: str = Field(default="")


class CachePayload(BaseModel):
    value: str = Field(default="")
    ttl_seconds: int = Field(default=300, ge=1)


class TagHistoryPayload(BaseModel):
    track_id: int
    field_name: str
    old_value: str | None = None
    new_value: str | None = None
    source: str = "web"


class ImportPreviewPayload(BaseModel):
    folder: str
    recursive: bool = True


class ImportCommitPayload(BaseModel):
    paths: list[str]


class DuplicatesPayload(BaseModel):
    mode: str = Field(pattern="^(hash|fingerprint|metadata)$")


class XmlConvertPayload(BaseModel):
    input_path: str
    output_path: str


class ProviderConfigPayload(BaseModel):
    provider: str = Field(pattern="^(openai|gemini|grok|deepseek)$")
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    priority: int = 100
    enabled: bool = True


class ProviderConfigUpdatePayload(BaseModel):
    providers: list[ProviderConfigPayload]


class AnalysisJobCreatePayload(BaseModel):
    track_ids: list[int] = Field(default_factory=list)
    providers: list[ProviderConfigPayload] = Field(default_factory=list)
    policy: str = Field(default="aggressive")


class AnalysisApplyPayload(BaseModel):
    overrides: dict[str, dict[str, bool]] = Field(default_factory=dict)
    source_prefix: str = "ai"


app = FastAPI(title="Lumbago Web Backend", version="0.3.0")

_ANALYSIS_ENGINE = AnalysisEngine()
_ANALYSIS_LOCK = threading.Lock()
_ANALYSIS_JOBS: dict[str, dict[str, Any]] = {}


def _serialize_track(row: TrackOrm) -> dict:
    return {
        "id": row.id,
        "path": row.path,
        "title": row.title or Path(row.path).stem,
        "artist": row.artist or "Unknown",
        "album": row.album,
        "albumartist": row.albumartist,
        "year": row.year,
        "genre": row.genre,
        "tracknumber": row.tracknumber,
        "composer": row.composer,
        "comment": row.comment,
        "lyrics": row.lyrics,
        "publisher": row.publisher,
        "key": row.key,
        "bpm": row.bpm,
        "duration": row.duration,
        "loudness": row.loudness_lufs,
        "energy": row.energy,
        "mood": row.mood,
        "artwork_path": row.artwork_path,
        "format": row.format,
        "bitrate": row.bitrate,
        "file_size": row.file_size,
        "date_added": row.date_added.isoformat() if row.date_added else None,
        "hash": row.file_hash,
        "url": row.path,
    }


def _serialize_preview_track(track: Track) -> dict:
    return {
        "id": 0,
        "path": track.path,
        "title": track.title or Path(track.path).stem,
        "artist": track.artist or "Unknown",
        "album": track.album,
        "year": track.year,
        "genre": track.genre,
        "composer": track.composer,
        "comment": track.comment,
        "lyrics": track.lyrics,
        "publisher": track.publisher,
        "key": track.key,
        "bpm": track.bpm,
        "duration": track.duration,
        "hash": track.file_hash,
        "fingerprint": track.fingerprint,
        "url": track.path,
    }


def _extract_track(path: Path) -> Track:
    try:
        track = extract_metadata(path)
    except Exception:
        stat = path.stat()
        track = Track(path=str(path), file_size=stat.st_size, file_mtime=stat.st_mtime)
    apply_local_metadata(track, path)
    return track


def _list_track_rows() -> list[TrackOrm]:
    init_db()
    Session = get_session_factory()
    with Session() as session:
        return list(session.scalars(select(TrackOrm).order_by(TrackOrm.id)).all())


def _track_from_row(row: TrackOrm) -> Track:
    return Track(
        path=row.path,
        title=row.title,
        artist=row.artist,
        album=row.album,
        albumartist=row.albumartist,
        year=row.year,
        genre=row.genre,
        tracknumber=row.tracknumber,
        discnumber=row.discnumber,
        composer=row.composer,
        bpm=row.bpm,
        key=row.key,
        mood=row.mood,
        energy=row.energy,
        comment=row.comment,
        isrc=row.isrc,
        publisher=row.publisher,
        grouping=row.grouping,
        copyright=row.copyright,
        remixer=row.remixer,
    )


def _default_provider_payloads() -> list[ProviderConfigPayload]:
    settings = load_settings()
    defaults = [
        ProviderConfigPayload(
            provider="openai",
            api_key=settings.openai_api_key or settings.cloud_ai_api_key or "",
            base_url=settings.openai_base_url or "https://api.openai.com/v1",
            model=settings.openai_model or "gpt-4.1-mini",
            priority=0,
            enabled=True,
        ),
        ProviderConfigPayload(
            provider="gemini",
            api_key=settings.gemini_api_key or settings.cloud_ai_api_key or "",
            base_url=settings.gemini_base_url or "https://generativelanguage.googleapis.com/v1beta",
            model=settings.gemini_model or "gemini-2.5-flash",
            priority=1,
            enabled=True,
        ),
        ProviderConfigPayload(
            provider="grok",
            api_key=settings.grok_api_key or settings.cloud_ai_api_key or "",
            base_url=settings.grok_base_url or "https://api.x.ai/v1",
            model=settings.grok_model or "grok-2-latest",
            priority=2,
            enabled=True,
        ),
        ProviderConfigPayload(
            provider="deepseek",
            api_key=settings.deepseek_api_key or settings.cloud_ai_api_key or "",
            base_url=settings.deepseek_base_url or "https://api.deepseek.com/v1",
            model=settings.deepseek_model or "deepseek-chat",
            priority=3,
            enabled=True,
        ),
    ]
    return defaults


def _load_provider_payloads() -> list[ProviderConfigPayload]:
    conn = _web_conn()
    try:
        raw = get_setting(conn, "ai_providers")
    finally:
        conn.close()
    if not raw:
        return _default_provider_payloads()
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return _default_provider_payloads()
        out: list[ProviderConfigPayload] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            out.append(ProviderConfigPayload(**item))
        return out or _default_provider_payloads()
    except Exception:
        return _default_provider_payloads()


def _to_provider_configs(payloads: list[ProviderConfigPayload]) -> list[ProviderConfig]:
    providers: list[ProviderConfig] = []
    for payload in payloads:
        if not payload.enabled:
            continue
        if not payload.api_key.strip():
            continue
        providers.append(
            ProviderConfig(
                provider=payload.provider,
                api_key=payload.api_key.strip(),
                base_url=payload.base_url.strip(),
                model=payload.model.strip(),
                priority=payload.priority,
                enabled=payload.enabled,
            )
        )
    return providers


def _process_analysis_job(job_id: str) -> None:
    with _ANALYSIS_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
    if not job:
        return
    track_ids = [int(item) for item in job["track_ids"]]
    provider_payloads = [ProviderConfigPayload(**item) for item in job["provider_payloads"]]
    providers = _to_provider_configs(provider_payloads)
    if not providers:
        with _ANALYSIS_LOCK:
            job["status"] = "failed"
            job["error"] = "No enabled providers with valid API keys"
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
        return

    Session = get_session_factory()
    items: list[dict[str, Any]] = []
    with Session() as session:
        rows = list(session.scalars(select(TrackOrm).where(TrackOrm.id.in_(track_ids))).all())
        total = len(rows)
        with _ANALYSIS_LOCK:
            job["total"] = total
        for index, row in enumerate(rows, start=1):
            track = _track_from_row(row)
            envelope = _ANALYSIS_ENGINE.analyze_track(
                track=track,
                providers=providers,
                policy=MergePolicy(mode=job.get("policy", "aggressive")),
            )
            item = {
                "track_id": row.id,
                "path": row.path,
                "title": row.title or Path(row.path).stem,
                "artist": row.artist or "Unknown",
                "provider_chain": envelope.provider_chain,
                "confidence": envelope.confidence,
                "decisions": [
                    {
                        "field": decision.field,
                        "old_value": decision.old_value,
                        "new_value": decision.new_value,
                        "winner_provider": decision.winner_provider,
                        "confidence": decision.confidence,
                        "accepted": decision.accepted,
                        "reason": decision.reason,
                    }
                    for decision in envelope.decisions
                ],
                "provider_results": [
                    {
                        "provider": result.provider,
                        "overall_confidence": result.overall_confidence,
                        "values": result.values,
                        "error": result.error,
                    }
                    for result in envelope.provider_results
                ],
            }
            items.append(item)
            with _ANALYSIS_LOCK:
                job["processed"] = index
                job["items"] = items
        with _ANALYSIS_LOCK:
            job["status"] = "completed"
            job["finished_at"] = datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/settings/{key}")
def read_setting(key: str) -> dict[str, str | None]:
    conn = _web_conn()
    try:
        return {"key": key, "value": get_setting(conn, key)}
    finally:
        conn.close()


@app.put("/settings/{key}")
def write_setting(key: str, payload: SettingPayload) -> dict[str, str]:
    conn = _web_conn()
    try:
        set_setting(conn, key, payload.value)
    finally:
        conn.close()
    return {"key": key, "value": payload.value}


@app.get("/cache/{key}")
def read_cache(key: str) -> dict[str, str | None]:
    conn = _web_conn()
    try:
        return {"key": key, "value": get_cache(conn, key)}
    finally:
        conn.close()


@app.put("/cache/{key}")
def write_cache(key: str, payload: CachePayload) -> dict[str, str | int]:
    conn = _web_conn()
    try:
        set_cache(conn, key, payload.value, payload.ttl_seconds)
    finally:
        conn.close()
    return {"key": key, "value": payload.value, "ttl_seconds": payload.ttl_seconds}


@app.get("/ai/providers")
def get_ai_providers() -> dict[str, list[dict[str, Any]]]:
    providers = _load_provider_payloads()
    return {"providers": [item.model_dump() for item in providers]}


@app.put("/ai/providers")
def put_ai_providers(payload: ProviderConfigUpdatePayload) -> dict[str, list[dict[str, Any]]]:
    conn = _web_conn()
    try:
        set_setting(conn, "ai_providers", json.dumps([item.model_dump() for item in payload.providers], ensure_ascii=False))
    finally:
        conn.close()
    return {"providers": [item.model_dump() for item in payload.providers]}


@app.post("/analysis/jobs")
def create_analysis_job(payload: AnalysisJobCreatePayload, background: BackgroundTasks) -> dict[str, Any]:
    track_ids = payload.track_ids
    if not track_ids:
        track_ids = [row.id for row in _list_track_rows()]
    if not track_ids:
        raise HTTPException(status_code=400, detail="No tracks available for analysis.")
    provider_payloads = payload.providers or _load_provider_payloads()
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "status": "queued",
        "policy": payload.policy or "aggressive",
        "track_ids": track_ids,
        "provider_payloads": [item.model_dump() for item in provider_payloads],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "processed": 0,
        "total": len(track_ids),
        "items": [],
    }
    with _ANALYSIS_LOCK:
        _ANALYSIS_JOBS[job_id] = job
        _ANALYSIS_JOBS[job_id]["status"] = "running"
    background.add_task(_process_analysis_job, job_id)
    return {"job_id": job_id, "status": "running"}


@app.get("/analysis/jobs/{job_id}")
def get_analysis_job(job_id: str) -> dict[str, Any]:
    with _ANALYSIS_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")
        return dict(job)


@app.post("/analysis/jobs/{job_id}/apply")
def apply_analysis_job(job_id: str, payload: AnalysisApplyPayload) -> dict[str, Any]:
    with _ANALYSIS_LOCK:
        job = _ANALYSIS_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.get("status") != "completed":
        raise HTTPException(status_code=409, detail="Job is not completed yet.")

    Session = get_session_factory()
    conn = _web_conn()
    updated = 0
    changes = 0
    try:
        with Session() as session:
            rows = list(session.scalars(select(TrackOrm).where(TrackOrm.id.in_(job["track_ids"]))).all())
            by_id = {row.id: row for row in rows}
            for item in job.get("items", []):
                track_id = int(item["track_id"])
                row = by_id.get(track_id)
                if row is None:
                    continue
                item_changes = 0
                override = payload.overrides.get(str(track_id), {})
                source = f"{payload.source_prefix}:{item.get('provider_chain', 'unknown')}"
                for decision in item.get("decisions", []):
                    field_name = decision.get("field")
                    if field_name not in AI_FIELDS:
                        continue
                    accepted = bool(decision.get("accepted"))
                    if field_name in override:
                        accepted = bool(override[field_name])
                    if not accepted:
                        continue
                    new_value = decision.get("new_value")
                    old_value = getattr(row, field_name, None)
                    if old_value == new_value:
                        continue
                    setattr(row, field_name, new_value)
                    add_tag_history(
                        conn=conn,
                        track_id=track_id,
                        field_name=field_name,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        source=source,
                    )
                    item_changes += 1
                    changes += 1
                if item_changes > 0:
                    row.date_modified = datetime.utcnow()
                    updated += 1
            session.commit()
    finally:
        conn.close()
    return {"updated_tracks": updated, "applied_changes": changes}


@app.post("/tag-history")
def create_tag_history(payload: TagHistoryPayload) -> dict[str, str | int | None]:
    conn = _web_conn()
    try:
        add_tag_history(
            conn=conn,
            track_id=payload.track_id,
            field_name=payload.field_name,
            old_value=payload.old_value,
            new_value=payload.new_value,
            source=payload.source,
        )
    finally:
        conn.close()
    return payload.model_dump()


@app.get("/tag-history/{track_id}")
def read_tag_history(track_id: int) -> dict[str, list[dict]]:
    conn = _web_conn()
    try:
        rows = list_tag_history(conn, track_id)
    finally:
        conn.close()
    return {"items": [dict(row) for row in rows]}


@app.get("/tracks")
def list_tracks() -> dict[str, list[dict]]:
    return {"tracks": [_serialize_track(row) for row in _list_track_rows()]}


@app.put("/tracks/{track_path:path}")
def update_track_endpoint(track_path: str, payload: TrackUpdatePayload) -> dict:
    """Aktualizuje tagi wybranego tracka w bazie i pliku audio."""
    from lumbago_app.data.repository import update_track as repo_update_track

    init_db()
    Session = get_session_factory()
    with Session() as session:
        row = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))
        if row is None:
            raise HTTPException(status_code=404, detail=f"Track not found: {track_path}")

        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            if hasattr(row, field):
                setattr(row, field, value)
        session.commit()
        updated_row = session.scalar(select(TrackOrm).where(TrackOrm.path == track_path))

    # Zapisz tagi do pliku audio
    if update_data:
        try:
            from lumbago_app.core.audio import write_tags
            file_tags = {k: str(v) for k, v in update_data.items()
                         if k not in {"energy", "mood", "loudness"}}
            if file_tags:
                write_tags(Path(track_path), file_tags)
        except Exception as exc:
            # Błąd zapisu do pliku — loguj szczegóły wewnętrznie, nie eksponuj
            # stack trace / ścieżek systemowych w odpowiedzi HTTP (CodeQL CWE-209).
            import logging
            logging.getLogger(__name__).warning("write_tags failed for %s: %s",
                                                Path(track_path).name, exc)
            return {"track": _serialize_track(updated_row),
                    "warning": "Zapis tagów do pliku audio nie powiódł się."}

    return {"track": _serialize_track(updated_row)}


@app.post("/tracks/import-preview")
def import_preview(payload: ImportPreviewPayload) -> dict[str, list[dict] | list[str]]:
    folder = Path(payload.folder).resolve()
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="Folder importu nie istnieje.")

    tracks: list[dict] = []
    errors: list[str] = []
    for path in iter_audio_files(folder, recursive=payload.recursive):
        try:
            tracks.append(_serialize_preview_track(_extract_track(path)))
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    return {"tracks": tracks, "errors": errors}


@app.post("/tracks/import-commit")
def import_commit(payload: ImportCommitPayload) -> dict[str, int | list[str]]:
    if not payload.paths:
        raise HTTPException(status_code=400, detail="Brak plikow do importu.")

    init_db()
    imported = []
    errors: list[str] = []
    for raw_path in payload.paths:
        path = Path(raw_path).resolve()
        if not path.exists() or not path.is_file():
            errors.append(f"{raw_path}: plik nie istnieje")
            continue
        try:
            imported.append(_extract_track(path))
        except Exception as exc:
            errors.append(f"{raw_path}: {exc}")

    if imported:
        upsert_tracks(imported)

    return {"imported": len(imported), "errors": errors}


@app.post("/duplicates/analyze")
def analyze_duplicates(payload: DuplicatesPayload) -> dict[str, list[dict]]:
    buckets: dict[str, list[TrackOrm]] = {}

    for row in _list_track_rows():
        if payload.mode == "hash":
            bucket_key = row.file_hash or ""
            similarity = 1.0
        elif payload.mode == "fingerprint":
            bucket_key = row.fingerprint or ""
            similarity = 0.95
        else:
            title = (row.title or "").strip().lower()
            artist = (row.artist or "").strip().lower()
            duration = int(row.duration or 0)
            bucket_key = f"{title}|{artist}|{duration}"
            similarity = 0.9
        if not bucket_key:
            continue
        buckets.setdefault(bucket_key, []).append(row)

    groups = []
    for key, group_rows in buckets.items():
        if len(group_rows) < 2:
            continue
        groups.append(
            {
                "key": key,
                "similarity": similarity,
                "tracks": [_serialize_track(row) for row in group_rows],
            }
        )

    return {"groups": groups}


@app.delete("/tracks/{track_path:path}")
def delete_track_endpoint(track_path: str) -> dict[str, str]:
    """Usuwa track z bazy danych (nie usuwa pliku z dysku)."""
    init_db()
    delete_tracks_by_paths([track_path])
    return {"deleted": track_path}


@app.post("/convert/rekordbox-to-virtualdj")
def convert_rekordbox_to_virtualdj(payload: XmlConvertPayload) -> dict[str, object]:
    """Konwertuje plik Rekordbox XML na format VirtualDJ XML."""
    from lumbago_app.services.xml_converter import export_virtualdj_xml, parse_rekordbox_xml

    # resolve() canonicalizuje ścieżkę (eliminuje ../) — sanitizer dla CWE-022.
    input_path = Path(payload.input_path).resolve()
    output_path = Path(payload.output_path).resolve()

    if input_path.suffix.lower() != ".xml":
        raise HTTPException(status_code=400, detail="Plik wejściowy musi mieć rozszerzenie .xml.")
    if output_path.suffix.lower() != ".xml":
        raise HTTPException(status_code=400, detail="Plik wyjściowy musi mieć rozszerzenie .xml.")
    if not input_path.is_file():
        raise HTTPException(status_code=400, detail="Plik wejściowy nie istnieje.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tracks = parse_rekordbox_xml(input_path)
    if not tracks:
        raise HTTPException(status_code=422, detail="Nie znaleziono tracków w pliku XML.")

    export_virtualdj_xml(tracks, output_path)
    return {"converted": len(tracks), "output_path": str(output_path)}

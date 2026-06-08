from pydantic import BaseModel
from enum import Enum
from typing import Optional


class TrackStatus(str, Enum):
    pending = "pending"
    downloading = "downloading"
    done = "done"
    unavailable = "unavailable"
    not_found = "not_found"


class Track(BaseModel):
    id: str
    artist: str
    title: str
    status: TrackStatus = TrackStatus.pending
    source: Optional[str] = None
    error: Optional[str] = None
    yandex_id: Optional[int] = None
    available: bool = True
    sc_url: Optional[str] = None
    duration_ms: Optional[int] = None
    album: Optional[str] = None
    year: Optional[int] = None

from pydantic import BaseModel
from .track import Track


class Job(BaseModel):
    id: str
    name: str
    source: str
    folder: str
    tracks: list[Track]

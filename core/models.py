from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional

class Photo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True)
    thumbnail_path: str
    created_at: datetime
    exif_date: datetime
    favorite: bool = False
    hash: Optional[str] = None
    is_video: bool = False
    is_live: bool = False
    

Index("idx_photo_path_unique", Photo.path, unique=True)
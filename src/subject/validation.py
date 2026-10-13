from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr


class SubjectCreateSchema(BaseModel):
    name: constr(min_length=1, max_length=100)
    image_url: Optional[str] = None


class SubjectUpdateSchema(BaseModel):
    name: constr(min_length=1, max_length=100) | None = None
    image_url: Optional[str] = None


class SubjectResponseSchema(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

from typing import Optional
from pydantic import BaseModel


class PaginatedMeta(BaseModel):
    """Reusable pagination metadata for list responses."""
    total: int
    page: int
    page_size: int

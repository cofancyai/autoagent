"""Standard API response schemas"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard API response wrapper"""

    data: DataT
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat()})


class ErrorDetail(BaseModel):
    """Error detail schema"""

    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: ErrorDetail
    meta: dict = Field(default_factory=lambda: {"timestamp": datetime.utcnow().isoformat()})

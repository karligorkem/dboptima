from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class DatabaseConnectionCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    host: str = Field(
        min_length=1,
        max_length=255,
    )

    port: int = Field(
        default=5432,
        ge=1,
        le=65535,
    )

    database_name: str = Field(
        min_length=1,
        max_length=100,
    )

    username: str = Field(
        min_length=1,
        max_length=100,
    )

    password: str = Field(
        min_length=1,
        max_length=255,
    )


class DatabaseConnectionResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    database_name: str
    username: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
"""Typed inputs and storefront events for a digital delivery stream."""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class DeliveryRequest(BaseModel):
    content_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    asset_name: str = Field(min_length=1, max_length=120)
    asset_format: str = Field(min_length=1, max_length=40)
    signed_download_url: HttpUrl
    subscriber_name: str = Field(min_length=1, max_length=80)


class StreamEvent(BaseModel):
    event: Literal["copy_delta", "asset_ready"]
    content_id: str
    text: str
    download_url: str | None = None


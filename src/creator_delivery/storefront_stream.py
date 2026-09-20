"""FastAPI route that streams creator delivery copy as SSE."""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from creator_delivery.content_processor import delivery_events
from creator_delivery.delivery_models import DeliveryRequest
from creator_delivery.infrai_stream import CreatorCopyStream

storefront = FastAPI(title="Creator delivery stream")

@storefront.post("/creator-deliveries/stream")
async def stream_delivery(order: DeliveryRequest) -> StreamingResponse:
    return StreamingResponse(
        delivery_events(order, CreatorCopyStream().deltas),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

import asyncio

from creator_delivery.content_processor import delivery_events
from creator_delivery.delivery_models import DeliveryRequest


class RecordedCopyStream:
    async def deltas(self, order: DeliveryRequest):
        yield f"Hi {order.subscriber_name}, your "
        yield f"{order.asset_name} is ready."


def test_sse_feed_finishes_with_one_ready_event() -> None:
    order = DeliveryRequest(
        content_id="template-17",
        asset_name="Checkout Template",
        asset_format="FIG",
        signed_download_url="https://downloads.example/template-17?signature=test",
        subscriber_name="Noor",
    )

    async def collect() -> list[str]:
        return [event async for event in delivery_events(order, RecordedCopyStream().deltas)]

    events = asyncio.run(collect())

    assert sum("event: asset_ready" in event for event in events) == 1
    assert "Hi Noor, your Checkout Template is ready." in events[-1]
    assert str(order.signed_download_url) in events[-1]

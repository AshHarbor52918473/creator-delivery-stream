"""Turn model deltas into a publishable subscriber update."""

from collections.abc import AsyncIterator
from collections.abc import Callable

from creator_delivery.delivery_models import DeliveryRequest, StreamEvent


class DeliveryContentProcessor:
    def __init__(self, order: DeliveryRequest) -> None:
        self.order = order
        self._parts: list[str] = []

    def accept(self, text: str) -> StreamEvent | None:
        if not text:
            return None
        self._parts.append(text)
        return StreamEvent(
            event="copy_delta",
            content_id=self.order.content_id,
            text=text,
        )

    def finish(self) -> StreamEvent:
        update = "".join(self._parts).strip()
        if not update:
            raise ValueError("A completed delivery update must contain text")
        return StreamEvent(
            event="asset_ready",
            content_id=self.order.content_id,
            text=update,
            download_url=str(self.order.signed_download_url),
        )


def encode_sse(event: StreamEvent) -> str:
    return f"event: {event.event}\ndata: {event.model_dump_json()}\n\n"


async def delivery_events(
    order: DeliveryRequest,
    delta_source: Callable[[DeliveryRequest], AsyncIterator[str]],
) -> AsyncIterator[str]:
    processor = DeliveryContentProcessor(order)
    async for text in delta_source(order):
        event = processor.accept(text)
        if event is not None:
            yield encode_sse(event)
    yield encode_sse(processor.finish())

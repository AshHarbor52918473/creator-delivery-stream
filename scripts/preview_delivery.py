"""Print the same SSE feed a storefront would consume."""

import argparse
import asyncio

from creator_delivery.content_processor import delivery_events
from creator_delivery.delivery_models import DeliveryRequest
from creator_delivery.infrai_stream import CreatorCopyStream


async def preview() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-url", required=True)
    args = parser.parse_args()
    order = DeliveryRequest(
        content_id="launch-kit-1042",
        asset_name="Launch Day Product Photo Kit",
        asset_format="ZIP",
        signed_download_url=args.download_url,
        subscriber_name="Maya",
    )
    async for event in delivery_events(order, CreatorCopyStream().deltas):
        print(event, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(preview())

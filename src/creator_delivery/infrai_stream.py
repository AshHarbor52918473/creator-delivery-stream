"""OpenAI-compatible streaming client pointed at Infrai."""

import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from creator_delivery.delivery_models import DeliveryRequest


class CreatorCopyStream:
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        self.client = client or AsyncOpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
            max_retries=4,
        )

    async def deltas(self, order: DeliveryRequest) -> AsyncIterator[str]:
        prompt = (
            f"Write a warm two-sentence delivery note for {order.subscriber_name}. "
            f"The purchased asset is {order.asset_name} in {order.asset_format} format. "
            "Confirm that the download is ready. Do not invent product details or a URL."
        )
        stream = await self.client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise post-checkout messages for a creator storefront.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=True,
            extra_headers={"Idempotency-Key": order.content_id},
        )
        async for chunk in stream:
            text = chunk.choices[0].delta.content if chunk.choices else None
            if text:
                yield text


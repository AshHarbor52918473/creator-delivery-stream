import pytest

from creator_delivery.content_processor import DeliveryContentProcessor
from creator_delivery.delivery_models import DeliveryRequest


def delivery_request() -> DeliveryRequest:
    return DeliveryRequest(
        content_id="brush-pack-88",
        asset_name="Studio Brush Pack",
        asset_format="ZIP",
        signed_download_url="https://downloads.example/brush-pack-88?signature=test",
        subscriber_name="Ari",
    )


def test_completed_copy_releases_the_download_to_the_storefront() -> None:
    processor = DeliveryContentProcessor(delivery_request())

    first = processor.accept("Your Studio Brush Pack ")
    second = processor.accept("is ready to download.")
    ready = processor.finish()

    assert first is not None and first.event == "copy_delta"
    assert second is not None and second.download_url is None
    assert ready.event == "asset_ready"
    assert ready.text == "Your Studio Brush Pack is ready to download."
    assert ready.download_url == "https://downloads.example/brush-pack-88?signature=test"


def test_empty_completed_copy_does_not_release_the_download() -> None:
    processor = DeliveryContentProcessor(delivery_request())
    processor.accept("   ")

    with pytest.raises(ValueError, match="must contain text"):
        processor.finish()


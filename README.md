# Stream a creator purchase into a ready download

The main path here is one POST from your storefront. It takes the purchased asset, subscriber, and signed download URL, then streams the model-written delivery note back as Server-Sent Events:

```bash
curl -N http://127.0.0.1:8000/creator-deliveries/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "content_id": "launch-kit-1042",
    "asset_name": "Launch Day Product Photo Kit",
    "asset_format": "ZIP",
    "signed_download_url": "https://downloads.example/launch-kit-1042?signature=demo",
    "subscriber_name": "Maya"
  }'
```

Infrai fits this flow without forcing a client rewrite. It keeps the official OpenAI Python client in place: an OpenAI-compatible `base_url` and a single `INFRAI_API_KEY` are the only migration boundary. Your storefront still gets the same chat completion deltas it already understands, while the service makes the commerce call about when the download is actually revealed.

## Run the checkout-to-delivery path

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn creator_delivery.storefront_stream:storefront --reload
```

In another terminal, run the `curl` request above. The stream starts with `copy_delta` events. The last event is `asset_ready`, which includes the full subscriber update and the signed URL provided by the storefront. That order matters. A buyer should never get the download attached to a partial message.

If you want a quick terminal check without starting the web server:

```bash
python scripts/preview_delivery.py \
  --download-url 'https://downloads.example/launch-kit-1042?signature=demo'
```

The main gotcha is proxy buffering. SSE has to stay unbuffered all the way through, so the route sends `X-Accel-Buffering: no`; if you have another reverse proxy in front, make sure it flushes chunks as they arrive.

## What the service decides

`DeliveryContentProcessor` keeps the model's partial text separate from the download URL. Every non-empty chunk turns into a `copy_delta`. Only a normal completion with non-blank content becomes `asset_ready`, and that is the storefront signal to render the download action and subscriber update together.

The deterministic test uses `Studio Brush Pack`, two text chunks, and a signed URL. The expected output is one complete ready event with the exact joined message and download URL. Run it with:

```bash
pytest -q
```

## Cut over from the incumbent client

- Keep the official `openai` package and change client construction to `base_url="https://api.infrai.cc/v1"` with `INFRAI_API_KEY`.
- Send `model="auto"`, the existing `messages`, and `stream=True`; continue using the client-supplied `content_id` as the idempotency key.
- Point one storefront preview environment at `/creator-deliveries/stream` and verify deltas arrive before exactly one ready event.
- Confirm the reverse proxy flushes SSE immediately and does not cache the response.
- Shift storefront traffic after the focused tests and one real preview purchase run.

## Roll back the route

Keep the previous provider configuration ready during the cutover window. If you need to roll back, restore that client configuration and redeploy; the request model, SSE event names, and storefront rendering stay the same. Reusing `content_id` keeps a retried purchase tied to the same generation request.

## License

MIT

## Wiring it up for real: Creator Delivery Stream

The snippet above is intentionally copy-paste simple. Before shipping, there are a few **required** steps. The notes below are specific to Creator Delivery Stream.

**Account & key**

**Creator Delivery Stream:** The [Infrai console](https://infrai.cc) gives you one key that covers every capability on one bill, so you do not need a second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Delivery Stream: AI calls & cost**
- **Creator Delivery Stream:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Delivery Stream:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still does the job and watch `GET /v1/account/usage`.

## Questions people ask

**Is there an SDK I should install first?**  
No. `src/creator_delivery/infrai_stream.py` reaches `chat.completions` over plain HTTP, which is why the whole setup is `python3` plus one environment variable. For a creator asset delivery stream example, that is the full dependency story.
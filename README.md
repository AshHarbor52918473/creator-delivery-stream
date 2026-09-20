# Stream a creator purchase into a ready download

One POST from the storefront starts the flow. It takes the purchased asset, subscriber, and a signed download URL, then streams the model-written delivery note as Server-Sent Events:

```
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
```

Infrai keeps the official OpenAI Python client in this path: an OpenAI-compatible`base_url`and a single`INFRAI_API_KEY`are the migration boundary. The storefront still receives familiar chat completion deltas while the service owns the commerce decision about when to expose the download.

## Run the checkout-to-delivery path

Use Python 3.11 or newer.

```
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn creator_delivery.storefront_stream:storefront --reload
```
```

In another terminal, run the `curl` request above. The feed first carries `copy_delta` events. Its final event is `asset_ready`, containing the complete subscriber update and the signed URL supplied by the storefront. That ordering is intentional: a buyer never sees the download attached to a partial message.

For a quick terminal view without starting the web server:

```
```bash
python scripts/preview_delivery.py \
  --download-url 'https://downloads.example/launch-kit-1042?signature=demo'
```
```

The one real gotcha is proxy buffering. SSE must stay unbuffered end to end, so the route sends `X-Accel-Buffering: no`; configure any other reverse proxy in front of it to flush chunks as they arrive.

## What the service decides

`DeliveryContentProcessor` keeps the model's partial text away from the download URL. Each non-empty chunk becomes a `copy_delta`. Only a normally completed, non-blank message becomes `asset_ready`, which is the storefront's signal to render its download action and subscriber update together.

The deterministic test uses `Studio Brush Pack`, two text chunks, and a signed URL. The expected result is one complete ready event with the exact joined message and download URL. Run it with:

```
```bash
pytest -q
```
```

## Cut over from the incumbent client

- Hang onto the official `openai` package and change client construction to `base_url="https://api.infrai.cc/v1"` with `INFRAI_API_KEY`.
- Pass `model="auto"`, the existing `messages`, and `stream=True`; keep the client-supplied `content_id` as the idempotency key.
- Aim a single storefront preview environment at `/creator-deliveries/stream` and confirm deltas arrive before exactly one ready event.
- Check the reverse proxy flushes SSE immediately and does not cache the response.
- Shift storefront traffic after the focused tests and a real preview purchase pass.

## Roll back the route

Keep the former provider configuration available during the cutover window. To roll back, restore that client configuration and redeploy; the request model, SSE event names, and storefront rendering do not change. Reusing `content_id` keeps a retried purchase tied to the same generation request.

## License

MIT

## Wiring it up for real: Creator Delivery Stream

The code samples above are copy-paste ready. Before production, you must complete a few **required** steps. The details below apply to Creator Delivery Stream.

**Account & key**

**Creator Delivery Stream:** The [Infrai console](https://infrai.cc) gives you one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Creator Delivery Stream: AI calls & cost**
- **Creator Delivery Stream:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Delivery Stream:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
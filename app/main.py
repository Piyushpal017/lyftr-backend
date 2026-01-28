from fastapi import FastAPI, status
from app.config import settings
from app.models import init_db, get_db_connection
import hmac
import hashlib
from fastapi import Request, HTTPException
from pydantic import BaseModel, Field, validator
import re
from app.storage import insert_message
from app.storage import get_stats
import time
import uuid
from fastapi import Request
from app.logging_utils import setup_logger
from fastapi import Query
from app.storage import list_messages
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from app.metrics import (
    webhook_requests_total,
    webhook_duplicates_total,
    webhook_errors_total,
)


logger = setup_logger(settings.LOG_LEVEL)


app = FastAPI(title="Lyftr AI Backend Assignment")

class WebhookMessage(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_: str = Field(..., alias="from")
    to: str
    ts: str
    text: str | None = Field(default=None, max_length=4096)

    @validator("from_", "to")
    def validate_msisdn(cls, v):
        if not re.fullmatch(r"\+\d+", v):
            raise ValueError("Invalid E.164 number")
        return v

    @validator("ts")
    def validate_ts(cls, v):
        if not v.endswith("Z"):
            raise ValueError("Timestamp must be UTC with Z")
        return v

@app.on_event("startup")
def startup():
    if not settings.WEBHOOK_SECRET:
        print("WEBHOOK_SECRET is not set")
        return
    init_db()

@app.get("/health/live")
def health_live():
    return {"status": "alive"}

@app.get("/health/ready")
def health_ready():
    if not settings.WEBHOOK_SECRET:
        return {"status": "WEBHOOK_SECRET missing"}, status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        conn = get_db_connection()
        conn.execute("SELECT 1;")
        conn.close()
    except Exception:
        return {"status": "DB not ready"}, status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": "ready"}

def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    computed = hmac.new(
        key=secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


@app.post("/webhook")
async def webhook(request: Request):
    webhook_requests_total.inc()   # 👈 STEP 7: total requests counter

    raw_body = await request.body()
    signature = request.headers.get("X-Signature")

    result = "created"
    dup = False
    message_id = None

    # ❌ Invalid signature
    if not signature or not verify_signature(
        settings.WEBHOOK_SECRET, raw_body, signature
    ):
        result = "invalid_signature"
        webhook_errors_total.inc()   # 👈 error counter

        logger.error(
            "webhook_failed",
            extra={"extra": {"result": result}}
        )
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = await request.json()
        msg = WebhookMessage(**payload)
        message_id = msg.message_id

        inserted = insert_message(msg.dict(by_alias=True))

        if not inserted:
            dup = True
            result = "duplicate"
            webhook_duplicates_total.inc()   # 👈 duplicate counter

        logger.info(
            "webhook_processed",
            extra={
                "extra": {
                    "message_id": message_id,
                    "dup": dup,
                    "result": result,
                }
            },
        )

        return {"status": "ok"}

    except Exception as e:
        webhook_errors_total.inc()   # 👈 unexpected error
        logger.exception(
            "webhook_exception",
            extra={"extra": {"error": str(e)}}
        )
        raise HTTPException(status_code=500, detail="internal error")





@app.get("/messages")
def get_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_: str | None = Query(None, alias="from"),
    since: str | None = None,
    q: str | None = None,
):
    rows, total = list_messages(limit, offset, from_, since, q)

    data = [
        {
            "message_id": r["message_id"],
            "from": r["from"],
            "to": r["to"],
            "ts": r["ts"],
            "text": r["text"],
        }
        for r in rows
    ]

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
@app.get("/stats")
def stats():
    return get_stats()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    response = await call_next(request)

    latency_ms = int((time.time() - start_time) * 1000)

    log_data = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": latency_ms,
    }

    logger.info("request_completed", extra={"extra": log_data})

    return response
@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
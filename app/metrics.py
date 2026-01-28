from prometheus_client import Counter

webhook_requests_total = Counter(
    "webhook_requests_total",
    "Total webhook requests received"
)

webhook_duplicates_total = Counter(
    "webhook_duplicates_total",
    "Total duplicate webhook requests"
)

webhook_errors_total = Counter(
    "webhook_errors_total",
    "Total webhook errors"
)

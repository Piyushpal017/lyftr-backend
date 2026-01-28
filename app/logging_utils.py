import json
import logging
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra"):
            log_record.update(record.extra)

        return json.dumps(log_record)


def setup_logger(level="INFO"):
    logger = logging.getLogger("app")
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger

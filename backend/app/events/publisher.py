from typing import Any, Dict
import os
import json
import logging

logger = logging.getLogger(__name__)


class Publisher:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or os.environ.get("REDIS_URL")
        self._client = None

    def _ensure_redis(self):
        if not self.redis_url:
            return None
        if self._client is not None:
            return self._client
        try:
            import redis

            self._client = redis.from_url(self.redis_url)
            return self._client
        except Exception as e:
            logger.debug("Redis not available: %s", e)
            self._client = None
            return None

    def publish(self, channel: str, event: Dict[str, Any]) -> bool:
        payload = json.dumps(event)
        client = self._ensure_redis()
        if client is None:
            logger.info("No redis configured; skipping publish for channel %s", channel)
            return False
        try:
            client.publish(channel, payload)
            logger.debug("Published event to %s", channel)
            return True
        except Exception as e:
            logger.exception("Failed to publish to redis: %s", e)
            return False


# module-level default publisher
default = Publisher()


def publish_event(channel: str, event: Dict[str, Any]) -> bool:
    return default.publish(channel, event)

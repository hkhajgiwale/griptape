from __future__ import annotations

import time
from abc import ABC, abstractmethod
from concurrent import futures
from logging import Logger

from attr import Factory, define, field

from griptape.events import BaseEvent

logger = Logger(__name__)


@define
class BaseEventListenerDriver(ABC):
    futures_executor: futures.Executor = field(default=Factory(lambda: futures.ThreadPoolExecutor()), kw_only=True)
    batched: bool = field(default=False, kw_only=True)
    batch_size: int = field(default=10, kw_only=True)
    batch_timeout: float = field(default=1, kw_only=True)

    _batch: list[dict] = field(default=Factory(list), kw_only=True)
    _last_batch_time: float = field(default=0, kw_only=True)

    def publish_event(self, event: BaseEvent | dict) -> None:
        self.futures_executor.submit(self._safe_try_publish_event, event)

    @abstractmethod
    def try_publish_event_payload(self, event_payload: dict) -> None:
        ...

    @abstractmethod
    def try_publish_event_payload_batch(self, event_payload_batch: list[dict]) -> None:
        ...

    def _safe_try_publish_event(self, event: BaseEvent | dict) -> None:
        try:
            event_payload = event if isinstance(event, dict) else event.to_dict()

            if self.batched:
                self._batch.append(event_payload)
                now = time.time()
                if len(self._batch) >= self.batch_size or now - self._last_batch_time >= self.batch_timeout:
                    self.try_publish_event_payload_batch(self._batch)
                    self._last_batch_time = now
                    self._batch = []
                return
            else:
                self.try_publish_event_payload(event_payload)
        except Exception as e:
            logger.error(e)

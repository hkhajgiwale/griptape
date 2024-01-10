from __future__ import annotations
from griptape.mixins import SerializableMixin
from typing import Any
import json
import uuid
from abc import ABC, abstractmethod
from attr import define, field, Factory
from marshmallow import class_registry
from marshmallow.exceptions import RegistryError
from griptape.schemas import BaseSchema


@define()
class BaseArtifact(SerializableMixin, ABC):
    id: str = field(default=Factory(lambda: uuid.uuid4().hex), kw_only=True, metadata={"serialize": True})
    name: str = field(
        default=Factory(lambda self: self.id, takes_self=True), kw_only=True, metadata={"serialize": True}
    )
    value: Any = field()
    type: str = field(
        default=Factory(lambda self: self.__class__.__name__, takes_self=True),
        kw_only=True,
        metadata={"serialize": True},
    )

    @classmethod
    def value_to_bytes(cls, value: Any) -> bytes:
        if isinstance(value, bytes):
            return value
        else:
            return str(value).encode()

    @classmethod
    def value_to_dict(cls, value: Any) -> dict:
        if isinstance(value, dict):
            dict_value = value
        else:
            dict_value = json.loads(value)

        return {k: v for k, v in dict_value.items()}

    @classmethod
    def from_dict(cls, data: dict) -> BaseArtifact:
        from griptape.artifacts import (
            TextArtifact,
            InfoArtifact,
            ErrorArtifact,
            BlobArtifact,
            CsvRowArtifact,
            ListArtifact,
            ImageArtifact,
        )

        class_registry.register("TextArtifact", BaseSchema.from_attrscls(TextArtifact))
        class_registry.register("InfoArtifact", BaseSchema.from_attrscls(InfoArtifact))
        class_registry.register("ErrorArtifact", BaseSchema.from_attrscls(ErrorArtifact))
        class_registry.register("BlobArtifact", BaseSchema.from_attrscls(BlobArtifact))
        class_registry.register("CsvRowArtifact", BaseSchema.from_attrscls(CsvRowArtifact))
        class_registry.register("ListArtifact", BaseSchema.from_attrscls(ListArtifact))
        class_registry.register("ImageArtifact", BaseSchema.from_attrscls(ImageArtifact))

        try:
            return class_registry.get_class(data["type"])().load(data)
        except RegistryError:
            raise ValueError("Unsupported artifact type")

    def to_text(self) -> str:
        return str(self.value)

    def __str__(self) -> str:
        return self.to_text()

    def __bool__(self) -> bool:
        return bool(self.value)

    def __len__(self) -> int:
        return len(self.value)

    @abstractmethod
    def __add__(self, other: BaseArtifact) -> BaseArtifact:
        ...

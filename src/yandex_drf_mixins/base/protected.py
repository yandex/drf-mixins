from itertools import islice
from typing import Any, Iterable

from django.db import models


def get_protected_object_name(
    protected_objects: Iterable[models.Model],
    *,
    limit: int | None,
    default: Any,
) -> str:
    objects = protected_objects if limit is None else islice(protected_objects, limit)
    names = [str(obj._meta.verbose_name) for obj in objects]
    return ", ".join(names) if names else str(default)

from itertools import islice
from typing import Any, Iterable

from django.db import models
from django.utils.functional import Promise


def get_protected_object_name(
    protected_objects: Iterable[models.Model],
    *,
    limit: int | None,
    default: Any,
) -> str:
    objects = protected_objects if limit is None else islice(protected_objects, limit)
    names = [str(obj._meta.verbose_name) for obj in objects]
    return ", ".join(names) if names else str(default)


def format_deletion_error_message(
    related_objects: Iterable[models.Model],
    *,
    template: str | Promise,
    limit: int | None,
    default: Any,
) -> str:
    object_name = get_protected_object_name(related_objects, limit=limit, default=default)
    return str(template) % {"object_name": object_name}

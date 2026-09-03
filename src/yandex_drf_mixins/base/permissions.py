from typing import Any, Iterable

from asgiref.sync import iscoroutinefunction


async def acheck_object_permissions(
    view: Any,
    request: Any,
    obj: Any,
    permissions: Iterable[Any],
) -> None:
    for permission in permissions:
        if iscoroutinefunction(permission.has_object_permission):
            allowed = await permission.has_object_permission(request, view, obj)
        else:
            allowed = permission.has_object_permission(request, view, obj)
        if not allowed:
            view.permission_denied(
                request,
                message=getattr(permission, "message", None),
                code=getattr(permission, "code", None),
            )

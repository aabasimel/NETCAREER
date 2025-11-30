"""
Standardized API response helpers.
"""

from typing import Any, Dict
from rest_framework.response import Response
from rest_framework import status


def ok(data: Dict[str, Any] | list[Any] | None = None, **extra) -> Response:
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return Response(payload, status=status.HTTP_200_OK)


def created(data: Dict[str, Any] | None = None, **extra) -> Response:
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return Response(payload, status=status.HTTP_201_CREATED)


def error(message: str, code: int = status.HTTP_400_BAD_REQUEST, **extra) -> Response:
    payload = {"success": False, "error": message}
    payload.update(extra)
    return Response(payload, status=code)

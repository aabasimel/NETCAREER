"""
Shared exception classes for consistent API error handling.
"""

from rest_framework.exceptions import APIException


class Conflict(APIException):
    status_code = 409
    default_detail = "Conflict"
    default_code = "conflict"


class UnprocessableEntity(APIException):
    status_code = 422
    default_detail = "Unprocessable Entity"
    default_code = "unprocessable_entity"


class TooManyRequests(APIException):
    status_code = 429
    default_detail = "Too Many Requests"
    default_code = "too_many_requests"

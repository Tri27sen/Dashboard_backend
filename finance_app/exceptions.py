"""
Custom exceptions for the finance API.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class PermissionDeniedException(APIException):
    """Exception raised when user lacks required permissions."""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class ValidationException(APIException):
    """Exception raised for invalid data."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input data.'
    default_code = 'validation_error'


class NotAuthenticatedException(APIException):
    """Exception raised when authentication is missing or invalid."""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication credentials were not provided.'
    default_code = 'not_authenticated'
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_message = None
        error_code = 'UNKNOWN_ERROR'

        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                error_message = exc.detail
            elif isinstance(exc.detail, list):
                error_message = exc.detail[0] if exc.detail else str(exc)
            else:
                error_message = str(exc.detail)
        else:
            error_message = str(exc)

        status_code = response.status_code
        if status_code == 400:
            error_code = 'VALIDATION_ERROR'
        elif status_code == 401:
            error_code = 'UNAUTHORIZED'
        elif status_code == 403:
            error_code = 'PERMISSION_DENIED'
        elif status_code == 404:
            error_code = 'NOT_FOUND'
        elif status_code >= 500:
            error_code = 'SERVER_ERROR'

        response.data = {
            'error': error_message,
            'status': 'error',
            'code': error_code
        }

    return response
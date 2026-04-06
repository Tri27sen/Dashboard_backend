"""
Custom authentication and exception handling for the API.
"""

from rest_framework.authentication import TokenAuthentication as BaseTokenAuth
from rest_framework.exceptions import AuthenticationFailed
from finance_app.models import User


class TokenAuthentication(BaseTokenAuth):
    """
    Custom token authentication.
    
    In production, this would use proper JWT or session tokens.
    For development, we accept any user ID as a simple token.
    
    Header format: "Authorization: Token <username>"
    """
    
    keyword = 'Token'
    
    def authenticate(self, request):
        """Authenticate using username-based token."""
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if not auth or auth[0].lower() != self.keyword.lower():
            return None
        
        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)
        
        token = auth[1]
        return self.authenticate_credentials(token)
    
    def authenticate_credentials(self, key):
        """Look up user by username (using username as token in dev)."""
        try:
            user = User.objects.get(username=key)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')
        
        if not user.is_active:
            raise AuthenticationFailed('User account is disabled.')
        
        return (user, key)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.
    
    All errors return a consistent format:
    {
        "error": "Error message",
        "status": "error",
        "code": "ERROR_CODE"
    }
    """
    from rest_framework.response import Response
    from rest_framework import status
    from rest_framework.views import exception_handler
    
    # Use default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Build custom response format
        error_message = None
        error_code = 'UNKNOWN_ERROR'
        
        # Extract error details
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                # Multiple field errors
                error_message = exc.detail
            elif isinstance(exc.detail, list):
                error_message = exc.detail[0] if exc.detail else str(exc)
            else:
                error_message = str(exc.detail)
        else:
            error_message = str(exc)
        
        # Determine error code from status code
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
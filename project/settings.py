AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    # ...
    'accounts.middleware.AccessControlMiddleware',
    # ...
] 
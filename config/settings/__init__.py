"""
Settings package para diferentes ambientes.
"""
# Cargar settings según ambiente
import os

from .base import *

env = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
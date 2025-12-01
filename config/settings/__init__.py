"""
Settings package para diferentes ambientes.
"""
from .base import *

# Cargar settings según ambiente
import os

env = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
"""
Modelos base para el sistema
"""
from django.db import models


class BaseModel(models.Model):
    """Modelo base con timestamps"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
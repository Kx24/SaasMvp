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


class EmailOutbox(models.Model):
    """
    Cola de emails transaccionales (#MED-01).

    EmailService encola acá en vez de abrir una conexión SMTP dentro del
    request cuando settings.EMAIL_ASYNC=True. El contenido ya viene
    renderizado (render_to_string es CPU local, no red) -- lo único que
    se difiere es el .send() real, que hace el comando
    send_pending_emails vía cron.
    """

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido (máximo de reintentos alcanzado)'),
    ]

    to_email = models.EmailField()
    from_email = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    text_content = models.TextField()
    reply_to = models.EmailField(blank=True)

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Email en cola'
        verbose_name_plural = 'Emails en cola'
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.to_email} - {self.subject} ({self.status})"
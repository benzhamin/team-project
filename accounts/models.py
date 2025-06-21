from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    Role = (
        ('admin', _('Admin')),
        ('patient', _('Patient')),
        ('doctor', _('Doctor')),
        ('receptionist', _('Receptionist')),
    )
    role = models.CharField(
        max_length=20,
        choices=Role,
        default='patient',
        verbose_name=_('Role')
    )

    def __str__(self):
        return f"{self.id} {self.username}"
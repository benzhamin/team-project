from django.db import models
from accounts.models import User


# 📅 Запись на консультацию
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланирована'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_doctor')
    datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient} -> {self.doctor} @ {self.datetime}"


# 💬 Чат (сообщения)
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

    def __str__(self):
        return f"{self.sender} -> {self.receiver} : {self.text[:30]}"


# 📁 Медицинские файлы
class MedicalFile(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_files')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    file = models.FileField(upload_to='medical_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient} - {self.file.name}"
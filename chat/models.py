from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone

User = get_user_model()


class Chat(models.Model):
    CHAT_TYPES = [
        ('patient_doctor', 'Patient-Doctor'),
        ('group', 'Group Chat'),
        ('support', 'Support Chat'),
    ]
    
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES, default='patient_doctor')
    participants = models.ManyToManyField(User, related_name='chats')
    title = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.title:
            return self.title
        participants_names = ', '.join([user.username for user in self.participants.all()[:3]])
        return f"Chat: {participants_names}"
    
    @property
    def last_message(self):
        return self.messages.filter(is_deleted=False).order_by('-timestamp').first()
    
    @property
    def unread_count(self, user=None):
        if user:
            return self.messages.filter(
                is_deleted=False,
                timestamp__gt=user.last_read_timestamp or timezone.now() - timezone.timedelta(days=30)
            ).count()
        return 0


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),
        ('appointment', 'Appointment Related'),
    ]
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    
    # Text content
    text = models.TextField(blank=True)
    
    # File attachments
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    file = models.FileField(
        upload_to='chat_files/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'])]
    )
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)
    
    # Message metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)
    
    # Reply functionality
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    # Appointment reference
    appointment = models.ForeignKey('medlink.Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_messages')
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        if self.text:
            return f"{self.sender.username}: {self.text[:50]}..."
        elif self.image:
            return f"{self.sender.username}: [Image]"
        elif self.file:
            return f"{self.sender.username}: [File: {self.file_name}]"
        return f"{self.sender.username}: [System Message]"
    
    def save(self, *args, **kwargs):
        # Set file name and size if file is uploaded
        if self.file and not self.file_name:
            self.file_name = self.file.name.split('/')[-1]
            self.file_size = self.file.size
        
        # Set message type based on content
        if self.image:
            self.message_type = 'image'
        elif self.file:
            self.message_type = 'file'
        elif self.appointment:
            self.message_type = 'appointment'
        
        super().save(*args, **kwargs)
    
    def mark_as_read(self, user):
        """Mark message as read by specific user"""
        if user not in self.read_by.all():
            self.read_by.add(user)
            self.is_read = True
            self.save()
    
    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.save()


class ChatParticipant(models.Model):
    """Track participant status in chats"""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participant_status')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_participant_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    last_read_timestamp = models.DateTimeField(default=timezone.now)
    is_muted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('chat', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.chat}"
    
    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    def mark_as_read(self, timestamp):
        """Mark all messages up to timestamp as read"""
        if timestamp > self.last_read_timestamp:
            self.last_read_timestamp = timestamp
            self.save(update_fields=['last_read_timestamp'])


class ChatNotification(models.Model):
    """Track chat notifications for users"""
    NOTIFICATION_TYPES = [
        ('new_message', 'New Message'),
        ('mention', 'Mention'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_notifications')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='new_message')
    title = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])


class ChatInvitation(models.Model):
    """Handle chat invitations between users"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='invitations')
    message = models.TextField(blank=True, help_text='Optional invitation message')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation from {self.inviter.username} to {self.invitee.username}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def accept(self):
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
        
        # Add invitee to chat participants
        self.chat.participants.add(self.invitee)
        
        # Create participant status
        ChatParticipant.objects.get_or_create(
            chat=self.chat,
            user=self.invitee
        )
    
    def decline(self):
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()

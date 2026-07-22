from django.db import models
from django.contrib.auth.models import User

class GroupChat(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name="group_chats")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class GroupMessageRead(models.Model):
    """Track which users have read which group messages"""
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='group_reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {'Read' if self.is_read else 'Unread'}"
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(
        upload_to='messages/images/',
        blank=True,
        null=True
    )

    video = models.FileField(
        upload_to='messages/videos/',
        blank=True,
        null=True
    )

    file = models.FileField(
        upload_to='messages/files/',
        blank=True,
        null=True
    )
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.message[:30]}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()
    
    @classmethod
    def get_conversation(cls, user1, user2):
        from django.db.models import Q
        return cls.objects.filter(
            Q(sender=user1, receiver=user2) |
            Q(sender=user2, receiver=user1)
        ).order_by('created_at')
    
    @classmethod
    def get_unread_count(cls, user):
        return cls.objects.filter(receiver=user, is_read=False).count()
    
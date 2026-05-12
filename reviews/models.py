from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    
    rating = models.IntegerField()  # 1 to 5
    comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"{self.reviewer} -> {self.reviewed_user} ({self.rating})"

# Create your models here.

# Create your models here.

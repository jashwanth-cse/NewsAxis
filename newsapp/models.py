from django.db import models
from django.utils import timezone
class CollegeTweet(models.Model):
    tweet_id = models.CharField(max_length=50, unique=True)
    text = models.TextField()
    image = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField()
    url = models.URLField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Tweet {self.tweet_id} - {self.text[:50]}"
from django.db import models
from django.contrib.auth.models import User

class Article(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Waiting for review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=10)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    images = models.JSONField(null=True, blank=True)  # Store image paths as JSON

    def __str__(self):
        return self.title

    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
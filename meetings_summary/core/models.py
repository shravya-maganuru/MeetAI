from django.db import models

class Job(models.Model):
    """
    Model to track the status of long-running transcription and summary tasks.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETE', 'Complete'),
        ('FAILED', 'Failed'),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Job {self.id} - {self.status}"

class Meeting(models.Model):
    """
    Model to store the final result of a meeting analysis.
    Links directly to a job, so we know which request generated this meeting data.
    """
    job = models.OneToOneField(Job, on_delete=models.CASCADE, primary_key=True)
    title = models.CharField(max_length=255)
    audio_file = models.FileField(upload_to='recordings/')
    transcript = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    todo_list = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
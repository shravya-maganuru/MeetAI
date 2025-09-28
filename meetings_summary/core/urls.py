from django.urls import path
from . import views

urlpatterns = [
    # API to start the long-running job. Returns a Job ID immediately.
    path('start-summary-job/', views.start_summary_job, name='start_summary_job'),
    
    # API for the frontend to poll (repeatedly check) the job status.
    path('check-job-status/<int:job_id>/', views.check_job_status, name='check_job_status'),
]
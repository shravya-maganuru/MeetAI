import openai
import json
import os
import threading
import traceback

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone  #
from moviepy import VideoFileClip
from .models import Meeting, Job

# Frontend Logic

def homepage(request):
    """Renders the main index.html file (the frontend)."""
    return render(request, 'index.html')

@csrf_exempt
def start_summary_job(request):
    """
    API endpoint: Receives the file, creates a job, launches background processing,
    and returns a Job ID immediately (non-blocking).
    
    CRITICAL FIX: Reads the file content and name in the main thread before Django closes it,
    then passes the raw data to the background thread.
    """
    if request.method == 'POST' and request.FILES.get('audio_file'):
        uploaded_file = request.FILES['audio_file']
        
        # Read the file data and add it to the main thread
        try:
            file_content = uploaded_file.read()
            file_name = uploaded_file.name
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Could not read uploaded file: {str(e)}"}, status=400)
        
        # Create a PENDING Job in the database immediately
        job = Job.objects.create(status='PENDING')
        
        try:
            # Launch the long-running process in a separate thread
            # Pass raw content and name, not the closed file object.
            thread = threading.Thread(
                target=process_in_background,
                args=(job.id, file_content, file_name)
            )
            thread.start()
            
            # Return Job ID immediately to the frontend (202 Accepted)
            return JsonResponse({"status": "PENDING", "job_id": job.id}, status=202)
        
        except Exception as e:
            job.status = 'FAILED'
            job.error_message = f"Failed to start thread: {str(e)}"
            job.completed_at = timezone.now()
            job.save()
            return JsonResponse({"status": "FAILED", "message": "Could not launch processing."}, status=500)
    
    return JsonResponse({"status": "error", "message": "Invalid request or file missing."}, status=400)

def check_job_status(request, job_id):
    """
    API endpoint: Allows the frontend to check the status of a long-running job.
    Returns the final results if the job is COMPLETE.
    """
    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Job not found."}, status=404)

    if job.status == 'COMPLETE':
        try:
            meeting = Meeting.objects.get(job=job)
            return JsonResponse({
                "status": "COMPLETE",
                "summary": meeting.summary,
                "todo_list": meeting.todo_list,
                "transcript": meeting.transcript,
                "title": meeting.title,
            })
        except Meeting.DoesNotExist:
            return JsonResponse({"status": "FAILED", "message": "Job complete, but result data missing."}, status=500)
            
    return JsonResponse({"status": job.status, "message": job.error_message})

# Backend Logic

def process_in_background(job_id, file_content, file_name):
    """
    The function that runs in a separate thread to handle long-running tasks.
    It takes raw file content (bytes) and rebuilds a working ContentFile.
    """
    job = Job.objects.get(pk=job_id)
    job.status = 'RUNNING'
    job.save()
    
    # Rebuild the file object from raw content
    cloned_file = ContentFile(file_content, name=file_name)

    try:
        # File Handling and Audio Extraction 
        
        # Determine file extension
        _, file_extension = os.path.splitext(cloned_file.name)
        file_extension = file_extension.lower()
        
        audio_content = None
        temp_audio_path = None 

        # Video Processing Path
        if file_extension in ['.mp4', '.mov', '.avi']:
            job.error_message = f"Extracting audio from {cloned_file.name}..."
            job.save()
            
            # Save the cloned video data temporarily (moviepy needs a physical file path)
            temp_video_path = os.path.join(settings.MEDIA_ROOT, 'temp_videos', cloned_file.name)
            os.makedirs(os.path.dirname(temp_video_path), exist_ok=True)

            with open(temp_video_path, 'wb+') as f:
                f.write(file_content)
            
            # Extract audio
            video_clip = VideoFileClip(temp_video_path)
            
            # Use tempfile path for extracted audio
            temp_audio_name = f"{file_name}_extracted.mp3"
            temp_audio_path = os.path.join(settings.MEDIA_ROOT, 'temp_audio', temp_audio_name)
            os.makedirs(os.path.dirname(temp_audio_path), exist_ok=True)
            
            video_clip.audio.write_audiofile(temp_audio_path, logger=None)
            video_clip.close()
            os.remove(temp_video_path) # Clean up temp video

            # Open the extracted audio file for the next step
            with open(temp_audio_path, 'rb') as f:
                audio_content = ContentFile(f.read(), name=temp_audio_name)
        
        # Audio Processing Path
        elif file_extension in ['.mp3', '.m4a', '.wav', '.ogg']:
            audio_content = cloned_file
            
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

        # Save File to DB and Get Path for OpenAI
        
        # Create the final Meeting object now, associated with the Job
        meeting = Meeting(job=job, title=file_name)
        meeting.audio_file.save(audio_content.name, audio_content)
        
        # Clean up temp audio file if created (only if we extracted it)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            
        # OpenAI API Calls (Long-running)
        
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Transcription (Whisper)
        job.error_message = "Transcribing audio..."
        job.save()
        
        # Pass the physical file path to Whisper
        with open(meeting.audio_file.path, "rb") as audio_file_rb:
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_rb
            )
        transcript_text = transcript_response.text
        meeting.transcript = transcript_text
        
        # B. Summarization (GPT)
        job.error_message = "Generating summary and to-do list..."
        job.save()
        
        prompt = (
            "You are a professional assistant. Summarize the following meeting transcript. "
            "Also, extract all action items and format them as a bulleted list. "
            "The output MUST be in a single JSON object with two keys: 'summary' (string) and 'todo_list' (string)."
            f"\n\nTRANSCRIPT: {transcript_text}"
        )
        
        completion = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a professional meeting assistant. Output ONLY a valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        llm_output = completion.choices[0].message.content
        parsed_output = json.loads(llm_output)

        # Final Save and Completion
        meeting.summary = parsed_output.get('summary', '')
        meeting.todo_list = parsed_output.get('todo_list', '')
        meeting.save()

        job.status = 'COMPLETE'
        job.completed_at = timezone.now()
        job.error_message = "" 
        job.save()

    except Exception as e:
        # Catch and log any errors that occur during processing
        job.status = 'FAILED'
        job.error_message = f"Processing Error: {str(e)}\n\n{traceback.format_exc()}"
        job.completed_at = timezone.now()
        job.save()
        
        # If the meeting object was created, clean up the audio file on failure
        if 'meeting' in locals():
            # Check if the audio file object exists before trying to delete it
            if hasattr(meeting, 'audio_file') and meeting.audio_file:
                meeting.audio_file.delete(save=False)
            meeting.delete() 

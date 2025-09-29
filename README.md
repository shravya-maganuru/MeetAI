# 🎙️ AI Meeting Summarizer

This project is a full-stack web application designed to automatically transcribe, summarize, and extract actionable tasks from meeting recordings (audio or video). It uses a specialized **Asynchronous Polling** architecture to handle long-running API tasks without freezing the user interface, ensuring a robust and professional user experience.

---

## ✨ Key Features & Architectural Highlights

This project was built specifically to solve the common full-stack challenge of **HTTP Request Timeouts** during long API processes.

* **Architected Asynchronous AI Pipeline:** Designed and implemented a non-blocking **Asynchronous Polling** solution using **Django Threading** to eliminate HTTP timeouts during meeting summarization and seamlessly integrate the powerful **GPT-5 nano** model.

* **Resilient File Processing & Data Management:** Engineered robust processing using **FFmpeg** and custom logic to handle multi-format inputs (MP4/MP3) and ensure analysis data is securely persisted and retrieved from a **MySQL** environment.

* **Secure & Scalable Stack:** Built with the high-level Django framework for reliable backend operations and data integrity.

---

## 🛠️ Tech Stack

| **Component** | **Technology** | **Role** |
| :--- | :--- | :--- |
| **Backend Framework** | **Django** (Python) | Routing, ORM, API endpoints, Authentication (Admin). |
| **Database** | **MySQL** | Persistent storage for \`Jobs\` and \`Meeting\` summaries. |
| **Asynchronicity** | **Python \`threading\`** | Runs long Whisper/GPT tasks in the background to avoid timeouts. |
| **AI Integration** | **OpenAI Whisper** (Transcription), **GPT-5 nano** (Summarization). | Speech-to-Text and Generative Analysis. |
| **File Processing** | **FFmpeg / \`moviepy\`** | Audio extraction from video files. |
| **Frontend** | **HTML, CSS, JavaScript** | Simple, clean UI and the core polling logic. |

---

## 🚀 Setup and Installation

Follow these steps to get the application running locally.

### Prerequisites

1. Python 3.8+
2. MySQL Server (Running locally, e.g., on port 3306)
3. FFmpeg: Must be installed on your system and added to your environment's PATH.
4. OpenAI API Key: Obtain a key and ensure your account has active billing/quota.

### 1. Clone and Setup VENV

```bash
# Assuming you are in the root directory (MEETAI)
git clone [YOUR REPO URL] meetings_summary
cd meetings_summary

# Create and activate virtual environment
python -m venv .venv
.venv/Scripts/activate # Windows
# source .venv/bin/activate # Linux/macOS
```

#### Install Dependencies

```bash
# Install dependencies (from the generated requirements.txt file)
pip install -r requirements.txt
```

### 2. Configuration and Environment

The `SECRET_KEY` is crucial for Django's security. Generate a strong key and use environment variables to store all credentials.

#### Generating the Django SECRET_KEY
Open your Python shell (within your active VENV) and run the following commands to generate a secure key:

```bash
python
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
# Copy the long string that is printed.
```

#### Creating the .env File
Create a file named `.env` in your root project directory (`meetings_summary/`) and fill it with your credentials:

```bash
# .env File
SECRET\_KEY="<Paste the generated Django Secret Key here>"
OPENAI\_API\_KEY="<Your OpenAI API Key>"
```

### 3. Database Setup
Run the migrations to create the necessary tables in your `meetingai` database:

```bash
python manage.py makemigrations core
python manage.py migrate
```

### 4. Run the Application
Start the Django development server:
```bash
python manage.py runserver
```

Open your browser and navigate to: `http://127.0.0.1:8000/`

## 🎯 Testing the Asynchronous Workflow

1. Upload: Select an audio or video file.

2. Start: Click the Summarize Meeting button.

3. Polling: The UI will immediately show a "Job started... Processing audio..." message. Your browser is now polling the server every 3 seconds, keeping the connection stable.

4. Completion: Once the background thread completes the GPT analysis, the results will instantly appear on the page.
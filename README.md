# 🎙️ Noteefy: The Ultimate AI Audio Recorder & Transcriber

**Noteefy** is a powerful desktop application built for anyone who needs to capture professional-grade audio, from meetings and interviews to speeches and podcasts. It cleans the audio with advanced noise reduction and uses cutting-edge AI to transform hours of recordings into beautifully structured PDF notes in seconds.

---

## ✨ Features

### 🚀 State-of-the-Art Transcription
*   **NVIDIA Parakeet TDT:** Built-in support for the world's most accurate English transcription model (WER 6.05%).
*   **Turbo Fallback (Groq):** Blazing fast fallback using Whisper Large v3 on Groq Cloud if primary APIs are busy.
*   **Bundled MP3 Encoding:** Built-in `lameenc` compression shrinks 2-hour recordings by **95%** with zero external dependencies (no FFmpeg needed).
*   **16kHz Optimization:** Records natively in 16kHz mono to maximize AI accuracy while saving disk space.

### 📝 Intelligent Multi-Purpose Notes
*   **AI Structuring:** Powered by Llama 3 to create summaries, key concepts, detailed bullet points, and action items for any session.
*   **Professional PDF Export:** One-click conversion to clean, structured PDF documents.
*   **Smart Filenaming:** Automatically names exports by **Speaker and Date** (e.g., `Expert_Name_12-18.pdf`) for effortless organization.

### 🛡️ Robust & Portable
*   **Offline Queue:** Recordings are saved locally and can be processed whenever you're back online.
*   **Noise Cleaning:** Advanced noise reduction clarifying recordings from busy offices or large halls.


---

## 🛠️ Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-username/noteefy.git
cd noteefy
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```bash
GROQ_API_KEY=your_key_here
CLOUD_BACKEND_URL=optional_fallback_url
```

### 3. Run
```bash
python main.py
```

---

## 🏗️ Project Components

| Module | Description |
| :--- | :--- |
| `main.py` | Modern Dark-mode GUI using **CustomTkinter**. |
| `recorder.py` | Optimized 16kHz audio capture with **sounddevice**. |
| `transcriber.py` | Zero-dependency MP3 encoding and Multi-Cloud orchestration. |
| `notes_generator.py`| **Groq/Llama 3** prompt engineering for generalized note-taking. |
| `exporter.py` | HTML-to-PDF engine using **xhtml2pdf**. |
| `cleaner.py` | Advanced noise reduction using **noisereduce**. |

---

## 📄 License
Designed and developed by **Ghasty**. MIT License.

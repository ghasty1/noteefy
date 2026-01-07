import os
import sys
from dotenv import load_dotenv

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Load environment variables BEFORE importing local modules
load_dotenv(resource_path(".env"))

from modules.exporter import Exporter
from PIL import Image
import customtkinter as ctk
import threading
import time
import json
import requests
from tkinter import messagebox
from modules.recorder import AudioRecorder
from modules.cleaner import AudioCleaner
from modules.transcriber import CloudTranscriber
from modules.notes_generator import NotesGenerator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class NoteefyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Noteefy - AI Transcription & Notes")
        self.geometry("600x650") # Slightly taller for logo
        
        # Security Check
        self.verify_remote_access()

        # Set Window Icon
        try:
            self.iconbitmap(resource_path("logo.ico"))
        except Exception as e:
            print(f"Could not load window icon: {e}")

        # Modules
        self.recorder = AudioRecorder(output_dir="output")
        self.cleaner = AudioCleaner()
        self.transcriber = None # Initialized on process (needs URL)
        self.notes_gen = NotesGenerator()
        self.exporter = Exporter()

        # State
        self.is_recording = False
        self.current_recording = None
        self.pending_files = [] # List of paths to process later

        self.load_pending() # Check for existing pending files
        self._init_ui()

    def verify_remote_access(self):
        """
        Checks a remote URL to authorize the application.
        - Fails OPEN on connection error (runs offline).
        - Fails CLOSED if server explicitly denies (status != ok).
        """
        control_url = "https://inquote.onrender.com/health"
        try:
            response = requests.get(control_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") != "ok":
                    messagebox.showerror("Access Denied", "This version of Noteefy has been deactivated by the administrator.")
                    sys.exit()
            else:
                # Server reached but returned error (e.g. 500, 404). Run anyway? 
                # User said "Let the app run if the server is not reachable".
                pass
        except Exception:
            # Connection failed/Timeout - Fail Open
            pass

    def _init_ui(self):
        # Brand Colors
        self.brand_teal = "#00deed"
        self.brand_navy = "#023551"
        self.brand_hover = "#00c4d1"

        # Header Logo (Transparent)
        try:
            logo_img = Image.open(resource_path("logo_new_ui.png"))
            w, h = logo_img.size
            aspect = h / w
            new_w = 280
            new_h = int(new_w * aspect)
            
            self.logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(new_w, new_h))
            self.header = ctk.CTkLabel(self, image=self.logo_ctk, text="")
        except Exception as e:
            print(f"Logo load error: {e}")
            self.header = ctk.CTkLabel(self, text="Noteefy", font=("Roboto", 28, "bold"), text_color=self.brand_teal)
            
        self.header.pack(pady=25)

        # Metadata Frame
        self.meta_frame = ctk.CTkFrame(self, fg_color="transparent") # Clean look
        self.meta_frame.pack(pady=5, padx=20, fill="x")

        self.topic_entry = ctk.CTkEntry(self.meta_frame, placeholder_text="Topic / Project Name", border_color=self.brand_navy)
        self.topic_entry.pack(pady=8, padx=10, fill="x")

        self.speaker_entry = ctk.CTkEntry(self.meta_frame, placeholder_text="Speaker / Source", border_color=self.brand_navy)
        self.speaker_entry.pack(pady=8, padx=10, fill="x")

        # Controls
        self.record_btn = ctk.CTkButton(
            self, 
            text="Start Recording", 
            command=self.toggle_recording,
            fg_color=self.brand_teal, 
            hover_color=self.brand_hover,
            text_color="black", # Contrast with bright teal
            height=55,
            font=("Roboto", 18, "bold"),
            corner_radius=15
        )
        self.record_btn.pack(pady=20, padx=20, fill="x")

        self.process_btn = ctk.CTkButton(
            self, 
            text="Process Pending Files", 
            command=self.start_processing_thread,
            fg_color=self.brand_navy,
            hover_color="#1a4d6b",
            state="disabled" if not self.pending_files else "normal",
            corner_radius=10
        )
        self.process_btn.pack(pady=10, padx=20, fill="x")

        self.manage_queue_btn = ctk.CTkButton(
            self, 
            text="Manage Queue", 
            command=self.open_queue_manager,
            fg_color="transparent",
            border_width=1,
            border_color=self.brand_navy,
            state="disabled" if not self.pending_files else "normal",
            corner_radius=10
        )
        self.manage_queue_btn.pack(pady=5, padx=20, fill="x")

        # Log Console Header with Clear Button
        self.log_header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.log_header_frame.pack(pady=(10, 0), padx=20, fill="x")
        
        self.log_label = ctk.CTkLabel(self.log_header_frame, text="Activity Log", font=("Roboto", 12, "bold"))
        self.log_label.pack(side="left")

        self.clear_btn = ctk.CTkButton(
            self.log_header_frame, 
            text="Clear Log", 
            width=80, 
            height=24,
            command=self.clear_log,
            fg_color="transparent",
            border_width=1,
            border_color=self.brand_navy,
            font=("Roboto", 11)
        )
        self.clear_btn.pack(side="right")

        self.log_box = ctk.CTkTextbox(self, state="disabled", height=150) # Reduced height slightly
        self.log_box.pack(pady=(5, 20), padx=20, fill="both", expand=True)

    def clear_log(self):
        self.log_header_frame = None # Not related, just clearing
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"> {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def toggle_recording(self):
        if not self.is_recording:
            # Start
            self.current_recording = self.recorder.start_recording()
            self.is_recording = True
            self.record_btn.configure(text="Stop Recording", fg_color="#ff4d4d", hover_color="#cc0000")
            self.process_btn.configure(state="disabled")
            self.log("Recording started...")
        else:
            # Stop
            self.current_recording = self.recorder.stop_recording()
            self.is_recording = False
            self.record_btn.configure(text="Start Recording", fg_color=self.brand_teal, hover_color=self.brand_hover)
            self.process_btn.configure(state="normal")
            self.log(f"Recording saved: {self.current_recording}")
            
            # Auto-Process
            self.pending_files.append(self.current_recording)
            self.save_pending()
            self.start_processing_thread()

    def load_pending(self):
        try:
            if os.path.exists("pending.json"):
                with open("pending.json", "r") as f:
                    self.pending_files = json.load(f)
        except:
            self.pending_files = []

    def save_pending(self):
        with open("pending.json", "w") as f:
            json.dump(self.pending_files, f)

    def start_processing_thread(self):
        threading.Thread(target=self.process_workflow).start()

    def process_workflow(self):

        if not self.pending_files:
            self.log("No pending files to process.")
            return

        self.process_btn.configure(state="disabled")
        
        # Process Copy of list
        files_to_process = list(self.pending_files)
        
        for audio_path in files_to_process:
            self.log(f"Processing: {os.path.basename(audio_path)}...")
            try:
                # 1. Clean
                self.log("Step 1/4: Cleaning audio...")
                clean_path = self.cleaner.clean_audio(audio_path, aggressive=False)
                
                # 2. Transcribe
                self.log("Step 2/4: Transcribing...")
                self.transcriber = CloudTranscriber()
                transcript = self.transcriber.transcribe(clean_path)
                
                # 3. Generate Notes
                self.log("Step 3/4: Generating Notes...")
                topic = self.topic_entry.get() or "General Session"
                speaker = self.speaker_entry.get() or "Unknown Speaker"
                date_time = time.strftime("%Y-%m-%d %H:%M:%S")
                
                notes = self.notes_gen.generate_notes(transcript, topic, speaker, date_time)
                
                # 4. Export (Named after Topic, Speaker and Date)
                self.log("Step 4/4: Exporting PDF...")
                date_str = time.strftime("%m-%d") # Date without year
                clean_topic = "".join([c for c in topic if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
                clean_speaker = "".join([c for c in speaker if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
                
                pdf_filename = f"{clean_topic}_{clean_speaker}_{date_str}.pdf"
                pdf_path = os.path.join("output", pdf_filename)
                
                result = self.exporter.export_to_pdf(notes, pdf_path)
                if "Error" in result:
                    self.log(result)
                else:
                    self.log(f"SUCCESS! Saved to: {pdf_path}")
                    os.startfile(pdf_path)
                    
                    # Cleanup & Remove from pending
                    self.log("Cleaning up temporary audio files...")
                    try:
                        os.remove(audio_path)
                        os.remove(clean_path)
                    except Exception as cleanup_err:
                        self.log(f"Cleanup Warning: {cleanup_err}")

                    self.pending_files.remove(audio_path)
                    self.save_pending()

            except Exception as e:
                self.log(f"ERROR: {str(e)}")
                if "Connection" in str(e) or "Max retries" in str(e):
                    self.log("OFFLINE DETECTED. File kept in queue.")
                    break # Stop processing rest of queue if offline
                else:
                    # Non-connection error (e.g. file bad), maybe skip?
                    # For now, keep in queue to be safe.
                    self.log("Failed. Keeping in queue.")
        
        self.process_btn.configure(text=f"Process Pending ({len(self.pending_files)})", state="normal" if self.pending_files else "disabled")
        self.manage_queue_btn.configure(state="normal" if self.pending_files else "disabled")

    def open_queue_manager(self):
        """ Opens a popup window to manage/discard pending recordings. """
        manager = ctk.CTkToplevel(self)
        manager.title("Manage Pending Queue")
        manager.geometry("450x400")
        manager.attributes("-topmost", True)

        label = ctk.CTkLabel(manager, text="Pending Recordings", font=("Roboto", 16, "bold"))
        label.pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(manager, width=400, height=300)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.refresh_queue_ui(scroll_frame)

    def refresh_queue_ui(self, frame):
        # Clear frame
        for widget in frame.winfo_children():
            widget.destroy()

        if not self.pending_files:
            ctk.CTkLabel(frame, text="Queue is empty.").pack(pady=20)
            return

        for path in self.pending_files:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(pady=5, fill="x")

            filename = os.path.basename(path)
            name_label = ctk.CTkLabel(row, text=filename, anchor="w")
            name_label.pack(side="left", padx=10, fill="x", expand=True)

            discard_btn = ctk.CTkButton(
                row, 
                text="Discard", 
                width=70, 
                height=24, 
                fg_color="#ff4d4d", 
                hover_color="#cc0000",
                command=lambda p=path: self.discard_recording(p, frame)
            )
            discard_btn.pack(side="right", padx=10)

    def discard_recording(self, path, frame):
        """ Removes a recording from the queue and deletes the file. """
        if path in self.pending_files:
            self.pending_files.remove(path)
            self.save_pending()
            
            # Update Main UI buttons
            self.process_btn.configure(text=f"Process Pending ({len(self.pending_files)})", state="normal" if self.pending_files else "disabled")
            self.manage_queue_btn.configure(state="normal" if self.pending_files else "disabled")
            
            # Refresh Manager UI
            self.refresh_queue_ui(frame)
            self.log(f"Discarded: {os.path.basename(path)}")
            
            # Optional: Delete actual file
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                self.log(f"Cleanup Error: {e}")

if __name__ == "__main__":
    app = NoteefyApp()
    app.mainloop()

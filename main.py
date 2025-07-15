import os
import pyaudio
import wave
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, font, filedialog, messagebox
from openai import AzureOpenAI
from dotenv import load_dotenv
import re

class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Client")
        self.root.geometry("600x450")

        self.is_recording = False
        self.frames = []
        self.audio_file_path = "temp_recording.wav"
        self.current_transcript = None  # Store parsed transcript

        # --- Style Configuration ---
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        # Define fonts
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI", size=10)
        
        # Define colors
        self.BG_COLOR = "#282c34"
        self.TEXT_COLOR = "white" # Changed from "#abb2bf" for better contrast
        self.BUTTON_BG = "#61afef"
        self.BUTTON_FG = "black" # Changed from "white" for better contrast
        self.BUTTON_HOVER = "#528bce"
        self.TEXT_AREA_BG = "#21252b"
        self.DISABLED_FG = "#84888c"

        # Configure root window
        self.root.configure(bg=self.BG_COLOR)

        # Configure ttk styles
        self.style.configure("TFrame", background=self.BG_COLOR)
        self.style.configure("TButton", 
                             background=self.BUTTON_BG, 
                             foreground=self.BUTTON_FG, 
                             font=self.default_font, 
                             padding=10,
                             borderwidth=0,
                             relief="flat")
        self.style.map("TButton",
            background=[("active", self.BUTTON_HOVER)],
            relief=[("pressed", "sunken")],
            foreground=[("disabled", self.DISABLED_FG)])
        
        self.style.configure("TLabel", background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=self.default_font)

        # Load environment variables and initialize OpenAI client
        load_dotenv()
        whisper_api_key = os.getenv("AZURE_OPENAI_WHISPER_API_KEY")
        azure_whisper_endpoint = os.getenv("AZURE_OPENAI_WHISPER_ENDPOINT")
        self.whisper_deployment = os.getenv("AZURE_OPENAI_WHISPER_DEPLOYMENT")

        gpt_api_key = os.getenv("AZURE_OPENAI_GPT_API_KEY")
        azure_gpt_endpoint = os.getenv("AZURE_OPENAI_GPT_ENDPOINT")
        self.gpt_deployment = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")

        if not all([whisper_api_key, azure_whisper_endpoint, self.whisper_deployment, gpt_api_key, self.gpt_deployment, azure_gpt_endpoint]):
            self.show_error("Please set Azure credentials and deployment names in .env file.\nRequired: AZURE_OPENAI_WHISPER_API_KEY, AZURE_OPENAI_WHISPER_ENDPOINT, AZURE_OPENAI_WHISPER_DEPLOYMENT, AZURE_OPENAI_GPT_API_KEY, AZURE_OPENAI_GPT_DEPLOYMENT, AZURE_OPENAI_GPT_ENDPOINT")
            return

        self.whisper_client = AzureOpenAI(
            api_key=whisper_api_key,
            azure_endpoint=azure_whisper_endpoint,
            api_version="2024-12-01-preview"
        )
        self.gpt_client = AzureOpenAI(
            api_key=gpt_api_key,
            azure_endpoint=azure_gpt_endpoint,
            api_version="2025-01-01-preview"
        )

        # --- UI Elements ---
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Recording Tab
        self.recording_frame = ttk.Frame(self.notebook, padding="20 10 20 10")
        self.notebook.add(self.recording_frame, text="Voice Recording")

        # Meeting Notes Tab
        self.notes_frame = ttk.Frame(self.notebook, padding="20 10 20 10")
        self.notebook.add(self.notes_frame, text="Meeting Notes")

        self.setup_recording_tab()
        self.setup_meeting_notes_tab()
        
        self.status_bar = ttk.Label(root, text="Ready", padding="10 5 10 5")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_recording_tab(self):
        button_frame = ttk.Frame(self.recording_frame)
        button_frame.pack(pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Recording", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Recording", command=self.stop_recording, style="TButton", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.copy_button = ttk.Button(self.recording_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=5)

        self.output_text = scrolledtext.ScrolledText(self.recording_frame, wrap=tk.WORD, state=tk.DISABLED, bg=self.TEXT_AREA_BG, fg=self.TEXT_COLOR, font=self.default_font, relief="flat", borderwidth=2)
        self.output_text.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

    def setup_meeting_notes_tab(self):
        # Upload section
        upload_frame = ttk.Frame(self.notes_frame)
        upload_frame.pack(pady=10, fill=tk.X)

        ttk.Label(upload_frame, text="Upload VTT Transcript File:").pack(anchor=tk.W, pady=(0, 5))
        
        file_select_frame = ttk.Frame(upload_frame)
        file_select_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_path_var = tk.StringVar()
        self.file_path_entry = ttk.Entry(file_select_frame, textvariable=self.file_path_var, state="readonly")
        self.file_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.browse_button = ttk.Button(file_select_frame, text="Browse", command=self.browse_vtt_file)
        self.browse_button.pack(side=tk.RIGHT)

        # Buttons frame
        buttons_frame = ttk.Frame(upload_frame)
        buttons_frame.pack(pady=5, fill=tk.X)

        self.generate_notes_button = ttk.Button(buttons_frame, text="Generate Meeting Notes", command=self.generate_meeting_notes, state=tk.DISABLED)
        self.generate_notes_button.pack(side=tk.LEFT, padx=(0, 5))

        # Question section
        question_frame = ttk.Frame(self.notes_frame)
        question_frame.pack(pady=10, fill=tk.X)

        ttk.Label(question_frame, text="Ask a question about the transcript:").pack(anchor=tk.W, pady=(0, 5))
        
        question_input_frame = ttk.Frame(question_frame)
        question_input_frame.pack(fill=tk.X, pady=(0, 5))

        self.question_var = tk.StringVar()
        self.question_entry = ttk.Entry(question_input_frame, textvariable=self.question_var, state=tk.DISABLED)
        self.question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.question_entry.bind('<Return>', self.ask_question_enter)

        self.ask_question_button = ttk.Button(question_input_frame, text="Ask Question", command=self.ask_question, state=tk.DISABLED)
        self.ask_question_button.pack(side=tk.RIGHT)

        # Output section
        self.notes_output = scrolledtext.ScrolledText(self.notes_frame, wrap=tk.WORD, state=tk.DISABLED, bg=self.TEXT_AREA_BG, fg=self.TEXT_COLOR, font=self.default_font, relief="flat", borderwidth=2)
        self.notes_output.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

        # Copy notes button
        self.copy_notes_button = ttk.Button(self.notes_frame, text="Copy Response to Clipboard", command=self.copy_notes_to_clipboard)
        self.copy_notes_button.pack(pady=5)

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.set_status_text("Recording...")
        self.set_output_text("Recording...")

        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.set_status_text("Finished recording. Transcribing...")
        self.set_output_text("Finished recording. Transcribing...")

    def _record_audio(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        
        while self.is_recording:
            data = stream.read(1024)
            self.frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        self.save_and_transcribe()

    def save_and_transcribe(self):
        with wave.open(self.audio_file_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))

        transcribe_thread = threading.Thread(target=self._transcribe)
        transcribe_thread.start()

    def _transcribe(self):
        try:
            with open(self.audio_file_path, "rb") as audio_file:
                result = self.whisper_client.audio.transcriptions.create(
                    model=self.whisper_deployment,
                    file=audio_file
                )
            self.set_output_text(result.text)
            self.export_transcription(result.text)
            self.set_status_text("Transcription complete.")
        except Exception as e:
            self.show_error(f"An error occurred: {e}")
        finally:
            if os.path.exists(self.audio_file_path):
                os.remove(self.audio_file_path)

    def set_output_text(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)

    def show_error(self, message):
        self.set_output_text(f"Error: {message}")
        self.set_status_text("Error occurred.")

    def export_transcription(self, text):
        with open("out.txt", "w") as f:
            f.write(text)
        print("\nTranscription saved to out.txt")

    def copy_to_clipboard(self):
        self.root.clipboard_clear()
        text = self.output_text.get("1.0", tk.END)
        self.root.clipboard_append(text.strip())
        self.set_status_text("Copied to clipboard!")
        self.root.after(2000, lambda: self.set_status_text("Ready"))

    def on_closing(self):
        if self.is_recording:
            self.stop_recording()
        self.root.destroy()

    def set_status_text(self, text):
        self.status_bar.config(text=text)

    def browse_vtt_file(self):
        file_path = filedialog.askopenfilename(
            title="Select VTT Transcript File",
            filetypes=[("VTT files", "*.vtt"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            self.generate_notes_button.config(state=tk.NORMAL)
            self.question_entry.config(state=tk.NORMAL)
            self.ask_question_button.config(state=tk.NORMAL)
            # Clear previous transcript when new file is selected
            self.current_transcript = None

    def parse_vtt_file(self, file_path):
        """Parse VTT file and extract the transcript text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove VTT header and timestamps, keep only the text
            lines = content.split('\n')
            transcript_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip VTT header, empty lines, and timestamp lines
                if (line and 
                    not line.startswith('WEBVTT') and 
                    not re.match(r'^\d+$', line) and  # Skip cue numbers
                    not re.match(r'^[\d:.,\s-]+-->', line)):  # Skip timestamp lines
                    transcript_lines.append(line)
            
            return ' '.join(transcript_lines)
        except Exception as e:
            raise Exception(f"Error reading VTT file: {str(e)}")

    def generate_meeting_notes(self):
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a VTT file first.")
            return

        self.generate_notes_button.config(state=tk.DISABLED)
        self.set_status_text("Generating meeting notes...")
        self.set_notes_output("Generating meeting notes...")

        # Run in separate thread to avoid blocking UI
        notes_thread = threading.Thread(target=self._generate_meeting_notes, args=(file_path,))
        notes_thread.start()

    def _generate_meeting_notes(self, file_path):
        try:
            # Parse VTT file and store transcript
            if self.current_transcript is None:
                self.current_transcript = self.parse_vtt_file(file_path)
            
            transcript = self.current_transcript
            
            if not transcript.strip():
                raise Exception("No transcript text found in the VTT file.")

            # Create meeting notes prompt
            prompt = f"""Please analyze the following meeting transcript and create comprehensive meeting notes. 

The notes should include:
1. **Meeting Summary** - Brief overview of the main topics discussed
2. **Key Discussion Points** - Main topics and decisions made
3. **Action Items** - Specific tasks, assignments, and deadlines mentioned
4. **Important Decisions** - Key decisions made during the meeting
5. **Follow-up Items** - Things to be addressed in future meetings

Please format the output in a clear, professional manner suitable for sharing with meeting participants.

Transcript:
{transcript}"""

            # Generate meeting notes using Azure OpenAI
            response = self.gpt_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "You are a professional meeting notes assistant. Create clear, organized, and actionable meeting notes from transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more focused output
                max_tokens=2000
            )

            meeting_notes = response.choices[0].message.content
            self.set_notes_output(meeting_notes)
            self.set_status_text("Meeting notes generated successfully.")
            
        except Exception as e:
            self.show_notes_error(f"An error occurred: {e}")
        finally:
            # Re-enable the button
            self.root.after(0, lambda: self.generate_notes_button.config(state=tk.NORMAL))

    def set_notes_output(self, text):
        self.notes_output.config(state=tk.NORMAL)
        self.notes_output.delete(1.0, tk.END)
        self.notes_output.insert(tk.END, text)
        self.notes_output.config(state=tk.DISABLED)

    def show_notes_error(self, message):
        self.set_notes_output(f"Error: {message}")
        self.set_status_text("Error occurred while generating notes.")

    def copy_notes_to_clipboard(self):
        self.root.clipboard_clear()
        text = self.notes_output.get("1.0", tk.END)
        self.root.clipboard_append(text.strip())
        self.set_status_text("Meeting notes copied to clipboard!")
        self.root.after(2000, lambda: self.set_status_text("Ready"))

    def ask_question_enter(self, event):
        """Handle Enter key press in question entry"""
        self.ask_question()

    def ask_question(self):
        file_path = self.file_path_var.get()
        question = self.question_var.get().strip()
        
        if not file_path:
            messagebox.showerror("Error", "Please select a VTT file first.")
            return
            
        if not question:
            messagebox.showerror("Error", "Please enter a question.")
            return

        self.ask_question_button.config(state=tk.DISABLED)
        self.question_entry.config(state=tk.DISABLED)
        self.set_status_text("Processing your question...")
        self.set_notes_output("Processing your question...")

        # Run in separate thread to avoid blocking UI
        question_thread = threading.Thread(target=self._process_question, args=(file_path, question))
        question_thread.start()

    def _process_question(self, file_path, question):
        try:
            # Use stored transcript or parse VTT file if not already parsed
            if self.current_transcript is None:
                self.current_transcript = self.parse_vtt_file(file_path)
            
            transcript = self.current_transcript
            
            if not transcript.strip():
                raise Exception("No transcript text found in the VTT file.")

            # Create question prompt
            prompt = f"""You are an AI assistant helping to analyze a meeting transcript. Please answer the following question based on the transcript content provided.

Question: {question}

Transcript:
{transcript}

Please provide a clear, accurate answer based on the information available in the transcript. If the transcript doesn't contain enough information to answer the question, please indicate that clearly."""

            # Generate response using Azure OpenAI
            response = self.gpt_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that analyzes meeting transcripts and answers questions about their content. Provide accurate, clear, and concise responses based on the information available."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Lower temperature for more factual responses
                max_tokens=1500
            )

            answer = response.choices[0].message.content
            
            # Format the response with the question
            formatted_response = f"Question: {question}\n\n{answer}"
            
            self.set_notes_output(formatted_response)
            self.set_status_text("Question answered successfully.")
            
        except Exception as e:
            self.show_notes_error(f"An error occurred: {e}")
        finally:
            # Re-enable the controls
            self.root.after(0, lambda: self.ask_question_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.question_entry.config(state=tk.NORMAL))

def main():
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

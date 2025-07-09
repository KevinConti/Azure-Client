import os
import pyaudio
import wave
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, font
from openai import AzureOpenAI
from dotenv import load_dotenv

class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Whisper Client")
        self.root.geometry("600x450")

        self.is_recording = False
        self.frames = []
        self.audio_file_path = "temp_recording.wav"

        # --- Style Configuration ---
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        # Define fonts
        self.default_font = font.nametofont("TkDefaultFont")
        self.default_font.configure(family="Segoe UI", size=10)
        
        # Define colors
        BG_COLOR = "#282c34"
        TEXT_COLOR = "#abb2bf"
        BUTTON_BG = "#61afef"
        BUTTON_FG = "white"
        BUTTON_HOVER = "#528bce"
        TEXT_AREA_BG = "#21252b"

        # Configure root window
        self.root.configure(bg=BG_COLOR)

        # Configure ttk styles
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TButton", 
                             background=BUTTON_BG, 
                             foreground=BUTTON_FG, 
                             font=self.default_font, 
                             padding=10,
                             borderwidth=0,
                             relief="flat")
        self.style.map("TButton",
            background=[("active", BUTTON_HOVER)],
            relief=[("pressed", "sunken")])
        
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=self.default_font)

        # Load environment variables and initialize OpenAI client
        load_dotenv()
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        if not all([api_key, azure_endpoint, self.deployment_name]):
            self.show_error("Please set Azure credentials in .env file.")
            return

        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version="2024-02-01"
        )

        # --- UI Elements ---
        main_frame = ttk.Frame(root, padding="20 10 20 10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.start_button = ttk.Button(button_frame, text="Start Recording", command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop Recording", command=self.stop_recording, style="TButton", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        self.copy_button = ttk.Button(main_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(pady=5)

        self.output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state=tk.DISABLED, bg=TEXT_AREA_BG, fg=TEXT_COLOR, font=self.default_font, relief="flat", borderwidth=2)
        self.output_text.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        
        self.status_bar = ttk.Label(root, text="Ready", padding="10 5 10 5")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.set_status_text("Recording...")
        self.set_output_text("")

        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.set_status_text("Finished recording. Transcribing...")

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
                result = self.client.audio.transcriptions.create(
                    model=self.deployment_name,
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

def main():
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

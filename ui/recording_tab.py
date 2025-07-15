"""
Recording tab UI component for audio recording functionality.
"""
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Optional

from controllers import AppController
from models import AppState, RecordingSession, Transcript
from ui.theme import get_theme


class RecordingTab:
    """UI component for the voice recording tab."""
    
    def __init__(self, parent, controller: AppController):
        self.parent = parent
        self.controller = controller
        self.theme = get_theme()
        
        # Create main frame
        self.frame = ttk.Frame(parent, padding=f"{self.theme.spacing['large']} {self.theme.spacing['medium']}")
        
        # UI components
        self.start_button: Optional[ttk.Button] = None
        self.stop_button: Optional[ttk.Button] = None
        self.copy_button: Optional[ttk.Button] = None
        self.output_text: Optional[scrolledtext.ScrolledText] = None
        
        # Setup the UI
        self._setup_ui()
        self._update_button_states()
    
    def _setup_ui(self):
        """Setup the recording tab UI components."""
        # Button frame
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=self.theme.spacing['medium'])
        
        # Recording buttons
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Recording", 
            command=self._on_start_recording
        )
        self.start_button.pack(side=tk.LEFT, padx=self.theme.spacing['small'])
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Stop Recording", 
            command=self._on_stop_recording,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=self.theme.spacing['small'])
        
        # Copy button
        self.copy_button = ttk.Button(
            self.frame,
            text="Copy to Clipboard", 
            command=self._on_copy_to_clipboard
        )
        self.copy_button.pack(pady=self.theme.spacing['small'])
        
        # Output text area
        text_config = self.theme.get_text_widget_config()
        self.output_text = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            **text_config
        )
        self.output_text.pack(
            pady=self.theme.spacing['medium'],
            padx=self.theme.spacing['medium'],
            expand=True,
            fill=tk.BOTH
        )
    
    def _on_start_recording(self):
        """Handle start recording button click."""
        success = self.controller.start_recording()
        if success:
            self._update_button_states_recording()
            self._set_output_text("Recording...")
    
    def _on_stop_recording(self):
        """Handle stop recording button click."""
        success = self.controller.stop_recording()
        if success:
            self._update_button_states_stopped()
    
    def _on_copy_to_clipboard(self):
        """Handle copy to clipboard button click."""
        if self.output_text:
            # Get text content
            text = self.output_text.get("1.0", tk.END).strip()
            
            if text:
                # Copy to clipboard
                self.frame.clipboard_clear()
                self.frame.clipboard_append(text)
                
                # Show temporary status
                self._show_temporary_status("Copied to clipboard!")
    
    def _set_output_text(self, text: str):
        """Set the output text area content."""
        if self.output_text:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, text)
            self.output_text.config(state=tk.DISABLED)
    
    def _append_output_text(self, text: str):
        """Append text to the output text area."""
        if self.output_text:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, text)
            self.output_text.config(state=tk.DISABLED)
            # Auto-scroll to bottom
            self.output_text.see(tk.END)
    
    def _update_button_states(self):
        """Update button states based on current application state."""
        app_state = self.controller.get_app_state()
        
        if app_state.can_record():
            self._update_button_states_idle()
        elif app_state.current_recording and app_state.current_recording.is_active():
            self._update_button_states_recording()
        else:
            self._update_button_states_processing()
    
    def _update_button_states_idle(self):
        """Update button states for idle state."""
        if self.start_button:
            self.start_button.config(state=tk.NORMAL)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
    
    def _update_button_states_recording(self):
        """Update button states for recording state."""
        if self.start_button:
            self.start_button.config(state=tk.DISABLED)
        if self.stop_button:
            self.stop_button.config(state=tk.NORMAL)
    
    def _update_button_states_stopped(self):
        """Update button states for stopped/processing state."""
        if self.start_button:
            self.start_button.config(state=tk.DISABLED)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
    
    def _update_button_states_processing(self):
        """Update button states for processing state."""
        if self.start_button:
            self.start_button.config(state=tk.DISABLED)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
    
    def _show_temporary_status(self, message: str, duration: int = 2000):
        """Show a temporary status message."""
        # This could be enhanced to show a temporary overlay or tooltip
        # For now, we'll rely on the main status bar
        pass
    
    # Event handlers for controller callbacks
    
    def on_recording_started(self, session: RecordingSession):
        """Handle recording started event."""
        self._update_button_states_recording()
        self._set_output_text("Recording...")
    
    def on_recording_stopped(self, session: RecordingSession):
        """Handle recording stopped event."""
        self._update_button_states_stopped()
        self._set_output_text("Finished recording. Transcribing...")
    
    def on_transcription_started(self, file_path: str):
        """Handle transcription started event."""
        self._set_output_text("Transcribing audio...")
    
    def on_transcription_complete(self, transcript: Transcript):
        """Handle transcription complete event."""
        self._update_button_states_idle()
        self._set_output_text(transcript.to_plain_text())
    
    def on_error(self, error_message: str):
        """Handle error event."""
        self._update_button_states_idle()
        error_config = self.theme.get_error_config()
        
        # Show error in output text with error styling
        if self.output_text:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, f"Error: {error_message}")
            
            # Apply error styling to the text
            self.output_text.tag_add("error", "1.0", tk.END)
            self.output_text.tag_config("error", foreground=error_config['fg'])
            
            self.output_text.config(state=tk.DISABLED)
    
    def update_state(self, app_state: AppState):
        """Update the tab based on application state."""
        self._update_button_states()
        
        # Update output text if we have a transcript
        if app_state.current_transcript:
            self._set_output_text(app_state.current_transcript.to_plain_text())
        elif app_state.error_message:
            self.on_error(app_state.error_message)
    
    def clear_output(self):
        """Clear the output text area."""
        self._set_output_text("")
    
    def set_recording_info(self, info: str):
        """Set recording information text."""
        self._set_output_text(info)
    
    def enable_controls(self):
        """Enable all controls."""
        self._update_button_states_idle()
    
    def disable_controls(self):
        """Disable all controls."""
        if self.start_button:
            self.start_button.config(state=tk.DISABLED)
        if self.stop_button:
            self.stop_button.config(state=tk.DISABLED)
        if self.copy_button:
            self.copy_button.config(state=tk.DISABLED)

"""
Main window UI component for the Whisper Client application.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from controllers import AppController
from ui.theme import apply_theme_to_root, get_theme
from ui.recording_tab import RecordingTab
from ui.notes_tab import NotesTab


class MainWindow:
    """Main application window that contains all UI components."""
    
    def __init__(self, root: tk.Tk, controller: AppController):
        self.root = root
        self.controller = controller
        self.theme = get_theme()
        
        # UI components
        self.notebook: Optional[ttk.Notebook] = None
        self.recording_tab: Optional[RecordingTab] = None
        self.notes_tab: Optional[NotesTab] = None
        self.status_bar: Optional[ttk.Label] = None
        
        # Initialize the UI
        self._setup_window()
        self._setup_components()
        self._setup_controller_callbacks()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_window(self):
        """Setup the main window properties."""
        self.root.title("Whisper Client")
        self.root.geometry(f"{self.theme.sizes['window_width']}x{self.theme.sizes['window_height']}")
        
        # Apply theme
        self.style = apply_theme_to_root(self.root)
        
        # Center the window
        self._center_window()
    
    def _center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _setup_components(self):
        """Setup all UI components."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill=tk.BOTH, 
                          padx=self.theme.spacing['medium'], 
                          pady=self.theme.spacing['medium'])
        
        # Create tabs
        self.recording_tab = RecordingTab(self.notebook, self.controller)
        self.notes_tab = NotesTab(self.notebook, self.controller)
        
        # Add tabs to notebook
        self.notebook.add(self.recording_tab.frame, text="Voice Recording")
        self.notebook.add(self.notes_tab.frame, text="Meeting Notes")
        
        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", 
                                   padding=f"{self.theme.spacing['medium']} {self.theme.spacing['small']}")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_controller_callbacks(self):
        """Setup callbacks for controller events."""
        self.controller.set_ui_callbacks(
            on_recording_started=self._on_recording_started,
            on_recording_stopped=self._on_recording_stopped,
            on_transcription_started=self._on_transcription_started,
            on_transcription_complete=self._on_transcription_complete,
            on_notes_started=self._on_notes_started,
            on_notes_complete=self._on_notes_complete,
            on_question_started=self._on_question_started,
            on_question_complete=self._on_question_complete,
            on_file_selected=self._on_file_selected,
            on_error=self._on_error,
            on_status_change=self._on_status_change
        )
    
    def _on_recording_started(self, session):
        """Handle recording started event."""
        self.set_status("Recording...")
        if self.recording_tab:
            self.recording_tab.on_recording_started(session)
    
    def _on_recording_stopped(self, session):
        """Handle recording stopped event."""
        self.set_status("Finished recording. Transcribing...")
        if self.recording_tab:
            self.recording_tab.on_recording_stopped(session)
    
    def _on_transcription_started(self, file_path):
        """Handle transcription started event."""
        self.set_status("Transcribing audio...")
        if self.recording_tab:
            self.recording_tab.on_transcription_started(file_path)
    
    def _on_transcription_complete(self, transcript):
        """Handle transcription complete event."""
        self.set_status("Transcription complete.")
        if self.recording_tab:
            self.recording_tab.on_transcription_complete(transcript)
    
    def _on_notes_started(self):
        """Handle notes generation started event."""
        self.set_status("Generating meeting notes...")
        if self.notes_tab:
            self.notes_tab.on_notes_started()
    
    def _on_notes_complete(self, notes):
        """Handle notes generation complete event."""
        self.set_status("Meeting notes generated successfully.")
        if self.notes_tab:
            self.notes_tab.on_notes_complete(notes)
    
    def _on_question_started(self, question):
        """Handle question processing started event."""
        self.set_status("Processing your question...")
        if self.notes_tab:
            self.notes_tab.on_question_started(question)
    
    def _on_question_complete(self, question, answer):
        """Handle question processing complete event."""
        self.set_status("Question answered successfully.")
        if self.notes_tab:
            self.notes_tab.on_question_complete(question, answer)
    
    def _on_file_selected(self, file_path):
        """Handle file selection event."""
        self.set_status("VTT file loaded successfully.")
        if self.notes_tab:
            self.notes_tab.on_file_selected(file_path)
    
    def _on_error(self, error_message):
        """Handle error events."""
        self.set_status("Error occurred.")
        self.show_error(error_message)
    
    def _on_status_change(self, status):
        """Handle status change events."""
        self.set_status(status)
    
    def set_status(self, message: str):
        """Update the status bar message."""
        if self.status_bar:
            self.status_bar.config(text=message)
    
    def show_error(self, message: str):
        """Show an error message to the user."""
        messagebox.showerror("Error", message)
    
    def show_info(self, title: str, message: str):
        """Show an info message to the user."""
        messagebox.showinfo(title, message)
    
    def show_warning(self, message: str):
        """Show a warning message to the user."""
        messagebox.showwarning("Warning", message)
    
    def ask_yes_no(self, title: str, message: str) -> bool:
        """Ask the user a yes/no question."""
        return messagebox.askyesno(title, message)
    
    def switch_to_recording_tab(self):
        """Switch to the recording tab."""
        if self.notebook:
            self.notebook.select(0)
    
    def switch_to_notes_tab(self):
        """Switch to the notes tab."""
        if self.notebook:
            self.notebook.select(1)
    
    def get_current_tab(self) -> str:
        """Get the currently selected tab."""
        if not self.notebook:
            return "unknown"
        
        current = self.notebook.select()
        current_index = self.notebook.index(current)
        
        if current_index == 0:
            return "recording"
        elif current_index == 1:
            return "notes"
        else:
            return "unknown"
    
    def update_ui_state(self):
        """Update UI state based on controller state."""
        app_state = self.controller.get_app_state()
        
        # Update status
        self.set_status(app_state.status_message)
        
        # Update tabs
        if self.recording_tab:
            self.recording_tab.update_state(app_state)
        
        if self.notes_tab:
            self.notes_tab.update_state(app_state)
    
    def _on_closing(self):
        """Handle window closing event."""
        try:
            # Ask user confirmation if recording is active
            app_state = self.controller.get_app_state()
            if (app_state.current_recording and 
                app_state.current_recording.is_active()):
                
                if self.ask_yes_no("Confirm Exit", 
                                  "Recording is in progress. Do you want to stop and exit?"):
                    self.controller.stop_recording()
                else:
                    return  # Don't close
            
            # Cleanup controller resources
            self.controller.cleanup()
            
            # Destroy the window
            self.root.destroy()
            
        except Exception as e:
            # Force close if cleanup fails
            print(f"Error during shutdown: {e}")
            self.root.destroy()
    
    def run(self):
        """Start the main event loop."""
        # Initial UI state update
        self.update_ui_state()
        
        # Start the main loop
        self.root.mainloop()

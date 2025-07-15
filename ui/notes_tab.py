"""
Notes tab UI component for meeting notes and question answering functionality.
"""
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
from typing import Optional

from controllers import AppController
from models import AppState
from ui.theme import get_theme


class NotesTab:
    """UI component for the meeting notes tab."""
    
    def __init__(self, parent, controller: AppController):
        self.parent = parent
        self.controller = controller
        self.theme = get_theme()
        
        # Create main frame
        self.frame = ttk.Frame(parent, padding=f"{self.theme.spacing['large']} {self.theme.spacing['medium']}")
        
        # UI components
        self.file_path_var = tk.StringVar()
        self.question_var = tk.StringVar()
        
        self.file_path_entry: Optional[ttk.Entry] = None
        self.browse_button: Optional[ttk.Button] = None
        self.generate_notes_button: Optional[ttk.Button] = None
        self.question_entry: Optional[ttk.Entry] = None
        self.ask_question_button: Optional[ttk.Button] = None
        self.notes_output: Optional[scrolledtext.ScrolledText] = None
        self.copy_notes_button: Optional[ttk.Button] = None
        
        # Setup the UI
        self._setup_ui()
        self._update_button_states()
    
    def _setup_ui(self):
        """Setup the notes tab UI components."""
        # File upload section
        self._setup_upload_section()
        
        # Question section
        self._setup_question_section()
        
        # Output section
        self._setup_output_section()
    
    def _setup_upload_section(self):
        """Setup the file upload section."""
        upload_frame = ttk.Frame(self.frame)
        upload_frame.pack(pady=self.theme.spacing['medium'], fill=tk.X)
        
        # Upload label
        ttk.Label(upload_frame, text="Upload VTT Transcript File:").pack(
            anchor=tk.W, pady=(0, self.theme.spacing['small'])
        )
        
        # File selection frame
        file_select_frame = ttk.Frame(upload_frame)
        file_select_frame.pack(fill=tk.X, pady=(0, self.theme.spacing['medium']))
        
        # File path entry
        self.file_path_entry = ttk.Entry(
            file_select_frame, 
            textvariable=self.file_path_var, 
            state="readonly"
        )
        self.file_path_entry.pack(
            side=tk.LEFT, 
            fill=tk.X, 
            expand=True, 
            padx=(0, self.theme.spacing['small'])
        )
        
        # Browse button
        self.browse_button = ttk.Button(
            file_select_frame, 
            text="Browse", 
            command=self._on_browse_file
        )
        self.browse_button.pack(side=tk.RIGHT)
        
        # Generate notes button
        self.generate_notes_button = ttk.Button(
            upload_frame,
            text="Generate Meeting Notes", 
            command=self._on_generate_notes,
            state=tk.DISABLED
        )
        self.generate_notes_button.pack(pady=self.theme.spacing['small'])
    
    def _setup_question_section(self):
        """Setup the question asking section."""
        question_frame = ttk.Frame(self.frame)
        question_frame.pack(pady=self.theme.spacing['medium'], fill=tk.X)
        
        # Question label
        ttk.Label(question_frame, text="Ask a question about the transcript:").pack(
            anchor=tk.W, pady=(0, self.theme.spacing['small'])
        )
        
        # Question input frame
        question_input_frame = ttk.Frame(question_frame)
        question_input_frame.pack(fill=tk.X, pady=(0, self.theme.spacing['small']))
        
        # Question entry
        self.question_entry = ttk.Entry(
            question_input_frame, 
            textvariable=self.question_var,
            state=tk.DISABLED
        )
        self.question_entry.pack(
            side=tk.LEFT, 
            fill=tk.X, 
            expand=True, 
            padx=(0, self.theme.spacing['small'])
        )
        self.question_entry.bind('<Return>', self._on_question_enter)
        
        # Ask question button
        self.ask_question_button = ttk.Button(
            question_input_frame,
            text="Ask Question", 
            command=self._on_ask_question,
            state=tk.DISABLED
        )
        self.ask_question_button.pack(side=tk.RIGHT)
    
    def _setup_output_section(self):
        """Setup the output section."""
        # Output text area
        text_config = self.theme.get_text_widget_config()
        self.notes_output = scrolledtext.ScrolledText(
            self.frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            **text_config
        )
        self.notes_output.pack(
            pady=self.theme.spacing['medium'],
            padx=self.theme.spacing['medium'],
            expand=True,
            fill=tk.BOTH
        )
        
        # Copy notes button
        self.copy_notes_button = ttk.Button(
            self.frame,
            text="Copy Response to Clipboard", 
            command=self._on_copy_notes
        )
        self.copy_notes_button.pack(pady=self.theme.spacing['small'])
    
    def _on_browse_file(self):
        """Handle browse file button click."""
        file_path = filedialog.askopenfilename(
            title="Select VTT Transcript File",
            filetypes=[("VTT files", "*.vtt"), ("All files", "*.*")]
        )
        
        if file_path:
            success = self.controller.select_vtt_file(file_path)
            if success:
                self.file_path_var.set(file_path)
                self._update_button_states()
    
    def _on_generate_notes(self):
        """Handle generate notes button click."""
        app_state = self.controller.get_app_state()
        
        if not app_state.can_generate_notes():
            messagebox.showerror("Error", "Cannot generate notes in current state.")
            return
        
        # Disable button and show processing message
        if self.generate_notes_button:
            self.generate_notes_button.config(state=tk.DISABLED)
        
        self._set_notes_output("Generating meeting notes...")
        
        # Start notes generation
        success = self.controller.generate_meeting_notes()
        if not success:
            if self.generate_notes_button:
                self.generate_notes_button.config(state=tk.NORMAL)
    
    def _on_ask_question(self):
        """Handle ask question button click."""
        question = self.question_var.get().strip()
        
        if not question:
            messagebox.showerror("Error", "Please enter a question.")
            return
        
        app_state = self.controller.get_app_state()
        if not app_state.can_ask_question():
            messagebox.showerror("Error", "Cannot ask question in current state.")
            return
        
        # Disable controls and show processing message
        self._disable_question_controls()
        self._set_notes_output("Processing your question...")
        
        # Start question processing
        success = self.controller.ask_question(question)
        if not success:
            self._enable_question_controls()
    
    def _on_question_enter(self, event):
        """Handle Enter key press in question entry."""
        self._on_ask_question()
    
    def _on_copy_notes(self):
        """Handle copy notes to clipboard button click."""
        if self.notes_output:
            # Get text content
            text = self.notes_output.get("1.0", tk.END).strip()
            
            if text:
                # Copy to clipboard
                self.frame.clipboard_clear()
                self.frame.clipboard_append(text)
                
                # Show temporary status
                self._show_temporary_status("Response copied to clipboard!")
    
    def _set_notes_output(self, text: str):
        """Set the notes output text area content."""
        if self.notes_output:
            self.notes_output.config(state=tk.NORMAL)
            self.notes_output.delete(1.0, tk.END)
            self.notes_output.insert(tk.END, text)
            self.notes_output.config(state=tk.DISABLED)
    
    def _append_notes_output(self, text: str):
        """Append text to the notes output text area."""
        if self.notes_output:
            self.notes_output.config(state=tk.NORMAL)
            self.notes_output.insert(tk.END, text)
            self.notes_output.config(state=tk.DISABLED)
            # Auto-scroll to bottom
            self.notes_output.see(tk.END)
    
    def _update_button_states(self):
        """Update button states based on current application state."""
        app_state = self.controller.get_app_state()
        
        # Generate notes button
        if self.generate_notes_button:
            if app_state.can_generate_notes() and not app_state.is_busy():
                self.generate_notes_button.config(state=tk.NORMAL)
            else:
                self.generate_notes_button.config(state=tk.DISABLED)
        
        # Question controls
        if app_state.selected_file_path and not app_state.is_busy():
            self._enable_question_controls()
        else:
            self._disable_question_controls()
    
    def _enable_question_controls(self):
        """Enable question input controls."""
        if self.question_entry:
            self.question_entry.config(state=tk.NORMAL)
        if self.ask_question_button:
            self.ask_question_button.config(state=tk.NORMAL)
    
    def _disable_question_controls(self):
        """Disable question input controls."""
        if self.question_entry:
            self.question_entry.config(state=tk.DISABLED)
        if self.ask_question_button:
            self.ask_question_button.config(state=tk.DISABLED)
    
    def _show_temporary_status(self, message: str, duration: int = 2000):
        """Show a temporary status message."""
        # This could be enhanced to show a temporary overlay or tooltip
        # For now, we'll rely on the main status bar
        pass
    
    # Event handlers for controller callbacks
    
    def on_file_selected(self, file_path: str):
        """Handle file selection event."""
        self.file_path_var.set(file_path)
        self._update_button_states()
    
    def on_notes_started(self):
        """Handle notes generation started event."""
        if self.generate_notes_button:
            self.generate_notes_button.config(state=tk.DISABLED)
        self._set_notes_output("Generating meeting notes...")
    
    def on_notes_complete(self, notes: str):
        """Handle notes generation complete event."""
        if self.generate_notes_button:
            self.generate_notes_button.config(state=tk.NORMAL)
        self._set_notes_output(notes)
    
    def on_question_started(self, question: str):
        """Handle question processing started event."""
        self._disable_question_controls()
        self._set_notes_output("Processing your question...")
    
    def on_question_complete(self, question: str, answer: str):
        """Handle question processing complete event."""
        self._enable_question_controls()
        
        # Format the response with the question
        formatted_response = f"Question: {question}\n\n{answer}"
        self._set_notes_output(formatted_response)
        
        # Clear the question input
        self.question_var.set("")
    
    def on_error(self, error_message: str):
        """Handle error event."""
        # Re-enable controls
        self._update_button_states()
        
        # Show error in output
        error_config = self.theme.get_error_config()
        
        if self.notes_output:
            self.notes_output.config(state=tk.NORMAL)
            self.notes_output.delete(1.0, tk.END)
            self.notes_output.insert(tk.END, f"Error: {error_message}")
            
            # Apply error styling
            self.notes_output.tag_add("error", "1.0", tk.END)
            self.notes_output.tag_config("error", foreground=error_config['fg'])
            
            self.notes_output.config(state=tk.DISABLED)
    
    def update_state(self, app_state: AppState):
        """Update the tab based on application state."""
        self._update_button_states()
        
        # Update file path display
        if app_state.selected_file_path:
            self.file_path_var.set(app_state.selected_file_path)
        
        # Update output if we have a response
        if app_state.last_response:
            if app_state.last_question:
                formatted_response = f"Question: {app_state.last_question}\n\n{app_state.last_response}"
                self._set_notes_output(formatted_response)
            else:
                self._set_notes_output(app_state.last_response)
        elif app_state.error_message:
            self.on_error(app_state.error_message)
    
    def clear_output(self):
        """Clear the output text area."""
        self._set_notes_output("")
    
    def clear_question(self):
        """Clear the question input."""
        self.question_var.set("")
    
    def clear_file_selection(self):
        """Clear the file selection."""
        self.file_path_var.set("")
        self._update_button_states()
    
    def enable_controls(self):
        """Enable all controls."""
        self._update_button_states()
    
    def disable_controls(self):
        """Disable all controls."""
        if self.browse_button:
            self.browse_button.config(state=tk.DISABLED)
        if self.generate_notes_button:
            self.generate_notes_button.config(state=tk.DISABLED)
        self._disable_question_controls()
        if self.copy_notes_button:
            self.copy_notes_button.config(state=tk.DISABLED)

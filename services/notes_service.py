"""
Notes generation service for handling meeting notes and question answering.
"""
import threading
import time
from typing import Callable, Optional
from openai import AzureOpenAI

from models.transcript import Transcript


class NotesService:
    """
    Service for generating meeting notes and answering questions using Azure OpenAI GPT.
    
    This service provides functionality for:
    - Generating structured meeting notes from transcripts
    - Interactive question answering based on transcript content
    - Configurable AI parameters (temperature, token limits)
    - Async processing with callback notifications
    - Retry logic for handling API errors
    
    Attributes:
        client: Azure OpenAI client instance
        deployment_name: GPT deployment name to use for requests
        max_retries: Maximum number of API retry attempts
        retry_delay: Delay between retry attempts in seconds
        notes_temperature: Temperature setting for notes generation (0.0-2.0)
        notes_max_tokens: Maximum tokens for notes generation responses
        question_temperature: Temperature setting for Q&A (0.0-2.0)
        question_max_tokens: Maximum tokens for Q&A responses
    """
    
    def __init__(self, client: AzureOpenAI, deployment_name: str):
        self.client = client
        self.deployment_name = deployment_name
        self._is_processing = False
        
        # Callbacks
        self._on_notes_started: Optional[Callable[[], None]] = None
        self._on_notes_complete: Optional[Callable[[str], None]] = None
        self._on_question_started: Optional[Callable[[str], None]] = None
        self._on_question_complete: Optional[Callable[[str, str], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        
        # Configuration
        self.max_retries = 2
        self.retry_delay = 2.0  # seconds
        self.notes_temperature = 0.3
        self.notes_max_tokens = 2000
        self.question_temperature = 0.2
        self.question_max_tokens = 1500
    
    def set_callbacks(self,
                     on_notes_started: Optional[Callable[[], None]] = None,
                     on_notes_complete: Optional[Callable[[str], None]] = None,
                     on_question_started: Optional[Callable[[str], None]] = None,
                     on_question_complete: Optional[Callable[[str, str], None]] = None,
                     on_error: Optional[Callable[[str], None]] = None) -> None:
        """
        Set callback functions for notes generation events.
        
        Args:
            on_notes_started: Called when notes generation begins
            on_notes_complete: Called with generated notes text when complete
            on_question_started: Called when question processing begins
            on_question_complete: Called with question and answer when complete
            on_error: Called with error message if operation fails
        """
        self._on_notes_started = on_notes_started
        self._on_notes_complete = on_notes_complete
        self._on_question_started = on_question_started
        self._on_question_complete = on_question_complete
        self._on_error = on_error
    
    def generate_notes(self, transcript: Transcript) -> bool:
        """
        Generate meeting notes from a transcript using AI.
        
        Args:
            transcript: The transcript object to generate notes from
            
        Returns:
            bool: True if generation started successfully, False if already processing
            
        Note:
            This method runs asynchronously. Results are delivered via callbacks.
        """
        if self._is_processing:
            if self._on_error:
                self._on_error("Notes generation already in progress")
            return False
        
        if not transcript.validate():
            if self._on_error:
                self._on_error("Invalid transcript provided")
            return False
        
        try:
            # Start notes generation in separate thread
            notes_thread = threading.Thread(
                target=self._generate_notes_with_retry,
                args=(transcript,)
            )
            notes_thread.start()
            
            if self._on_notes_started:
                self._on_notes_started()
            
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to start notes generation: {str(e)}")
            return False
    
    def answer_question(self, question: str, transcript: Transcript) -> bool:
        """Answer a question based on the transcript."""
        if self._is_processing:
            if self._on_error:
                self._on_error("Question processing already in progress")
            return False
        
        if not question.strip():
            if self._on_error:
                self._on_error("Question cannot be empty")
            return False
        
        if not transcript.validate():
            if self._on_error:
                self._on_error("Invalid transcript provided")
            return False
        
        try:
            # Start question processing in separate thread
            question_thread = threading.Thread(
                target=self._answer_question_with_retry,
                args=(question, transcript)
            )
            question_thread.start()
            
            if self._on_question_started:
                self._on_question_started(question)
            
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to start question processing: {str(e)}")
            return False
    
    def _generate_notes_with_retry(self, transcript: Transcript):
        """Internal method to generate notes with retry logic."""
        self._is_processing = True
        
        for attempt in range(self.max_retries):
            try:
                notes = self._generate_meeting_notes(transcript)
                
                if notes:
                    if self._on_notes_complete:
                        self._on_notes_complete(notes)
                    
                    self._is_processing = False
                    return
                    
            except Exception as e:
                error_msg = f"Notes generation attempt {attempt + 1} failed: {str(e)}"
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    if self._on_error:
                        self._on_error(f"Notes generation failed after {self.max_retries} attempts: {str(e)}")
        
        self._is_processing = False
    
    def _answer_question_with_retry(self, question: str, transcript: Transcript):
        """Internal method to answer question with retry logic."""
        self._is_processing = True
        
        for attempt in range(self.max_retries):
            try:
                answer = self._process_question(question, transcript)
                
                if answer:
                    if self._on_question_complete:
                        self._on_question_complete(question, answer)
                    
                    self._is_processing = False
                    return
                    
            except Exception as e:
                error_msg = f"Question processing attempt {attempt + 1} failed: {str(e)}"
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    if self._on_error:
                        self._on_error(f"Question processing failed after {self.max_retries} attempts: {str(e)}")
        
        self._is_processing = False
    
    def _generate_meeting_notes(self, transcript: Transcript) -> str:
        """Internal method to generate meeting notes using GPT."""
        try:
            # Import prompts module
            from prompts import MEETING_NOTES_SYSTEM_MESSAGE, get_meeting_notes_prompt
            
            # Create prompt
            prompt = get_meeting_notes_prompt(transcript.full_text)
            
            # Call GPT API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": MEETING_NOTES_SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.notes_temperature,
                max_tokens=self.notes_max_tokens
            )
            
            if response and response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""
            else:
                raise Exception("Invalid response from GPT API")
                
        except Exception as e:
            raise Exception(f"GPT API call failed: {str(e)}")
    
    def _process_question(self, question: str, transcript: Transcript) -> str:
        """Internal method to process question using GPT."""
        try:
            # Import prompts module
            from prompts import QUESTION_ANSWERING_SYSTEM_MESSAGE, get_question_answering_prompt
            
            # Create prompt
            prompt = get_question_answering_prompt(question, transcript.full_text)
            
            # Call GPT API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": QUESTION_ANSWERING_SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.question_temperature,
                max_tokens=self.question_max_tokens
            )
            
            if response and response.choices and response.choices[0].message:
                return response.choices[0].message.content or ""
            else:
                raise Exception("Invalid response from GPT API")
                
        except Exception as e:
            raise Exception(f"GPT API call failed: {str(e)}")
    
    def is_processing(self) -> bool:
        """Check if notes generation or question processing is in progress."""
        return self._is_processing
    
    def set_configuration(self, 
                         notes_temperature: Optional[float] = None,
                         notes_max_tokens: Optional[int] = None,
                         question_temperature: Optional[float] = None,
                         question_max_tokens: Optional[int] = None,
                         max_retries: Optional[int] = None,
                         retry_delay: Optional[float] = None):
        """Update service configuration parameters."""
        if notes_temperature is not None:
            self.notes_temperature = max(0.0, min(2.0, notes_temperature))
        
        if notes_max_tokens is not None:
            self.notes_max_tokens = max(1, min(4000, notes_max_tokens))
        
        if question_temperature is not None:
            self.question_temperature = max(0.0, min(2.0, question_temperature))
        
        if question_max_tokens is not None:
            self.question_max_tokens = max(1, min(4000, question_max_tokens))
        
        if max_retries is not None:
            self.max_retries = max(1, min(5, max_retries))
        
        if retry_delay is not None:
            self.retry_delay = max(0.5, min(10.0, retry_delay))
    
    def estimate_processing_time(self, transcript: Transcript) -> dict[str, float]:
        """Estimate processing times for different operations."""
        text_length = len(transcript.full_text)
        
        # Rough estimates based on text length
        notes_time = max(10.0, min(text_length / 100, 120.0))  # 10s to 2min
        question_time = max(5.0, min(text_length / 200, 60.0))  # 5s to 1min
        
        return {
            "notes_generation": notes_time,
            "question_answering": question_time
        }
    
    def validate_transcript_length(self, transcript: Transcript) -> tuple[bool, str]:
        """Validate transcript length for processing."""
        text_length = len(transcript.full_text)
        
        # Check minimum length
        if text_length < 10:
            return False, "Transcript too short for meaningful processing"
        
        # Check maximum length (approximate token limit)
        max_chars = 12000  # Rough estimate for token limits
        if text_length > max_chars:
            return False, f"Transcript too long: {text_length} chars (max {max_chars})"
        
        return True, "Transcript length is valid"
    
    def cleanup(self):
        """Clean up resources and cancel ongoing operations."""
        # Note: Azure OpenAI doesn't provide a way to cancel ongoing API calls
        # This is a placeholder for future implementation if needed
        self._is_processing = False

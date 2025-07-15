"""
Event system for handling inter-service communication and UI notifications.
"""
import logging
import queue
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type


class EventType(Enum):
    """Enumeration of event types in the application."""
    # Recording events
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_COMPLETE = "recording_complete"
    RECORDING_ERROR = "recording_error"
    
    # Transcription events
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETE = "transcription_complete"
    TRANSCRIPTION_ERROR = "transcription_error"
    
    # Notes events
    NOTES_GENERATION_STARTED = "notes_generation_started"
    NOTES_GENERATION_COMPLETE = "notes_generation_complete"
    NOTES_ERROR = "notes_error"
    
    # Question events
    QUESTION_STARTED = "question_started"
    QUESTION_COMPLETE = "question_complete"
    QUESTION_ERROR = "question_error"
    
    # File events
    FILE_SELECTED = "file_selected"
    FILE_PROCESSED = "file_processed"
    FILE_EXPORTED = "file_exported"
    FILE_ERROR = "file_error"
    
    # Application events
    APP_STATE_CHANGED = "app_state_changed"
    APP_MODE_CHANGED = "app_mode_changed"
    APP_ERROR = "app_error"
    STATUS_CHANGED = "status_changed"
    
    # UI events
    UI_UPDATE_REQUIRED = "ui_update_required"
    PROGRESS_UPDATE = "progress_update"


@dataclass
class Event:
    """Base event class containing common event data."""
    event_type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    event_id: Optional[str] = None
    
    def __post_init__(self):
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())
    
    @classmethod
    def create(cls, event_type: EventType, source: str, **data) -> 'Event':
        """Create a new event with the given type and data."""
        return cls(
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            data=data
        )
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data value by key with optional default."""
        return self.data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data
        }


class EventListener(ABC):
    """Abstract base class for event listeners."""
    
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """Handle an event. Must be implemented by subclasses."""
        pass
    
    def get_supported_events(self) -> List[EventType]:
        """Return list of event types this listener can handle."""
        return list(EventType)  # Default: handle all events


class CallbackEventListener(EventListener):
    """Event listener that wraps a callback function."""
    
    def __init__(self, callback: Callable[[Event], None], 
                 supported_events: Optional[List[EventType]] = None):
        self.callback = callback
        self._supported_events = supported_events or list(EventType)
    
    def handle_event(self, event: Event) -> None:
        """Handle event by calling the wrapped callback."""
        if event.event_type in self._supported_events:
            self.callback(event)
    
    def get_supported_events(self) -> List[EventType]:
        """Return supported event types."""
        return self._supported_events


class EventDispatcher:
    """Central event dispatcher for managing event distribution."""
    
    def __init__(self, max_queue_size: int = 1000, enable_async: bool = True):
        self.listeners: Dict[EventType, List[EventListener]] = {}
        self.global_listeners: List[EventListener] = []
        self.event_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.enable_async = enable_async
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        
        # Event statistics
        self.events_processed = 0
        self.events_failed = 0
        self.event_history: List[Event] = []
        self.max_history_size = 100
        
        if enable_async:
            self.start()
    
    def start(self):
        """Start the event dispatcher worker thread."""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self.worker_thread.start()
        self.logger.info("Event dispatcher started")
    
    def stop(self):
        """Stop the event dispatcher worker thread."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Signal worker thread to stop
        try:
            self.event_queue.put(None, timeout=1.0)
        except queue.Full:
            pass
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)
        
        self.logger.info("Event dispatcher stopped")
    
    def subscribe(self, listener: EventListener, event_types: Optional[List[EventType]] = None):
        """Subscribe a listener to specific event types or all events."""
        if event_types is None:
            # Global listener - receives all events
            self.global_listeners.append(listener)
        else:
            # Subscribe to specific event types
            for event_type in event_types:
                if event_type not in self.listeners:
                    self.listeners[event_type] = []
                self.listeners[event_type].append(listener)
        
        self.logger.debug(f"Subscribed listener {type(listener).__name__} to events: {event_types}")
    
    def unsubscribe(self, listener: EventListener, event_types: Optional[List[EventType]] = None):
        """Unsubscribe a listener from specific event types or all events."""
        if event_types is None:
            # Remove from global listeners
            if listener in self.global_listeners:
                self.global_listeners.remove(listener)
            
            # Remove from all specific event type listeners
            for event_type_listeners in self.listeners.values():
                if listener in event_type_listeners:
                    event_type_listeners.remove(listener)
        else:
            # Remove from specific event types
            for event_type in event_types:
                if event_type in self.listeners and listener in self.listeners[event_type]:
                    self.listeners[event_type].remove(listener)
        
        self.logger.debug(f"Unsubscribed listener {type(listener).__name__} from events: {event_types}")
    
    def dispatch(self, event: Event) -> bool:
        """Dispatch an event to all registered listeners."""
        try:
            if self.enable_async:
                # Queue event for async processing
                self.event_queue.put(event, timeout=1.0)
                return True
            else:
                # Process event synchronously
                self._dispatch_event(event)
                return True
                
        except queue.Full:
            self.logger.error(f"Event queue full, dropping event: {event.event_type}")
            self.events_failed += 1
            return False
        except Exception as e:
            self.logger.error(f"Failed to dispatch event {event.event_type}: {str(e)}")
            self.events_failed += 1
            return False
    
    def dispatch_simple(self, event_type: EventType, source: str, **data) -> bool:
        """Convenience method to create and dispatch an event."""
        event = Event.create(event_type, source, **data)
        return self.dispatch(event)
    
    def _process_events(self):
        """Worker thread method to process events from the queue."""
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = self.event_queue.get(timeout=1.0)
                
                if event is None:  # Shutdown signal
                    break
                
                self._dispatch_event(event)
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
                self.events_failed += 1
    
    def _dispatch_event(self, event: Event):
        """Internal method to dispatch an event to listeners."""
        try:
            # Add to history
            self._add_to_history(event)
            
            # Dispatch to global listeners
            for listener in self.global_listeners:
                try:
                    listener.handle_event(event)
                except Exception as e:
                    self.logger.error(f"Error in global listener {type(listener).__name__}: {str(e)}")
            
            # Dispatch to specific event type listeners
            if event.event_type in self.listeners:
                for listener in self.listeners[event.event_type]:
                    try:
                        listener.handle_event(event)
                    except Exception as e:
                        self.logger.error(f"Error in listener {type(listener).__name__}: {str(e)}")
            
            self.events_processed += 1
            self.logger.debug(f"Dispatched event: {event.event_type} from {event.source}")
            
        except Exception as e:
            self.logger.error(f"Critical error dispatching event {event.event_type}: {str(e)}")
            self.events_failed += 1
    
    def _add_to_history(self, event: Event):
        """Add event to history for debugging purposes."""
        self.event_history.append(event)
        
        # Keep history size manageable
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event dispatcher statistics."""
        return {
            'events_processed': self.events_processed,
            'events_failed': self.events_failed,
            'queue_size': self.event_queue.qsize(),
            'is_running': self.is_running,
            'listeners_count': {
                'global': len(self.global_listeners),
                'specific': sum(len(listeners) for listeners in self.listeners.values())
            },
            'event_types_registered': list(self.listeners.keys())
        }
    
    def get_recent_events(self, count: int = 10) -> List[Event]:
        """Get the most recent events from history."""
        return self.event_history[-count:] if self.event_history else []
    
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
    
    def wait_for_queue_empty(self, timeout: float = 5.0) -> bool:
        """Wait for the event queue to be empty."""
        if not self.enable_async:
            return True
        
        try:
            # Use join with timeout to wait for queue to be empty
            start_time = datetime.now()
            while (datetime.now() - start_time).total_seconds() < timeout:
                if self.event_queue.empty():
                    return True
                threading.Event().wait(0.1)  # Small delay
            
            return self.event_queue.empty()
            
        except Exception as e:
            self.logger.error(f"Error waiting for queue: {str(e)}")
            return False


# Global event dispatcher instance
_global_dispatcher: Optional[EventDispatcher] = None


def get_event_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance."""
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = EventDispatcher()
    return _global_dispatcher


def shutdown_event_system():
    """Shutdown the global event system."""
    global _global_dispatcher
    if _global_dispatcher:
        _global_dispatcher.stop()
        _global_dispatcher = None


# Convenience functions for common event operations

def dispatch_event(event_type: EventType, source: str, **data) -> bool:
    """Convenience function to dispatch an event."""
    return get_event_dispatcher().dispatch_simple(event_type, source, **data)


def subscribe_to_events(callback: Callable[[Event], None], 
                       event_types: Optional[List[EventType]] = None) -> CallbackEventListener:
    """Convenience function to subscribe a callback to events."""
    listener = CallbackEventListener(callback, event_types)
    get_event_dispatcher().subscribe(listener, event_types)
    return listener


def unsubscribe_from_events(listener: EventListener, 
                          event_types: Optional[List[EventType]] = None):
    """Convenience function to unsubscribe from events."""
    get_event_dispatcher().unsubscribe(listener, event_types)

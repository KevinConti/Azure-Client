# UI package

from .theme import AppTheme, get_theme, apply_theme_to_root
from .main_window import MainWindow
from .recording_tab import RecordingTab
from .notes_tab import NotesTab

__all__ = [
    'AppTheme',
    'get_theme',
    'apply_theme_to_root',
    'MainWindow',
    'RecordingTab',
    'NotesTab'
]

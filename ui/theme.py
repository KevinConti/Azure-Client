"""
UI styling and theming configuration for the Whisper Client application.
"""
import tkinter as tk
from tkinter import ttk, font
from typing import Dict, Any


class AppTheme:
    """Application theme configuration and styling."""
    
    def __init__(self):
        # Define color palette
        self.colors = {
            'bg_primary': '#282c34',
            'bg_secondary': '#21252b', 
            'text_primary': 'white',
            'text_secondary': '#abb2bf',
            'text_disabled': '#84888c',
            'button_bg': '#61afef',
            'button_fg': 'black',
            'button_hover': '#528bce',
            'error': '#e06c75',
            'success': '#98c379',
            'warning': '#e5c07b',
            'info': '#56b6c2'
        }
        
        # Define fonts
        self.fonts = {
            'default': ('Segoe UI', 10),
            'heading': ('Segoe UI', 12, 'bold'),
            'small': ('Segoe UI', 8),
            'monospace': ('Consolas', 10)
        }
        
        # Define spacing and sizing
        self.spacing = {
            'small': 5,
            'medium': 10,
            'large': 20,
            'xlarge': 30
        }
        
        self.sizes = {
            'button_padding': 10,
            'window_width': 600,
            'window_height': 450,
            'text_area_border': 2
        }
    
    def configure_root_window(self, root: tk.Tk):
        """Configure the root window with theme settings."""
        root.configure(bg=self.colors['bg_primary'])
        
        # Configure default font
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family=self.fonts['default'][0], size=self.fonts['default'][1])
    
    def configure_ttk_styles(self, style: ttk.Style):
        """Configure TTK widget styles."""
        style.theme_use("clam")
        
        # Configure frame styles
        style.configure("TFrame", 
                       background=self.colors['bg_primary'])
        
        # Configure button styles
        style.configure("TButton",
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_fg'],
                       font=self.fonts['default'],
                       padding=self.sizes['button_padding'],
                       borderwidth=0,
                       relief="flat")
        
        style.map("TButton",
                 background=[("active", self.colors['button_hover'])],
                 relief=[("pressed", "sunken")],
                 foreground=[("disabled", self.colors['text_disabled'])])
        
        # Configure label styles
        style.configure("TLabel",
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'],
                       font=self.fonts['default'])
        
        # Configure notebook styles
        style.configure("TNotebook",
                       background=self.colors['bg_primary'],
                       borderwidth=0)
        
        style.configure("TNotebook.Tab",
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       padding=[12, 8],
                       font=self.fonts['default'])
        
        style.map("TNotebook.Tab",
                 background=[("selected", self.colors['button_bg'])],
                 foreground=[("selected", self.colors['button_fg'])])
        
        # Configure entry styles
        style.configure("TEntry",
                       fieldbackground=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       insertcolor=self.colors['text_primary'])
    
    def get_text_widget_config(self) -> Dict[str, Any]:
        """Get configuration for text widgets (ScrolledText, etc.)."""
        return {
            'bg': self.colors['bg_secondary'],
            'fg': self.colors['text_primary'],
            'font': self.fonts['default'],
            'relief': "flat",
            'borderwidth': self.sizes['text_area_border'],
            'insertbackground': self.colors['text_primary'],
            'selectbackground': self.colors['button_bg'],
            'selectforeground': self.colors['button_fg']
        }
    
    def get_error_config(self) -> Dict[str, Any]:
        """Get configuration for error display."""
        return {
            'bg': self.colors['bg_secondary'],
            'fg': self.colors['error'],
            'font': self.fonts['default']
        }
    
    def get_success_config(self) -> Dict[str, Any]:
        """Get configuration for success display."""
        return {
            'bg': self.colors['bg_secondary'],
            'fg': self.colors['success'],
            'font': self.fonts['default']
        }


# Global theme instance
_app_theme: AppTheme = AppTheme()


def get_theme() -> AppTheme:
    """Get the global application theme."""
    return _app_theme


def apply_theme_to_root(root: tk.Tk) -> ttk.Style:
    """Apply theme to root window and return configured style."""
    theme = get_theme()
    theme.configure_root_window(root)
    
    style = ttk.Style(root)
    theme.configure_ttk_styles(style)
    
    return style

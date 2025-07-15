import sys
import tkinter as tk
from tkinter import messagebox
from typing import Optional, List

# Import new architecture components
from controllers.app_controller import AppController
from ui.main_window import MainWindow
from services.config_service import ConfigService


class WhisperApplication:
    """
    Main application class using the new refactored architecture.

    This class orchestrates the initialization of the application components:
    - Configuration validation and loading
    - Controller initialization with dependency injection
    - UI setup with proper event handling
    - Application lifecycle management (startup, shutdown, cleanup)

    Attributes:
        root: The main Tkinter window
        controller: Central application controller orchestrating services
        main_window: Primary UI window handling user interactions
        config_service: Service for managing application configuration
    """

    def __init__(self) -> None:
        """Initialize the application with default state."""
        self.root: Optional[tk.Tk] = None
        self.controller: Optional[AppController] = None
        self.main_window: Optional[MainWindow] = None
        self.config_service: Optional[ConfigService] = None

    def initialize(self) -> bool:
        """
        Initialize the application with proper error handling.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize configuration service
            self.config_service = ConfigService()

            # Validate configuration before proceeding
            is_valid, errors = self.config_service.validate_configuration()
            if not is_valid:
                self._show_config_error(errors)
                return False

            # Create root window
            self.root = tk.Tk()
            self.root.title("Whisper Client")
            self.root.geometry("600x450")

            # Initialize controller
            self.controller = AppController()

            # Check if controller initialization was successful
            if self.controller.app_state.error_message:
                error_msg = (
                    f"Controller initialization failed: {self.controller.app_state.error_message}"
                )
                messagebox.showerror("Controller Error", error_msg)
                return False

            # Initialize main window with controller
            self.main_window = MainWindow(root=self.root, controller=self.controller)

            # Set up cleanup on window close
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            return True

        except Exception as e:
            messagebox.showerror(
                "Initialization Error", f"Failed to initialize application: {str(e)}"
            )
            return False

    def _show_config_error(self, errors: List[str]) -> None:
        """
        Show configuration errors to the user.

        Args:
            errors: List of configuration error messages
        """
        error_message = "Configuration errors found:\n\n"
        for error in errors:
            error_message += f"• {error}\n"

        error_message += "\nPlease check your .env file and ensure all required Azure OpenAI credentials are set."

        # Create a minimal root window just to show the error
        temp_root = tk.Tk()
        temp_root.withdraw()  # Hide the window
        messagebox.showerror("Configuration Error", error_message)
        temp_root.destroy()

    def run(self) -> None:
        """
        Run the application main loop.

        Handles initialization, main event loop, error handling, and cleanup.
        """
        if self.initialize():
            try:
                if self.root:
                    self.root.mainloop()
            except KeyboardInterrupt:
                print("Application interrupted by user")
            except Exception as e:
                messagebox.showerror("Runtime Error", f"An error occurred: {str(e)}")
            finally:
                self.cleanup()
        else:
            print("Failed to initialize application. Exiting.")
            sys.exit(1)

    def on_closing(self) -> None:
        """
        Handle application closing with proper cleanup.

        Checks for active operations and prompts user confirmation if needed.
        Ensures all resources are properly cleaned up before exit.
        """
        try:
            # Check for active operations if controller exists
            if self.controller:
                # For now, just ask for confirmation
                if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
                    self.cleanup()
                    if self.root:
                        self.root.destroy()
            else:
                self.cleanup()
                if self.root:
                    self.root.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            if self.root:
                self.root.destroy()

    def cleanup(self) -> None:
        """
        Clean up resources before exit.

        Ensures all services are properly shut down and resources freed.
        """
        try:
            if self.controller:
                self.controller.cleanup()
            # MainWindow cleanup will be handled by the controller
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main() -> None:
    """
    Main entry point for the application.

    Initializes and runs the WhisperApplication with proper error handling.
    """
    try:
        app = WhisperApplication()
        app.run()
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

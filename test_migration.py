#!/usr/bin/env python
"""
Test script to validate the new architecture migration.
"""
import sys
import os

def test_imports():
    """Test that all new architecture components can be imported."""
    try:
        print("Testing imports...")
        
        # Test service imports
        from services.config_service import ConfigService
        from services.audio_service import AudioService
        from services.transcription_service import TranscriptionService
        from services.notes_service import NotesService
        from services.file_service import FileService
        print("✓ Services imported successfully")
        
        # Test model imports
        from models.app_state import AppState, AppConfig
        from models.transcript import Transcript
        from models.recording import RecordingSession
        print("✓ Models imported successfully")
        
        # Test controller import
        from controllers.app_controller import AppController
        print("✓ Controller imported successfully")
        
        # Test UI imports
        from ui.main_window import MainWindow
        print("✓ UI components imported successfully")
        
        print("✓ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_configuration():
    """Test configuration service."""
    try:
        print("\nTesting configuration...")
        
        from services.config_service import ConfigService
        config_service = ConfigService()
        
        # Test configuration validation
        is_valid, errors = config_service.validate_configuration()
        if is_valid:
            print("✓ Configuration is valid")
        else:
            print(f"! Configuration issues found: {errors}")
        
        # Test getting configurations
        azure_config = config_service.get_azure_config()
        app_config = config_service.get_app_config()
        
        if azure_config:
            print("✓ Azure configuration loaded")
        else:
            print("! Azure configuration not available")
            
        if app_config:
            print("✓ App configuration loaded")
        else:
            print("! App configuration not available")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test error: {e}")
        return False

def test_controller_initialization():
    """Test controller initialization."""
    try:
        print("\nTesting controller initialization...")
        
        from controllers.app_controller import AppController
        controller = AppController()
        
        if controller.app_state.error_message:
            print(f"! Controller has error: {controller.app_state.error_message}")
        else:
            print("✓ Controller initialized successfully")
            
        # Test cleanup
        controller.cleanup()
        print("✓ Controller cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Controller test error: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Testing New Architecture Migration ===\n")
    
    tests = [
        test_imports,
        test_configuration,
        test_controller_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} passed ===")
    
    if passed == total:
        print("🎉 All tests passed! Migration architecture is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

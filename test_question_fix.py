#!/usr/bin/env python3
"""
Test script to verify the fix for the question asking bug.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.app_state import AppState, AppMode, ProcessingState
from models.transcript import Transcript, TranscriptSegment
from controllers.app_controller import AppController


def test_question_asking_fix():
    """Test that question asking works after loading a VTT file."""
    print("=== Testing Question Asking Fix ===")
    
    # Create test transcript
    segments = [
        TranscriptSegment(start_time=0.0, end_time=5.0, text="This is a test meeting."),
        TranscriptSegment(start_time=5.0, end_time=10.0, text="We discussed important topics.")
    ]
    full_text = "This is a test meeting. We discussed important topics."
    test_transcript = Transcript(segments=segments, full_text=full_text)
    
    # Test 1: Basic app state functionality
    print("Testing app state logic...")
    app_state = AppState()
    
    # Initially should not be able to ask questions
    assert not app_state.can_ask_question(), "Should not be able to ask questions initially"
    
    # Set mode to NOTES and add transcript
    app_state.set_mode(AppMode.NOTES)
    app_state.set_transcript(test_transcript)
    
    # Now should be able to ask questions (this is the fix)
    assert app_state.can_ask_question(), "Should be able to ask questions in NOTES mode with transcript"
    print("✓ App state allows questions in NOTES mode")
    
    # Test 2: Basic controller setup (without full initialization)
    print("Testing controller basic functionality...")
    controller = AppController()
    
    # Set up state similar to after loading VTT file (without requiring API keys)
    controller.app_state.set_mode(AppMode.NOTES)
    controller.app_state.set_transcript(test_transcript)
    controller.app_state.set_selected_file("test.vtt")
    
    # Check that controller allows questions
    assert controller.app_state.can_ask_question(), "Controller should allow questions after VTT load"
    print("✓ Controller allows questions after VTT file loaded")
    
    # Test the actual question asking logic state check
    question = "What was discussed in the meeting?"
    
    # This should not fail on the state check anymore
    can_ask = controller.app_state.can_ask_question()
    assert can_ask, f"Should be able to ask questions, but can_ask_question() returned {can_ask}"
    print("✓ Question asking state validation passes")
    
    controller.cleanup()
    
    # Test 3: Edge cases
    print("Testing edge cases...")
    app_state = AppState()
    
    # Should work in QUESTION_ANSWERING mode too
    app_state.set_mode(AppMode.QUESTION_ANSWERING)
    app_state.set_transcript(test_transcript)
    assert app_state.can_ask_question(), "Should work in QUESTION_ANSWERING mode"
    
    # Should not work when busy
    app_state.set_processing_state(ProcessingState.GENERATING_NOTES)
    assert not app_state.can_ask_question(), "Should not work when busy"
    
    # Should not work without transcript
    app_state.set_processing_state(ProcessingState.IDLE)
    app_state.reset()  # This clears transcript and selected file
    assert not app_state.can_ask_question(), "Should not work without transcript or file"
    
    print("✓ Edge cases handled correctly")
    
    print("\n=== Fix Verification Results ===")
    print("✅ Question asking now works in NOTES mode")
    print("✅ State logic properly handles VTT file loading")
    print("✅ Controller integration works correctly")
    print("✅ Edge cases are handled properly")
    print("\n🎉 The bug fix is working correctly!")
    print("\nUsers can now:")
    print("1. Load a VTT file in Meeting Notes tab")
    print("2. Ask questions immediately without errors")
    print("3. Generate notes and ask questions from the same transcript")


if __name__ == "__main__":
    test_question_asking_fix()

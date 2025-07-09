import os
import argparse
import pyaudio
import wave
from openai import AzureOpenAI
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Get Azure OpenAI credentials from environment variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

    # Check if credentials are set
    if not all([api_key, azure_endpoint, deployment_name]):
        print("Error: Please make sure to set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME in your .env file.")
        return

    # Initialize the Azure OpenAI client
    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version="2024-02-01" 
    )

    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description="Transcribe an audio file using Azure OpenAI's Whisper model.")
    parser.add_argument("audio_file", nargs='?', default=None, help="Path to the audio file to transcribe. If not provided, will record from microphone.")
    args = parser.parse_args()

    audio_file_path = args.audio_file
    
    if audio_file_path is None:
        print("No audio file provided. Recording from microphone for 5 seconds...")
        audio_file_path = "temp_recording.wav"
        record_audio(audio_file_path)
        print(f"Recording saved to {audio_file_path}")

    # Transcribe the audio file
    try:
        transcription = transcribe_audio(client, deployment_name, audio_file_path)
        print("Transcription:")
        print(transcription)
    except FileNotFoundError:
        print(f"Error: The file '{args.audio_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up temporary recording file
        if audio_file_path == "temp_recording.wav" and os.path.exists(audio_file_path):
            os.remove(audio_file_path)

def record_audio(file_path, duration=5, sample_rate=44100, chunk=1024, channels=1, format=pyaudio.paInt16):
    """
    Records audio from the microphone and saves it to a WAV file.
    """
    audio = pyaudio.PyAudio()

    stream = audio.open(format=format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk)

    print("Recording...")
    frames = []

    for _ in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

def transcribe_audio(client, deployment_name, file_path):
    """
    Transcribes an audio file using the Azure OpenAI Whisper service.

    Args:
        client: The AzureOpenAI client instance.
        deployment_name: The name of the Whisper model deployment.
        file_path: The path to the audio file.

    Returns:
        The transcribed text.
    """
    with open(file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model=deployment_name,
            file=audio_file
        )
    return result.text

if __name__ == "__main__":
    main()

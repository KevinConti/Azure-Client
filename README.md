# Azure OpenAI Whisper Client

This project is a Python command-line tool that uses Azure OpenAI's Whisper model to transcribe audio files.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd whisper-client
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your credentials:**
   - Rename `.env.example` to `.env`.
   - Open the `.env` file and add your Azure OpenAI API key, endpoint, and deployment name.

## Usage

To transcribe an audio file, run the following command:

```bash
python main.py <path-to-your-audio-file>
```

For example:
```bash
python main.py my_audio.wav
```

The script will output the transcription to the console.

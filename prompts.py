"""
Prompts for the Whisper Client application.
Contains all AI prompts used for transcript analysis and meeting notes generation.
"""

# System messages for different AI tasks
MEETING_NOTES_SYSTEM_MESSAGE = "You are a professional meeting notes assistant. Create clear, organized, and actionable meeting notes from transcripts."

QUESTION_ANSWERING_SYSTEM_MESSAGE = "You are a helpful AI assistant that analyzes meeting transcripts and answers questions about their content. Provide accurate, clear, and concise responses based on the information available."

# User prompts for different tasks
def get_meeting_notes_prompt(transcript):
    """Generate a prompt for creating meeting notes from a transcript."""
    return f"""Please analyze the following meeting transcript and create comprehensive meeting notes. 

The notes should include:
1. **Meeting Summary** - Brief overview of the main topics discussed
2. **Key Discussion Points** - Main topics and decisions made
3. **Action Items** - Specific tasks, assignments, and deadlines mentioned
4. **Important Decisions** - Key decisions made during the meeting
5. **Follow-up Items** - Things to be addressed in future meetings

Please format the output in a clear, professional manner suitable for sharing with meeting participants.

Transcript:
{transcript}"""

def get_question_answering_prompt(question, transcript):
    """Generate a prompt for answering a question about a transcript."""
    return f"""You are an AI assistant helping to analyze a meeting transcript. Please answer the following question based on the transcript content provided.

Question: {question}

Transcript:
{transcript}

Please provide a clear, accurate answer based on the information available in the transcript. If the transcript doesn't contain enough information to answer the question, please indicate that clearly."""

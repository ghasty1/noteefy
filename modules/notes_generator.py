import os
from groq import Groq
from .crypto_utils import get_bundled_key

class NotesGenerator:
    def __init__(self, api_key=None):
        self.key = api_key if api_key else os.getenv("GROQ_API_KEY")
        if not self.key:
            self.key = get_bundled_key()
        
        self.client = Groq(api_key=self.key)

    def generate_notes(self, transcript, topic, speaker, date_time):
        """
        Sends the transcript to Groq to generate structured notes.
        Uses Llama 3.3 70B as primary (higher TPM) and Llama 3.1 8B as fallback.
        """
        print("Generating notes with Groq...")

        if not transcript or len(transcript.strip()) < 50:
            return "Error: Transcript is too short or empty. Please check your microphone or backend server."

        system_prompt = (
            "You are an expert personal assistant and note-taker. "
            "Your goal is to convert a raw transcript into clean, structured Markdown notes. "
            "CRITICAL INSTRUCTION: Use ONLY the provided transcript. Do NOT hallucinate or makeup information not present in the text. "
            "If the transcript is too short or nonsense, return 'Insufficient content to generate notes'."
        )

        user_prompt = f"""
        Metadata:
        - Topic: {topic}
        - Speaker/Source: {speaker}
        - Date: {date_time}
        
        Instructions:
        1. Create a header with the Topic, Speaker, and Date.
        2. Write a brief "Summary" section (3-5 sentences).
        3. Identify "Key Concepts" and list them as bullet points.
        4. Organize the main content into "Detailed Notes" with clear headings (H2, H3).
        5. If there are lists or comparisons, format them as bullets or tables.
        6. Determine "Action Items" or "Next Steps" if mentioned.
        7. Use formatting (bold, italics) to highlight important terms.

        TRANSCRIPT:
        {transcript}
        """

        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        
        for model in models:
            try:
                print(f"Attempting note generation with {model}...")
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model,
                    temperature=0.5,
                )
                print(f"Notes generated successfully with {model}.")
                return chat_completion.choices[0].message.content
            except Exception as e:
                error_msg = str(e)
                print(f"Error with {model}: {error_msg}")
                if "rate_limit_exceeded" in error_msg or "413" in error_msg:
                    print(f"{model} rate limited or overloaded, trying next model...")
                    continue
                else:
                    return f"Error generating notes: {error_msg}"
        
        return "Error: All available models reached their rate limits. Please try again later or use a shorter transcript."

if __name__ == "__main__":
    # Test script
    gen = NotesGenerator()
    dummy_transcript = "Welcome to Intro to Python. Today we are learning about lists and loops. Lists are mutable."
    print(gen.generate_notes(dummy_transcript, "CS101", "Dr. Smith", "2023-10-01"))

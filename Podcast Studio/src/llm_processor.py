# Import OS for environment variable access
import os
# Import OpenAI client for API calls
from openai import OpenAI

# Initialize OpenAI client using API key from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_podcast_script(articles, minutes=10, model="gpt-5-nano"):
    """
    Generate a podcast script using OpenAI LLM based on provided articles.

    Parameters:
    - articles: list of dictionaries, each with "url" and "text" keys
    - minutes: target length of the podcast episode (approximate)
    - model: the OpenAI model to use for script generation

    Returns:
    - script text as a string, ready for narration

    Functionality:
    1. Concatenates all article texts into a single prompt for context.
    2. Constructs a user prompt describing the task and desired episode length.
    3. Calls the OpenAI chat completion endpoint with a system role and user prompt.
    4. Returns the generated script text from the model's response.
    """
    sources_text = ""  # Initialize text container for all sources

    # Enumerate over articles and append each article's URL and text
    for i, a in enumerate(articles, start=1):
        sources_text += f"\nSOURCE {i} ({a['url']}):\n{a['text']}\n"

    # Build the prompt for the model
    prompt = f"""
You are a podcast scriptwriter and narrator.
Task: Using the sources below, write an original podcast script suitable for a {minutes}-minute episode.
Write clear, engaging narration for a general audience.
Do not copy sentences; rephrase ideas in your own words.

Sources:
{sources_text}
"""

    # Call the OpenAI API to generate a chat completion
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You write engaging podcast scripts."},
            {"role": "user", "content": prompt},
        ],
    )

    # Return the generated script text, stripped of leading/trailing whitespace
    return response.choices[0].message.content.strip()


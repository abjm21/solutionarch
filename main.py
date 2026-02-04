# main.py

import json
import google.generativeai as genai
import config  # Your file with GEMINI_API_KEY

# --- Change 1: Configure the Gemini client ---
# Configure the library with your API key from the config file
try:
    genai.configure(api_key=config.GEMINI_API_KEY)
except AttributeError:
    print("ERROR: Could not find GEMINI_API_KEY in config.py. Please create it and add your key.")
    exit()

# Load the predefined questions from the JSON file
with open('questions.json', 'r') as f:
    questions = json.load(f)

# Dictionary to store the extracted answers
collected_answers = {}

# --- Change 2: Select the Gemini Model ---
# This initializes the model we'll be using for our calls.
# "gemini-1.5-pro-latest" is a great choice for this kind of task.
model = genai.GenerativeModel('gemini-1.5-pro-latest')


def interpret_with_gemini(user_input, original_question):
    """
    Uses the Gemini API to interpret the user's free-form answer.
    """
    prompt = f"""
    The user was asked the following question: '{original_question}'
    The user responded with: '{user_input}'

    Your task is to extract the key information from the user's response.
    Present it as a concise summary. Return ONLY the summary, nothing else.
    """

    # --- Change 3: The API call is now much simpler ---
    # The `generate_content` method sends the prompt to the API.
    response = model.generate_content(prompt)

    # The response object contains the generated text.
    # We add a .strip() to remove any leading/trailing whitespace.
    return response.text.strip()


def generate_document():
    """
    Generates the final document using the collected answers.
    """
    print("\n🤖 AI: Compiling the Solution Architecture Design document...")
    with open('document_template.txt', 'r') as f:
        template = f.read()

    # Create the final prompt by filling the template with our collected answers
    final_prompt_content = template.format(**collected_answers)

    final_prompt = f"""
    You are a professional technical writer and solutions architect.
    Using the structured information below, please generate a polished, detailed, and professional Solution Architecture Design document in Markdown format.
    Expand on the provided points. Make sure the document is well-structured and coherent.

    ---
    {final_prompt_content}
    ---
    """

    # --- Change 4: Use the same model for the final generation ---
    response = model.generate_content(final_prompt)
    final_document = response.text

    # Save the final document to a file
    with open('Solution_Architecture_Design.md', 'w') as f:
        f.write(final_document)

    print("✅ Successfully generated 'Solution_Architecture_Design.md'")


def run_conversation():
    """
    The main loop that drives the conversation.
    """
    print("🤖 AI: Hello! I'm here to help you design your solution architecture. Let's start.")

    for item in questions:
        question_text = item['question']
        question_key = item['key']

        # Ask the question and get the user's raw input
        user_response = input(f"\n🤖 AI: {question_text}\n👤 You: ")

        # Use Gemini to interpret the answer into a structured format
        interpreted_answer = interpret_with_gemini(user_response, question_text)
        print(f"🤖 AI (DEBUG): Understood the following: '{interpreted_answer}'")

        # Store the structured answer
        collected_answers[question_key] = interpreted_answer

    print("\n🤖 AI: Excellent, that's all the information I need.")


# --- Main execution block ---
if __name__ == "__main__":
    run_conversation()
    generate_document()

# app.py

import json
import streamlit as st
import google.generativeai as genai
# import config  <- REMOVE THIS LINE

# --- ## MODIFIED ## Use st.secrets instead of config ---
try:
    # This line tells the app to get the key from Streamlit's secret manager
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, AttributeError):
    st.error("ERROR: Gemini API Key not found. Please add it to your secrets.")
    st.stop()

@st.cache_data
def load_questions():
    with open('questions.json', 'r') as f:
        return json.load(f)

questions = load_questions()
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. SESSION STATE INITIALIZATION ---

if 'question_idx' not in st.session_state:
    st.session_state.question_idx = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'conversation_finished' not in st.session_state:
    st.session_state.conversation_finished = False

# --- 3. HELPER FUNCTIONS (API CALLS) ---

def interpret_with_gemini(user_input, original_question):
    prompt = f"""
    The user was asked: '{original_question}'
    The user responded: '{user_input}'
    Extract the key information from the user's response as a concise summary.
    Return ONLY the summary.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

# MODIFIED: The caching key is now the dictionary itself.
# This means if the dictionary changes (an answer is edited), the cache
# will be invalidated and the function can be re-run with new data.
@st.cache_data
def generate_document_from_answers(_answers_dict):
    with open('document_template.txt', 'r') as f:
        template = f.read()

    final_prompt_content = template.format(**_answers_dict)
    final_prompt = f"""
    You are a professional technical writer. Based on the following structured information,
    generate a polished and detailed Solution Architecture Design document in Markdown format.
    Expand on the points and ensure it is professionally written.
    ---
    {final_prompt_content}
    ---
    """
    response = model.generate_content(final_prompt)
    return response.text

# --- ## NEW/MODIFIED ## 4. SIDEBAR FOR EDITING ANSWERS ---

def display_sidebar_editor():
    """Renders the sidebar UI for viewing and editing answers."""
    st.sidebar.title("📝 Answers Editor")
    st.sidebar.write("Review and edit your previous answers here.")
    st.sidebar.markdown("---")

    # Loop through all questions to display them in order
    for idx, question_item in enumerate(questions):
        question_key = question_item['key']

        # Only display the editor for questions that have been answered
        if question_key in st.session_state.answers:
            st.sidebar.markdown(f"**Question {idx + 1}:** {question_item['question']}")
            
            # Display the current answer
            current_answer = st.session_state.answers[question_key]
            st.sidebar.markdown(f"> _{current_answer}_")

            # The expander provides a clean way to hide the edit form
            with st.sidebar.expander(f"Edit Answer {idx + 1}"):
                # Use a form to group the text area and save button
                with st.form(key=f"edit_form_{question_key}"):
                    new_answer = st.text_area(
                        "Your new answer:",
                        value=current_answer, # Pre-fill with the existing answer
                        key=f"edit_text_{question_key}"
                    )
                    
                    if st.form_submit_button("Save Changes"):
                        # When "Save" is clicked, update the session state
                        st.session_state.answers[question_key] = new_answer
                        st.success("Answer updated!")
                        # We don't need to rerun, Streamlit's loop will handle the refresh
                        # on the next interaction or automatically after a button press.

# --- 5. THE MAIN WEB INTERFACE LOGIC ---

st.title("Solution Architecture AI Assistant 🤖")
st.write("I will ask you a series of questions to generate a design document for your application.")

# ## NEW/MODIFIED ## Call the sidebar function to render it
display_sidebar_editor()

current_idx = st.session_state.question_idx

if not st.session_state.conversation_finished:
    # Progress Bar (from previous step)
    st.markdown("---")
    progress_value = current_idx / len(questions)
    st.write(f"Progress: {current_idx} of {len(questions)} questions answered.")
    st.progress(progress_value)
    st.markdown("---")
    
    # Question display logic remains the same
    current_question_item = questions[current_idx]
    question_text = current_question_item['question']
    question_key = current_question_item['key']
    st.markdown(f"### Question {current_idx + 1}")
    st.info(question_text)
    
    with st.form(key=f"question_form_{current_idx}"):
        user_response = st.text_area("Your answer:", key=f"response_{current_idx}")
        submitted = st.form_submit_button("Submit Answer")

        if submitted and user_response:
            with st.spinner("Analyzing your response..."):
                interpreted = interpret_with_gemini(user_response, question_text)
                st.session_state.answers[question_key] = interpreted
                st.session_state.question_idx += 1
                if st.session_state.question_idx >= len(questions):
                    st.session_state.conversation_finished = True
            st.rerun() # Rerun to show the next question and update the sidebar
        elif submitted:
            st.warning("Please provide an answer.")

# --- 6. DOCUMENT GENERATION STAGE ---
else:
    st.success("Great! We have all the information needed.")
    st.balloons()

    st.info("You can review and edit your answers in the sidebar before generating the final document.")

    if st.button("✨ Generate Architecture Document"):
        with st.spinner("Brewing your document..."):
            # The function now uses the potentially edited answers
            final_doc = generate_document_from_answers(st.session_state.answers)
            
            st.markdown("---")
            st.markdown("### Your Generated Solution Architecture Design")
            st.markdown(final_doc)

            st.download_button(
                "Download Document", final_doc, "Solution_Architecture_Design.md", "text/markdown"
            )

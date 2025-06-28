import streamlit as st
import google.generativeai as genai
import random
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Try to get API key from Streamlit secrets first, then from environment
try:
    GEMINI_API_KEY = st.secrets["google_key"]
except:
    GEMINI_API_KEY = os.getenv("google_key")

# If no API key found, ask user to input it
if not GEMINI_API_KEY:
    st.sidebar.header("🔑 API Configuration")
    GEMINI_API_KEY = st.sidebar.text_input(
        "Enter your Google API Key:", 
        type="password",
        help="Get your API key from Google AI Studio"
    )
    
    if not GEMINI_API_KEY:
        st.error("🔑 Please enter your Google API key in the sidebar to continue")
        st.info("💡 Get your free API key from: https://makersuite.google.com/app/apikey")
        st.stop()

genai.configure(api_key=GEMINI_API_KEY)
# Set Streamlit page config
st.set_page_config(page_title="Quiz Craft", layout="centered")
st.markdown("<h1 style='text-align: center ;font-size: 60px; color: #96EAF0;'>QuizCraft</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Your AI-Powered Quiz Mentor – Personalized, Adaptive, Intelligent</h4>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; margin:20px'>🧠 Time To Test Your Knowledge </h2>", unsafe_allow_html=True)


# Session states for quiz
if "questions" not in st.session_state:
    st.session_state.questions = []
if "user_answers" not in st.session_state:
    st.session_state.user_answers = [None] * 10
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "hints" not in st.session_state:
    st.session_state.hints = [None] * 10


# Function to generate quiz
def generate_quiz(topic,difficulty):
    prompt = f"""Generate a 10-question multiple choice quiz on the topic: {topic}.
    Make the questions suitable for a {difficulty.lower()} level learner
Each question should have:
1. A clear question.
2. Four options (a, b, c, d).
3. The correct answer indicated in format: "Answer: b" (single line after each question).

Example format:
Q1. What is...?
a) ...
b) ...
c) ...
d) ...
Answer: b

Return exactly 10 questions in that format.
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

# Function to parse questions
def parse_questions(raw_text):
    lines = raw_text.strip().split("\n")
    questions = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("Q"):
            q = lines[i]
            opts = [lines[i+1], lines[i+2], lines[i+3], lines[i+4]]
            ans = lines[i+5].split(":")[-1].strip()
            questions.append({"q": q, "options": opts, "answer": ans})
            i += 6
        else:
            i += 1
    return questions

# Topic input and generate button
if not st.session_state.questions and not st.session_state.submitted:
    topic = st.text_input("Enter a quiz topic (e.g., Python, Space, History):")
    difficulty = st.selectbox("Select difficulty level:", ["Beginner", "Intermediate", "Advanced"])

    if st.button("Generate Quiz") and topic:
        raw = generate_quiz(topic,difficulty)
        st.session_state.questions = parse_questions(raw)
    
# Display quiz
if st.session_state.questions and not st.session_state.submitted:
    st.subheader("📝 Quiz Questions")

    for idx, q in enumerate(st.session_state.questions):
        # Use columns to place question + hint button side-by-side
        col1, col2 = st.columns([4, 1])  # Wider question, smaller button

        with col1:
            st.markdown(f"**{q['q']}**")

        with col2:
            if st.button(f"💡 Hint", key=f"hint_btn_{idx}"):
                with st.spinner("Getting a hint..."):
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    hint_prompt = f"Give a short, helpful hint for this question without revealing the answer:\n\n{q['q']}\n\nOptions:\n" + "\n".join(q['options'])
                    response = model.generate_content(hint_prompt)
                    st.session_state.hints[idx] = response.text.strip()

        # Display options
        selected_option = st.radio(
            label="Select an option:",
            options=q["options"],
            index=None if st.session_state.user_answers[idx] is None else q["options"].index(st.session_state.user_answers[idx]),
            key=f"q{idx}",
            label_visibility="collapsed"
        )
        st.session_state.user_answers[idx] = selected_option

        # Display hint below options
        if st.session_state.hints[idx]:
            st.info(f"💡 Hint: {st.session_state.hints[idx]}")

        st.markdown("---")


    if st.button("Submit Quiz"):
        st.session_state.submitted = True

# Display score
if st.session_state.submitted:
    score = 0
    results = []

    for idx, q in enumerate(st.session_state.questions):
        try:
            correct_index = ord(q["answer"]) - ord("a")
            correct_option = q["options"][correct_index]
        except:
            correct_option = "Unknown"
            correct_index = None
        user_ans = st.session_state.user_answers[idx]
        is_correct = (correct_index is not None) and (user_ans == correct_option)

        if is_correct:
            score += 1
        results.append({
            "q_num": idx + 1,
            "question": q["q"][3:],
            "your_answer": user_ans or "Not answered",
            "correct_answer": correct_option,
            "result": "✅ Correct" if is_correct else "❌ Incorrect"
        })

    # Show score first
    st.success(f"🎉 You scored {score} / 10")
    st.markdown("---")
    st.subheader("🧐 Question-wise Analysis")

    # Then show analysis
    for r in results:
        st.markdown(f"**Q{r['q_num']}:** {r['question']}")
        st.markdown(f"- Your answer: `{r['your_answer']}`")
        st.markdown(f"- Correct answer: `{r['correct_answer']}`")
        st.markdown(f"- Result: {r['result']}")
        st.markdown("---")

    if st.button("Start New Quiz"):
        st.session_state.questions = []
        st.session_state.user_answers = [None] * 10
        st.session_state.submitted = False
        st.session_state.hints = [None] * 10

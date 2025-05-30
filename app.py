import streamlit as st
import google.generativeai as genai
import re
import pyperclip # Import pyperclip

# --- Inject custom CSS ---
st.markdown("""
<style>
    /* Basic styling for the body and main content */
    body {
        font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif;
        line-height: 1.6;
        color: #333; /* Dark grey text */
        background-color: #f4f4f4; /* Light grey background */
        padding: 20px;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Style for sections */
    .stHeading, .stText, .stTextInput, .stRadio, .stButton, .stAlert {
        margin-bottom: 15px; /* Add space below elements */
    }

    /* Card-like sections for better visual separation */
    .stCard {
        background-color: #fff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* Style for the output section */
    .output-section {
        border-top: 2px solid #eee; /* Separator line */
        margin-top: 20px;
        padding-top: 20px;
    }

    /* Style for the history section */
    .history-item {
         border-bottom: 1px dashed #ccc; /* Dashed separator */
         padding-bottom: 15px;
         margin-bottom: 15px;
    }
    .history-item:last-child {
        border-bottom: none; /* No border for the last item */
        margin-bottom: 0;
    }

    /* Style for the TOP5 section - make it stand out */
    .top5-section {
        background-color: #ffeacc; /* Light orange background */
        border: 2px solid #ff9900; /* Orange border */
        padding: 20px;
        border-radius: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    .top5-section h2 {
        color: #ff9900; /* Match header color to border */
        margin-top: 0;
    }
    .top5-section li {
        margin-bottom: 10px;
    }

</style>
""", unsafe_allow_html=True)


# --- API Key Check ---
try:
    api_key = st.secrets["gemini_api_key"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("Gemini API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인해주세요.")
    st.stop()

# --- Model Configuration ---
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# --- Session State Initialization ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'ranked' not in st.session_state:
    st.session_state.ranked = []
# Store the most recent result separately for copy/regen
if 'last_response' not in st.session_state:
    st.session_state.last_response = None

# --- UI Elements ---
st.title("🤬 AI가 대신 싸워드립니다 – 디스해줘봇")
st.write("찔리는 한마디, AI가 대신 해드립니다. 감정 정리용 디스 멘트 생성기")

# Wrap input section in a card
st.markdown('<div class="stCard">', unsafe_allow_html=True)
user_input = st.text_input(
    label="상황 or 이름",
    placeholder="김영훈이 나한테 말없이 약속 펑크냄"
)

dis_style = st.radio(
    label="디스 스타일 선택",
    options=["병맛 스타일", "은근히 비꼬기", "사이다 직설", "공감형 위로"]
)
st.markdown('</div>', unsafe_allow_html=True) # Close card div

# --- Function to generate and display response ---
def generate_and_display_response(input_text, style):
    # 프롬프트 수정: 결과 텍스트만 생성하도록 명확히 지시
    prompt = f"""상황: {input_text}
디스 스타일: {style}
요청된 상황과 스타일에 맞춰 다음 정보를 생성하고, 코드나 코드 설명 없이 결과 텍스트만 다음 형식으로 출력하세요:
1. 디스 멘트 (한 줄, 굵게 강조)
2. 감정 분석 (감정 종류 + 감정 강도 %)
3. 대응 전략 (어떻게 대처하면 좋을지 조언)

예시 출력 형식:
1. **[여기에 디스 멘트]**
2. 감정 분석: [감정 종류] ([감정 강도]%)
3. 대응 전략: [여기에 조언]
"""
    try:
        with st.spinner('디스 멘트 생성 중...'):
            response = model.generate_content(prompt)
            response_text = response.text

            # Store the raw response text
            st.session_state.last_response = response_text

            # Wrap output in a distinct section
            st.markdown('<div class="stCard output-section">', unsafe_allow_html=True)
            st.markdown("### 생성 결과:") # Add a header for the output
            st.markdown(response_text)
            st.markdown('</div>', unsafe_allow_html=True) # Close output section div

            # Extract emotion percentage
            emotion_percentage = 0
            percentage_match = re.search(r'(\d+)%', response_text)
            if percentage_match:
                try:
                    emotion_percentage = int(percentage_match.group(1))
                except ValueError:
                    emotion_percentage = 0

            # Add to history
            st.session_state.history.append({
                "input": input_text,
                "style": style,
                "result": response_text,
                "percentage": emotion_percentage
            })

            # Update ranked list
            sorted_history = sorted(st.session_state.history, key=lambda x: x.get("percentage", 0), reverse=True)
            st.session_state.ranked = sorted_history[:5]

    except Exception as e:
        st.error(f"AI 응답 생성에 실패했습니다. 잠시 후 다시 시도해주세요. 오류: {e}")
        st.session_state.last_response = None # Clear last response on failure

# --- Main Button ---
if st.button("디스 멘트 생성하기"):
    if user_input:
        generate_and_display_response(user_input, dis_style)
    else:
        st.warning("상황 또는 이름을 입력해주세요.")

# --- Additional Buttons (show only if a response was generated) ---
if st.session_state.last_response:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("더 센 거 해줘 😈"):
            if user_input:
                # Re-generate with the same input and style
                generate_and_display_response(user_input, dis_style)
            else:
                 st.warning("상황 또는 이름을 입력해주세요.") # Should not happen if button is visible
    with col2:
        if st.button("복사하기 ✂️"):
            try:
                pyperclip.copy(st.session_state.last_response)
                st.success("복사되었습니다!")
            except pyperclip.PyperclipException:
                st.warning("클립보드에 복사할 수 없습니다. 지원되지 않는 환경일 수 있습니다.")


# --- History Section ---
st.header("🕓 감정 히스토리")
if st.session_state.history:
    st.markdown('<div class="stCard">', unsafe_allow_html=True) # Wrap history in a card
    # Use a plain div for history items as the card adds padding
    for item in reversed(st.session_state.history[-5:]):
        st.markdown('<div class="history-item">', unsafe_allow_html=True)
        st.subheader(f"상황: {item['input']} | 스타일: {item['style']}")
        st.markdown(item['result'])
        st.markdown('</div>', unsafe_allow_html=True) # Close history-item div

    st.markdown('</div>', unsafe_allow_html=True) # Close history card div

else:
    st.write("아직 생성된 디스 멘트가 없습니다.")

# --- TOP5 Section ---
# Wrap TOP5 section in a distinct, emphasized div
st.markdown('<div class="top5-section">', unsafe_allow_html=True)
st.header("🏆 감정 강도 TOP5")
if st.session_state.ranked:
    # Use markdown list for better formatting
    st.markdown("<ul>", unsafe_allow_html=True) # Start unordered list
    for i, item in enumerate(st.session_state.ranked):
        lines = item['result'].split('\\n')
        dis_ment_line = "디스 멘트 추출 실패"
        for line in lines:
            if line.strip().startswith("1.") and "**" in line:
                 match = re.search(r'\*\*(.*?)\*\*', line)
                 if match:
                    dis_ment_line = match.group(1).strip()
                    break
        # Format list item
        st.markdown(f"<li><b>{i + 1}위 (감정 강도 {item.get('percentage', 0)}%):</b> {dis_ment_line}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True) # End unordered list

else:
    st.write("아직 감정 강도 TOP5 결과가 없습니다.")
st.markdown('</div>', unsafe_allow_html=True) # Close TOP5 section div

# --- Advertisement ---
st.markdown("<center><i>📢 광고 자리입니다 (예: AdSense, 카카오 등)</i></center>", unsafe_allow_html=True)

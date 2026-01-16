import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

st.set_page_config(page_title="خبير المعرفة الذكي", page_icon="🧠")

# إعداد المفتاح بأمان
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ المفتاح غير موجود في Secrets!")

st.title("🧠 مساعدك الذكي")

# منطق جلب النص من PDF
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

# منطق جلب النص من يوتيوب
def get_youtube_text(url):
    try:
        video_id = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([i['text'] for i in transcript])
    except Exception as e:
        st.error(f"حدث خطأ في اليوتيوب: {e}")
        return None

source = st.sidebar.radio("المصدر:", ("PDF", "YouTube"))

if source == "PDF":
    files = st.file_uploader("ارفع ملفاتك", accept_multiple_files=True)
    if st.button("تحليل"):
        with st.spinner("جاري القراءة..."):
            st.session_state['data'] = get_pdf_text(files)
            st.success("تم تحليل المستند!")
else:
    url = st.text_input("رابط الفيديو:")
    if st.button("تحليل الفيديو"):
        with st.spinner("جاري الاستخراج..."):
            st.session_state['data'] = get_youtube_text(url)
            st.success("تم تحليل الفيديو!")

# الدردشة
question = st.text_input("اسأل عن المحتوى:")
if question:
    if 'data' in st.session_state and st.session_state['data']:
        try:
            # استخدام الموديل الأحدث والأكثر استقراراً
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"بناءً على النص التالي، أجب باختصار واحترافية:\n\nنص المصدر: {st.session_state['data'][:10000]}\n\nالسؤال: {question}"
            response = model.generate_content(full_prompt)
            st.markdown("### 🤖 الإجابة:")
            st.write(response.text)
        except Exception as e:
            st.error(f"خطأ في الاتصال بجوجل: {e}")
    else:
        st.warning("يرجى تحليل مصدر أولاً!")
        

import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

# --- 1. إعدادات الصفحة والفخامة ---
st.set_page_config(page_title="AI Knowledge Hub", page_icon="🧠", layout="wide")

# --- 2. الربط الآمن بمفتاح Google API ---
# سيقوم الكود بالبحث عن المفتاح في Secrets الخاصة بـ Streamlit
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ خطأ: لم يتم العثور على مفتاح GOOGLE_API_KEY في إعدادات Secrets.")

# --- 3. وظائف استخراج النصوص (المهام الأساسية) ---
def get_pdf_text(pdf_docs):
    """استخراج النص من ملفات PDF المرفوعة"""
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    return text

def get_youtube_text(video_url):
    """استخراج النص (الترجمة) من فيديوهات اليوتيوب"""
    try:
        # استخراج معرف الفيديو من الرابط
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        else:
            video_id = video_url.split("/")[-1]
            
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([i['text'] for i in transcript])
    except Exception as e:
        st.error(f"⚠️ تعذر جلب نص الفيديو. تأكد من وجود ترجمة مصاحبة (Subtitles).")
        return None

# --- 4. واجهة المستخدم (UI Design) ---
st.markdown("<h1 style='text-align: center;'>🧠 منصة المعرفة التفاعلية</h1>", unsafe_allow_html=True)
st.markdown("---")

# القائمة الجانبية للتحكم
st.sidebar.title("⚙️ الإعدادات")
source_type = st.sidebar.radio("اختر مصدر البيانات:", ("ملف PDF", "رابط YouTube"))

# تخزين البيانات في جلسة العمل (Session State) لضمان عدم ضياعها عند التفاعل
if 'final_context' not in st.session_state:
    st.session_state['final_context'] = ""

if source_type == "ملف PDF":
    uploaded_files = st.sidebar.file_uploader("ارفع ملفات PDF", accept_multiple_files=True, type=['pdf'])
    if st.sidebar.button("تحليل المستندات"):
        if uploaded_files:
            with st.spinner("جاري قراءة الملفات..."):
                st.session_state['final_context'] = get_pdf_text(uploaded_files)
                st.sidebar.success("✅ تم تحليل المستندات بنجاح!")
        else:
            st.sidebar.warning("يرجى رفع ملف أولاً.")

else:
    yt_link = st.sidebar.text_input("ضع رابط YouTube هنا:")
    if st.sidebar.button("تحليل الفيديو"):
        if yt_link:
            with st.spinner("جاري استخراج نص الفيديو..."):
                st.session_state['final_context'] = get_youtube_text(yt_link)
                if st.session_state['final_context']:
                    st.sidebar.success("✅ تم تحليل الفيديو بنجاح!")
        else:
            st.sidebar.warning("يرجى وضع الرابط أولاً.")

# --- 5. منطقة الدردشة والذكاء الاصطناعي ---
user_query = st.text_input("💬 اسأل الخبير عن أي شيء في المحتوى المرفوع:")

if user_query:
    if st.session_state['final_context']:
        try:
            with st.spinner("جاري توليد الإجابة..."):
                # استخدام الموديل الأكثر توافقاً وتوفراً
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # بناء الـ Prompt بأسلوب هندسي دقيق
                prompt = f"""
                أنت مساعد ذكي خبير. استخدم النص التالي فقط للإجابة على السؤال بدقة.
                إذا لم تكن الإجابة موجودة في النص، قل 'هذه المعلومة غير متوفرة في المصدر'.
                
                النص المصدر:
                {st.session_state['final_context'][:15000]} 
                
                السؤال:
                {user_query}
                
                الإجابة:
                """
                
                response = model.generate_content(prompt)
                st.markdown("### 🤖 الإجابة:")
                st.info(response.text)
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")
    else:
        st.warning("⚠️ يرجى تحليل مصدر بيانات (PDF أو YouTube) قبل السؤال.")
                

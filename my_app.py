import streamlit as st
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os

# --- 1. إعدادات الصفحة والتصميم الجمالي الفخم ---
st.set_page_config(page_title="AI Knowledge Hub", page_icon="🧠", layout="centered")

# إضافة CSS مخصص لتكبير الخط وتحسين شكل الأزرار
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-image: linear-gradient(to right, #1e3a8a, #3b82f6);
        color: white;
        font-size: 20px !important;
        font-weight: bold;
        border: none;
    }
    h1 {
        color: #1e3a8a;
        font-size: 45px !important;
        text-align: center;
        margin-bottom: 0px;
    }
    .stTextInput input { font-size: 18px !important; }
    .stRadio div[role='radiogroup'] {
        justify-content: center;
        gap: 30px;
    }
    div[data-baseweb="radio"] div { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعداد المفتاح والتحقق منه ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ لم يتم العثور على GOOGLE_API_KEY في Secrets!")

# --- 3. وظائف معالجة البيانات ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        except: continue
    return text

def get_youtube_text(video_url):
    try:
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        else:
            video_id = video_url.split("/")[-1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ar', 'en'])
        return " ".join([i['text'] for i in transcript])
    except: return None

# --- 4. واجهة المستخدم الرئيسية ---
st.markdown("<h1>🧠 خبير المعرفة الذكي</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 22px; color: #64748b;'>قم بتحليل الكتب أو الفيديوهات بضغطة زر</p>", unsafe_allow_html=True)
st.markdown("---")

# اختيار المصدر بشكل أنيق في المنتصف
source_type = st.radio("", ("📄 ملف PDF", "🎥 فيديو YouTube"), horizontal=True)

if 'final_context' not in st.session_state:
    st.session_state['final_context'] = ""

# عرض أدوات الرفع بناءً على الاختيار
col_main = st.columns([1, 4, 1])[1]
with col_main:
    if source_type == "📄 ملف PDF":
        uploaded_files = st.file_uploader("ارفع ملفاتك هنا", accept_multiple_files=True, type=['pdf'])
        if st.button("🚀 ابدأ تحليل المستندات"):
            if uploaded_files:
                with st.spinner("جاري استخراج المعرفة..."):
                    st.session_state['final_context'] = get_pdf_text(uploaded_files)
                    st.success("✅ تم تحليل الكتاب بنجاح!")
            else: st.warning("يرجى اختيار ملف أولاً.")
    else:
        yt_link = st.text_input("ضع رابط الفيديو هنا:", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("🚀 ابدأ تحليل الفيديو"):
            if yt_link:
                with st.spinner("جاري معالجة الفيديو..."):
                    st.session_state['final_context'] = get_youtube_text(yt_link)
                    if st.session_state['final_context']:
                        st.success("✅ تم تحليل الفيديو بنجاح!")
                    else: st.error("تعذر جلب النص. تأكد من وجود ترجمة.")

st.markdown("---")

# --- 5. منطقة الدردشة الذكية (مع البحث التلقائي عن الموديل) ---
st.markdown("<h2 style='text-align: center;'>💬 اسأل خبيرك الآن</h2>", unsafe_allow_html=True)
user_query = st.text_input("", placeholder="ماذا تريد أن تعرف عن المحتوى؟")

if user_query:
    if st.session_state['final_context']:
        try:
            with st.spinner("جاري استحضار الإجابة..."):
                # --- تقنية الاكتشاف التلقائي للموديلات ---
                # نجلب كل الموديلات المتاحة في حسابك التي تدعم توليد المحتوى
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # ترتيب الأولويات: نبحث عن 1.5 flash أولاً، ثم 1.0 pro، ثم أي موديل متاح
                selected_model = ""
                if 'models/gemini-1.5-flash' in available_models:
                    selected_model = 'models/gemini-1.5-flash'
                elif 'models/gemini-pro' in available_models:
                    selected_model = 'models/gemini-pro'
                else:
                    selected_model = available_models[0] # اختيار أول موديل متاح كحل نهائي
                
                model = genai.GenerativeModel(selected_model)
                
                # بناء البرومبت (Prompt)
                prompt = f"""
                أجب على السؤال التالي بناءً على النص المزود فقط.
                السؤال: {user_query}
                
                النص: {st.session_state['final_context'][:20000]}
                """
                
                response = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"<div style='background-color: #e2e8f0; padding: 20px; border-radius: 10px; font-size: 20px;'>{response.text}</div>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ حدث خطأ فني: {e}")
            st.info("حاول تحديث الصفحة أو التحقق من مفتاح الـ API.")
    else:
        st.warning("⚠️ يرجى تحميل وتحليل مصدر أولاً.")
        

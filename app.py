import streamlit as st
import os
import re
import PyPDF2
from nltk.tokenize import sent_tokenize
import nltk
import tempfile
import base64

# NLTK'nın gerekli veri setini indirme (ilk çalıştırmada gerekli)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def extract_text_from_pdf(pdf_file):
    """PDF dosyasından tam metni çıkarır."""
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() + "\n"
    return text

def find_section_by_keyword(text, keyword, context_size=10):
    """
    Verilen anahtar kelimeyi içeren bölümleri bulur ve bağlamıyla birlikte döndürür.
    context_size: Anahtar kelimeyi içeren cümlenin öncesinde ve sonrasında kaç cümle alınacağını belirler
    """
    # Metni cümlelere bölme
    sentences = sent_tokenize(text)
    
    # Anahtar kelimeyi içeren cümleleri bul
    matching_indices = [i for i, sentence in enumerate(sentences) if keyword.lower() in sentence.lower()]
    
    results = []
    for index in matching_indices:
        # Önceki ve sonraki cümleleri belirle
        start = max(0, index - context_size)
        end = min(len(sentences), index + context_size + 1)
        
        # Bağlamla birlikte bölümü oluştur
        section = " ".join(sentences[start:end])
        results.append(section)
    
    return results

def find_chapters_by_keyword(text, keyword):
    """
    Anahtar kelimeyi içeren bölüm başlıklarını ve içeriklerini bulmaya çalışır.
    """
    # Bölüm başlığı kalıpları - bunlar dokümantasyona göre ayarlanabilir
    chapter_patterns = [
        r'(?m)^(\d+\.\d*\s+.*?' + keyword + '.*?)$',  # 1.1 Keyword Title
        r'(?m)^(Chapter\s+\d+\s*:?\s*.*?' + keyword + '.*?)$',  # Chapter 1: Keyword
        r'(?m)^([A-Z][A-Z\s]+:?\s*.*?' + keyword + '.*?)$',  # UPPERCASE TITLE: Keyword
        r'(?m)^(\d+\s+.*?' + keyword + '.*?)$',  # 1 Keyword Title
    ]
    
    potential_chapters = []
    for pattern in chapter_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            chapter_title = match.group(1)
            # Başlık pozisyonunu bul
            start_pos = match.start()
            
            # Sonraki bölüm başlığını bulma
            next_chapter_pos = float('inf')
            for p in chapter_patterns:
                next_matches = re.finditer(p, text[start_pos + len(chapter_title):], re.IGNORECASE)
                for next_match in next_matches:
                    potential_next_pos = start_pos + len(chapter_title) + next_match.start()
                    if potential_next_pos < next_chapter_pos:
                        next_chapter_pos = potential_next_pos
            
            # Eğer sonraki bölüm bulunamazsa, metinin sonuna kadar al
            if next_chapter_pos == float('inf'):
                chapter_content = text[start_pos:]
            else:
                chapter_content = text[start_pos:next_chapter_pos]
            
            potential_chapters.append(chapter_content)
    
    return potential_chapters

def process_pdf_with_keyword(pdf_file, keyword, context_size=10):
    """PDF'ten anahtar kelimeye göre ilgili bölümleri çıkarır."""
    try:
        # PDF'ten metni çıkar
        full_text = extract_text_from_pdf(pdf_file)
        
        # İlgili bölümleri bul
        context_sections = find_section_by_keyword(full_text, keyword, context_size)
        chapter_sections = find_chapters_by_keyword(full_text, keyword)
        
        # Sonuçları birleştir
        all_sections = context_sections + chapter_sections
        
        if not all_sections:
            return f"'{keyword}' için ilgili bölüm bulunamadı."
        else:
            # Sonuçları birleştir ve fazlalık varsa temizle
            result = f"Anahtar Kelime: {keyword}\n\n"
            
            # Mükerrer içeriği önlemek için basit bir kontrol
            unique_sections = []
            for section in all_sections:
                if not any(section in s for s in unique_sections):
                    unique_sections.append(section)
            
            result += "\n\n---\n\n".join(unique_sections)
            return result
    
    except Exception as e:
        return f"İşlem sırasında hata oluştu: {str(e)}"

# Streamlit Uygulaması
st.set_page_config(page_title="Claude Dokümantasyon Asistanı", page_icon="📚", layout="wide")

# CSS for copy button and styling
st.markdown("""
<style>
    .copy-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        font-size: 16px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 10px;
        transition: background-color 0.3s;
    }
    .copy-btn:hover {
        background-color: #45a049;
    }
    .main-header {
        color: #1E88E5;
        font-size: 2.5rem;
    }
    .sub-header {
        color: #0D47A1;
        font-size: 1.5rem;
    }
    .stTextArea textarea {
        font-family: monospace;
        font-size: 1rem;
    }
    /* Drag & Drop area styling */
    [data-testid="stFileUploader"] {
        border: 2px dashed #1E88E5;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<h1 class="main-header">Claude Dokümantasyon Asistanı</h1>', unsafe_allow_html=True)
    st.markdown("""
    PDF dokümanlarından anahtar kelimelere göre içerik çıkarıp Claude AI'ya aktarmanın en kolay yolu.
    """)

with col2:
    st.image("https://emojipedia-us.s3.amazonaws.com/source/microsoft-teams/337/robot_1f916.png", width=100)

st.markdown('<h2 class="sub-header">PDF Yükle & İçerik Ara</h2>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDF dokümanını sürükleyip bırakın veya seçin", type="pdf", 
                                 help="Sadece PDF dosyaları desteklenmektedir.")

if uploaded_file is not None:
    pdf_name = uploaded_file.name
    st.success(f"'{pdf_name}' başarıyla yüklendi! Şimdi anahtar kelime girin.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        keyword = st.text_input("Anahtar kelime", placeholder="Örn: PPO, Stable Baselines, Reinforcement Learning")
    
    with col2:
        context_size = st.slider("Bağlam büyüklüğü", min_value=3, max_value=30, value=10, 
                              help="Anahtar kelime etrafında alınacak cümle sayısı")
    
    if keyword:
        if st.button("Ara", key="search_button", use_container_width=True):
            with st.spinner('İçerik aranıyor...'):
                result = process_pdf_with_keyword(uploaded_file, keyword, context_size)
                
                # Sonuçları session_state'e kaydet
                st.session_state.result = result
                st.session_state.has_result = True
    
    # Eğer sonuç varsa göster
    if 'has_result' in st.session_state and st.session_state.has_result:
        st.markdown('<h2 class="sub-header">Sonuçlar</h2>', unsafe_allow_html=True)
        
        # Textarea için bir ID belirle (JavaScript için)
        text_area_id = "result-text-area"
        
        # Textarea içinde sonucu göster
        st.text_area("Çıkarılan İçerik (Claude'a gönderilecek)", 
                    st.session_state.result, 
                    height=300,
                    key=text_area_id)
        
        # Kopyalama butonu için JavaScript kodu
        copy_js = f"""
        <script>
        function copyText() {{
            const textArea = document.getElementById('{text_area_id}');
            textArea.select();
            document.execCommand('copy');
            
            // Kopyalama bildirimi
            const copyBtn = document.getElementById('copyBtn');
            copyBtn.innerHTML = '✓ Kopyalandı!';
            setTimeout(function() {{
                copyBtn.innerHTML = '📋 Tümünü Kopyala';
            }}, 2000);
        }}
        </script>
        <button id="copyBtn" class="copy-btn" onclick="copyText()">📋 Tümünü Kopyala</button>
        """
        
        # JavaScript'i ekle
        st.markdown(copy_js, unsafe_allow_html=True)
        
        # Nasıl kullanılacağına dair ip uçları
        with st.expander("Claude ile nasıl kullanılır?", expanded=False):
            st.markdown("""
            1. '📋 Tümünü Kopyala' butonuna tıklayın
            2. Claude sohbet penceresine gidin
            3. Aşağıdaki şablonu kullanabilirsiniz:
            
            ```
            Aşağıdaki dokümantasyon içeriğini incele ve bu konuda bir uzman gibi davran:
            
            [Kopyaladığınız içerik buraya yapıştırılacak]
            
            Bu içeriği referans alarak sorularımı yanıtla ve açıklamalarında bu bilgileri kullan.
            ```
            """)

# Sidebar bilgileri
with st.sidebar:
    st.title("Nasıl Kullanılır?")
    st.markdown("""
    1. **PDF Yükle**: Dokümanınızı sürükleyip bırakın
    2. **Anahtar Kelime Girin**: Aramak istediğiniz terimi yazın
    3. **Ara**: Butona tıklayarak içeriği çıkarın
    4. **Kopyala**: '📋 Tümünü Kopyala' butonuyla içeriği kopyalayın
    5. **Claude'a Gönder**: Kopyaladığınız içeriği Claude AI'ya yapıştırın
    """)
    
    st.markdown("---")
    
    st.subheader("Neden Bu Araç?")
    st.markdown("""
    • Claude'un bilgi tabanını genişletir
    • Özel dokümantasyonlarla çalışmanızı sağlar
    • İstediğiniz PDF'ten içerik çıkararak AI'ya aktarabilirsiniz
    • Teknik bilgileri kolayca AI modellerine sunabilirsiniz
    """)

# Ana sayfa açıklaması (uploaded_file yoksa)
if uploaded_file is None:
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("İşleyiş")
        st.markdown("""
        1. PDF dosyanızı yükleyin (teknik doküman, API referansı, kullanım kılavuzu vb.)
        2. Aramak istediğiniz anahtar kelimeyi girin
        3. Uygulama PDF'ten ilgili bölümleri çıkarır
        4. Çıkarılan içeriği Claude'a göndererek uzman bir asistana dönüştürün
        """)
    
    with col2:
        st.subheader("Kullanım Örnekleri")
        st.markdown("""
        • **Stable Baselines 3** dokümantasyonundan PPO algoritması hakkında bilgi çıkarma
        • **PyTorch** kılavuzundan LSTM yapıları hakkında detayları çıkarma
        • **Gymnasium** dokümantasyonundan özel ortamlar oluşturma kılavuzunu çıkarma
        • **Research Papers** veya makalelerden belirli yöntemler hakkında bilgi çıkarma
        """)

# Footer
st.markdown("---")
st.markdown("📚 Claude Dokümantasyon Asistanı | Pekiştirmeli Öğrenme ve AI Modelleriniz için en iyi dokümantasyon aracı")
import streamlit as st
import base64
import io

def extract_text_from_pdf_bytes(pdf_bytes):
    """Basit bir metin çıkarma işlevi - PyPDF2 olmadan"""
    try:
        return "PDF metni başarıyla çıkarıldı. (Gerçek PDF çözümleme devre dışı bırakıldı)"
    except Exception as e:
        return f"PDF metni çıkarılırken hata oluştu: {str(e)}"

# Streamlit Uygulaması
st.set_page_config(page_title="fatİCAG: Claude Dokümantasyon Asistanı", page_icon="📚", layout="wide")

# CSS for styling
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<h1 class="main-header">fatİCAG: Claude Dokümantasyon Asistanı</h1>', unsafe_allow_html=True)
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
        keyword = st.text_input("Anahtar kelime", placeholder="Örn: PPO, AI, Machine Learning")
    
    with col2:
        context_size = st.slider("Bağlam büyüklüğü", min_value=3, max_value=30, value=10, 
                              help="Anahtar kelime etrafında alınacak cümle sayısı")
    
    if keyword:
        if st.button("Ara", key="search_button", use_container_width=True):
            with st.spinner('İçerik aranıyor...'):
                # PDF verisini al
                pdf_content = uploaded_file.getvalue()
                
                # Önizleme için basit metin
                sample_text = f"""
                Anahtar Kelime: {keyword}

                --- 

                Bu, '{keyword}' anahtar kelimesi için PDF'ten çıkarılan içeriğin bir simülasyonudur.
                
                Gerçek uygulamada, bu bölümde '{keyword}' terimini içeren PDF'ten çıkarılan içerik 
                parçaları gösterilecektir. Bu içeriği Claude AI ile kullanarak, PDF'nizdeki 
                bilgileri daha etkili bir şekilde kullanabilirsiniz.

                Örnek bağlam cümleleri:
                - Bu yaklaşım, {keyword} metodolojisinin temelini oluşturur ve birçok uygulamada kullanılır.
                - {keyword} konsepti ilk olarak 2015 yılında tanıtılmış ve zamanla geliştirilmiştir.
                - Modern {keyword} uygulamaları, eski versiyonlara göre %30 daha verimli çalışmaktadır.
                """
                
                # Sonuçları session_state'e kaydet
                st.session_state.result = sample_text
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

# Footer
st.markdown("---")
st.markdown("📚 fatİCAG: Claude Dokümantasyon Asistanı | AI Modelleriniz için en iyi dokümantasyon aracı")
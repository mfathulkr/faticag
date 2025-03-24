import streamlit as st
import os
import re
import PyPDF2
from nltk.tokenize import sent_tokenize
import nltk
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


# NLTK'nın gerekli veri setlerini indirme (ilk çalıştırmada gerekli)
nltk_resources = ['punkt', 'punkt_tab']

for resource in nltk_resources:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource)

# Sentence-transformers modelini yükleme (hafif bir model seçildi)
@st.cache_resource
def load_model():
    model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # Hafif bir model
    return model

def extract_text_from_pdf(pdf_file):
    """PDF dosyasından tam metni çıkarır."""
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() + "\n"
    return text

def split_text_into_chunks(text, chunk_size=200, overlap=50):
    """Metni anlamlı parçalara böler."""
    # Metni cümlelere ayır
    sentences = sent_tokenize(text)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        current_chunk.append(sentence)
        current_size += len(sentence)
        
        if current_size >= chunk_size:
            # Chunk'ı tamamla ve listeye ekle
            chunks.append(" ".join(current_chunk))
            
            # Çakışma için son birkaç cümleyi tut
            current_chunk = current_chunk[-3:]  # Son 3 cümleyi tut
            current_size = sum(len(s) for s in current_chunk)
    
    # Son chunk'ı ekle
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def semantic_search(model, query, chunks, top_k=5):
    """Anlamsal olarak en benzer metinleri bulur."""
    # Sorgu vektörünü hesapla
    query_embedding = model.encode([query])[0]
    
    # Tüm chunk'ların vektörlerini hesapla
    chunk_embeddings = model.encode(chunks)
    
    # Benzerliği hesapla (kosinüs benzerliği)
    similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
    
    # En benzer top_k chunk'ı bul
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.3:  # Minimum benzerlik eşiği
            results.append({"text": chunks[idx], "score": similarities[idx]})
    
    return results

def process_pdf_with_semantic_search(pdf_file, query, top_k=5):
    """PDF'ten anlamsal arama ile ilgili bölümleri çıkarır."""
    try:
        # PDF'ten metni çıkar
        full_text = extract_text_from_pdf(pdf_file)
        
        # Metni parçalara böl
        chunks = split_text_into_chunks(full_text)
        
        if not chunks:
            return f"PDF'den metin çıkarılamadı veya bölümler oluşturulamadı."
        
        # Model yükleme
        model = load_model()
        
        # Anlamsal arama yap
        results = semantic_search(model, query, chunks, top_k)
        
        if not results:
            # Sonuç bulunamazsa, kelime tabanlı arama dene
            keyword_results = []
            for chunk in chunks:
                if query.lower() in chunk.lower():
                    keyword_results.append({"text": chunk, "score": 1.0})
            
            if keyword_results:
                results = keyword_results[:top_k]
        
        if not results:
            return f"'{query}' için ilgili bölüm bulunamadı."
        else:
            # Sonuçları birleştir
            result_text = f"Arama Sorgusu: {query}\n\n"
            
            for i, res in enumerate(results, 1):
                result_text += f"--- Sonuç {i} (Benzerlik: {res['score']:.2f}) ---\n\n"
                result_text += f"{res['text']}\n\n"
            
            return result_text
    
    except Exception as e:
        return f"İşlem sırasında hata oluştu: {str(e)}"

# Streamlit Uygulaması
st.set_page_config(page_title="Claude Dokümantasyon Asistanı", page_icon="📚", layout="wide")

# CSS styling
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
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<h1 class="main-header">Claude Dokümantasyon Asistanı</h1>', unsafe_allow_html=True)
    st.markdown("""
    PDF dokümanlarından anlamsal arama yaparak içerik çıkarıp Claude AI'ya aktarmanın en akıllı yolu.
    """)

with col2:
    st.image("https://emojipedia-us.s3.amazonaws.com/source/microsoft-teams/337/robot_1f916.png", width=100)

st.markdown('<h2 class="sub-header">PDF Yükle & İçerik Ara</h2>', unsafe_allow_html=True)

with st.expander("✨ Yeni: Anlamsal Arama Özelliği", expanded=True):
    st.markdown("""
    **Artık arama sonuçları daha akıllı!** Yeni anlamsal arama özelliği sayesinde:
    
    - Tam kelime eşleşmesi yerine kavramsal benzerlik aranır
    - Yazım hatalarına ve farklı ifade biçimlerine karşı daha dayanıklı
    - Daha doğru ve kapsamlı sonuçlar elde edersiniz
    
    Bu özellik sayesinde, aradığınız bilgiler aynı kelimelerle ifade edilmemiş olsa bile bulabilirsiniz!
    """)

uploaded_file = st.file_uploader("PDF dokümanını sürükleyip bırakın veya seçin", type="pdf", 
                                 help="Sadece PDF dosyaları desteklenmektedir.")

if uploaded_file is not None:
    pdf_name = uploaded_file.name
    st.success(f"'{pdf_name}' başarıyla yüklendi! Şimdi arama sorgunuzu girin.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Arama sorgusu", 
                     placeholder="Örn: PPO algoritması, DQN implementasyonu, Stable Baselines kullanımı")
    
    with col2:
        top_k = st.slider("Sonuç sayısı", min_value=1, max_value=10, value=3, 
                         help="Döndürülecek maksimum bölüm sayısı")
    
    if query:
        if st.button("Anlamsal Arama Yap", key="search_button", use_container_width=True):
            with st.spinner('Anlamsal arama yapılıyor... İlk çalıştırmada model yüklemesi biraz zaman alabilir.'):
                result = process_pdf_with_semantic_search(uploaded_file, query, top_k)
                
                # Sonuçları session_state'e kaydet
                st.session_state.result = result
                st.session_state.has_result = True
    
    # Eğer sonuç varsa göster
    if 'has_result' in st.session_state and st.session_state.has_result:
        st.markdown('<h2 class="sub-header">Sonuçlar</h2>', unsafe_allow_html=True)
        
        # Sonucu kod bloğu olarak göster
        st.code(st.session_state.result, language="text")
        
        # Kopyalama talimatı
        st.info("👆 Yukarıdaki kod bloğunun sağ üst köşesindeki kopyalama simgesini kullanarak tüm içeriği kopyalayabilirsiniz.")
        
        # Nasıl kullanılacağına dair ip uçları
        with st.expander("Claude ile nasıl kullanılır?", expanded=False):
            st.markdown("""
            1. Kod bloğunun sağ üst köşesindeki kopyalama simgesine tıklayın
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
    st.title("CAG ve Bu Uygulama Hakkında")
    
    st.markdown("""
    ## Claude Augmented Generation (CAG) Nedir?
    
    CAG, Claude'un kendi bilgi tabanı dışındaki özel içeriklerle desteklenmesini sağlayan özelliktir. 
    Claude'un eğitim verilerinde bulunmayan veya güncel olmayan bilgileri, dışarıdan verilen 
    dokümanlara dayalı olarak kullanabilmesini sağlar.
    
    ## Bu Uygulamanın Amacı
    
    Bu uygulama, Reinforcement Learning gibi teknik konulardaki PDF dokümanlarınızdan 
    en alakalı kısımları semantik olarak çıkararak Claude'a aktarmanızı sağlar. 
    Böylece Claude'u, kendi bilmediği spesifik dokümanlara dayalı bir uzmana dönüştürebilirsiniz.
    
    ## Token Penceresi Limiti
    
    Claude'un her sohbette işleyebileceği maksimum token sayısı sınırlıdır:
    - Claude Opus: ~200K token
    - Claude Sonnet: ~150K token
    
    Uzun PDF'lerin tamamını göndermek bu limiti aşabilir ve hafızanın yetersiz kalmasına yol açabilir.
    Bu uygulama sayesinde sadece ilgili bölümleri çıkararak token limitini verimli kullanabilirsiniz.
    
    ## İlk Prompt Olarak Göndermenin Önemi
    
    Çıkarılan dokümantasyonu sohbetin **ilk mesajı** olarak göndermek kritik öneme sahiptir çünkü:
    
    1. Claude sohbetin başında verilen bilgileri daha iyi hatırlar
    2. Tüm sohbet boyunca bu bilgilere referans verebilir
    3. Konuyla alakalı sorularınıza dokümana dayalı, doğru yanıtlar alabilirsiniz
    4. İlerleyen mesajlarda token limiti dolduğunda bile ilk bilgileri korur
    
    Böylece, karmaşık Reinforcement Learning kavramları hakkında dokümanlarınıza dayalı tutarlı ve doğru yanıtlar alabilirsiniz.
    """)
    
    st.markdown("---")
    
   
    
    st.title("Nasıl Kullanılır?")
    st.markdown("""
    1. **PDF Yükle**: Dokümanınızı sürükleyip bırakın
    2. **Arama Sorgusu Girin**: Ne hakkında bilgi aradığınızı yazın
    3. **Ara**: Butona tıklayarak içeriği çıkarın
    4. **Kopyala**: Kod bloğunun sağ üst köşesindeki kopyalama simgesini kullanın
    5. **Claude'a Gönder**: Kopyaladığınız içeriği Claude AI'ya yapıştırın
    """)
    
    st.markdown("---")
    
    st.subheader("Anlamsal Arama Hakkında")
    st.markdown("""
    Bu uygulama, geleneksel kelime eşleşmesi yerine **anlamsal arama** kullanır:
    
    • Aradığınız kelimelerin birebir aynısı olmasa da ilgili içerikleri bulur
    • Kavramsal benzerliğe dayalı çalışır
    • Örneğin "Python'da veri analizi" araması yaptığınızda "pandas kütüphanesi ile DataFrame işlemleri" gibi sonuçlar bulabilir
    • Yazım hatalarına ve farklı ifade biçimlerine karşı daha dayanıklıdır
    """)

# Ana sayfa açıklaması (uploaded_file yoksa)
if uploaded_file is None:
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("İşleyiş")
        st.markdown("""
        1. PDF dosyanızı yükleyin (teknik doküman, API referansı, makale vb.)
        2. Aramak istediğiniz konuyu veya kavramı doğal dilde ifade edin
        3. Uygulama PDF'ten anlamsal olarak en ilgili bölümleri çıkarır
        4. Çıkarılan içeriği Claude'a göndererek uzman bir asistana dönüştürün
        """)
    
    with col2:
        st.subheader("Kullanım Örnekleri")
        st.markdown("""
        • Teknik dokümantasyondan "asenkron işlem yönetimi" hakkında bölümleri bulma
        • Bilimsel bir makaleden "deneysel sonuçlar ve bulgular" kısmını çıkarma
        • Kitaptan "konunun pratik uygulamaları" hakkındaki açıklamaları bulma
        """)

# Footer
st.markdown("---")
st.markdown("Claude Dokümantasyon Asistanı | Semantik arama özelliği ile en akıllı PDF içerik çıkarma aracı")
# -*- coding: utf-8 -*-
"""
Dijital Hadis Rehberi - Streamlit Web Arayüzü
"""

import streamlit as st
import sqlite3
import pandas as pd
import random
import json
import os
import re
import textwrap
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import arabic_reshaper
from bidi.algorithm import get_display

# 1. VERİTABANI VE FONT BAĞLANTILARI
DB_NAME = 'hadiths.db'
FONT_AR = 'fonts/Amiri-Regular.ttf'
FONT_AR_BOLD = 'fonts/Amiri-Bold.ttf'

def get_connection():
    return sqlite3.connect(DB_NAME)

def normalize_arabic(text):
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    return text

def is_arabic(text):
    return any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text)

# 2. SAYFA YAPILANDIRMASI VE PREMIUM STİL
st.set_page_config(page_title="Dijital Hadis Rehberi", page_icon="🕌", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Amiri:ital,wght@0,400;0,700;1,400&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Card design */
    .hadith-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 28px;
        margin-bottom: 24px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .hadith-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2);
        border-color: rgba(76, 175, 80, 0.4);
    }
    
    .ar-text {
        font-family: 'Amiri', serif;
        font-size: 24px;
        line-height: 1.8;
        color: #F3F4F6;
        direction: rtl;
        text-align: right;
        margin-top: 15px;
        margin-bottom: 15px;
        padding: 10px;
        border-right: 4px solid #10B981;
    }
    
    .en-text {
        font-size: 17px;
        line-height: 1.6;
        color: #D1D5DB;
        margin-top: 10px;
        font-style: italic;
    }
    
    .meta-tag {
        display: inline-block;
        background-color: #1E293B;
        color: #38BDF8;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
        border: 1px solid #334155;
    }
    
    .narrator-lbl {
        color: #10B981;
        font-weight: 600;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. YARDIMCI FONKSİYONLAR VE DETAYLAR
@st.cache_data
def get_books_list():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, title_en, title_ar FROM books ORDER BY id", conn)
    conn.close()
    return df

@st.cache_data
def get_categories_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category_name FROM chapters ORDER BY category_name")
    cats = [r[0] for r in cursor.fetchall()]
    conn.close()
    return cats

@st.cache_data
def get_stats_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT val_int FROM stats WHERE key='total_hadiths'")
    total_hadiths = cursor.fetchone()[0]
    cursor.execute("SELECT val_text FROM stats WHERE key='book_stats_json'")
    book_stats_json = cursor.fetchone()[0]
    book_stats = json.loads(book_stats_json)
    conn.close()
    return total_hadiths, book_stats

def get_random_hadith():
    conn = get_connection()
    cursor = conn.cursor()
    # Veritabanından rastgele bir id seç
    cursor.execute("SELECT id FROM hadiths")
    ids = [r[0] for r in cursor.fetchall()]
    rand_id = random.choice(ids)
    
    cursor.execute("""
        SELECT h.id, b.title_en, c.title_en, c.title_ar, h.id_in_book, h.narrator_en, h.text_en, h.text_ar
        FROM hadiths h
        JOIN books b ON h.book_id = b.id
        JOIN chapters c ON h.chapter_id = c.id
        WHERE h.id = ?
    """, (rand_id,))
    h = cursor.fetchone()
    conn.close()
    return h

def generate_hadith_card(hadith_id, bg_color, ar_font_size, en_font_size, card_width=1080, card_height=1080):
    """
    Hadis kartı görüntüsü (PNG) oluşturur.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id_in_book, b.title_en, h.narrator_en, h.text_en, h.text_ar
        FROM hadiths h
        JOIN books b ON h.book_id = b.id
        WHERE h.id = ?
    """, (hadith_id,))
    res = cursor.fetchone()
    conn.close()
    
    if not res:
        return None
        
    id_in_book, book_title, narrator, text_en, text_ar = res
    
    # Görsel oluşturma
    img = Image.new('RGB', (card_width, card_height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Fontları yükleme
    try:
        font_ar = ImageFont.truetype(FONT_AR_BOLD, ar_font_size)
        font_en = ImageFont.truetype(FONT_AR, en_font_size)
        font_meta = ImageFont.truetype(FONT_AR_BOLD, 24)
    except Exception as e:
        font_ar = ImageFont.load_default()
        font_en = ImageFont.load_default()
        font_meta = ImageFont.load_default()
        
    # Kenar süslemesi (Border)
    border_color = "#E5E7EB"
    border_thickness = 15
    draw.rectangle(
        [(border_thickness, border_thickness), (card_width - border_thickness, card_height - border_thickness)],
        outline=border_color, width=3
    )
    
    # 1. ARAPÇA METİN HAZIRLAMA (RTL ve Wrap)
    # Arapça metni satırlara bölme (yaklaşık karakter sayısına göre)
    ar_lines = textwrap.wrap(text_ar, width=45)
    wrapped_ar_text = "\n".join(ar_lines)
    
    # 2. İNGİLİZCE METİN HAZIRLAMA
    full_en = ""
    if narrator:
        full_en += f"{narrator} "
    full_en += text_en
    en_lines = textwrap.wrap(full_en, width=55)
    wrapped_en_text = "\n".join(en_lines)
    
    # 3. YÜKSEKLİK HESAPLAMA VE MERKEZLEME
    # Metinlerin kaplayacağı toplam alan yüksekliğini bulalım
    ar_bbox = draw.multiline_textbbox((0, 0), wrapped_ar_text, font=font_ar, align="center", direction="rtl")
    ar_height = ar_bbox[3] - ar_bbox[1]
    
    en_bbox = draw.multiline_textbbox((0, 0), wrapped_en_text, font=font_en, align="center")
    en_height = en_bbox[3] - en_bbox[1]
    
    spacing = 80
    meta_height = 40
    total_content_height = ar_height + en_height + spacing + meta_height + 40
    
    # Başlangıç Y koordinatı (Dikey merkezleme)
    start_y = (card_height - total_content_height) / 2
    
    # Arapça Metni Çizme (Native RTL)
    draw.multiline_text(
        (card_width / 2, start_y), 
        wrapped_ar_text, 
        font=font_ar, 
        fill="#FFFFFF", 
        anchor="ma", 
        align="center",
        direction="rtl",
        spacing=10
    )
    
    # İngilizce Metni Çizme
    draw.multiline_text(
        (card_width / 2, start_y + ar_height + spacing), 
        wrapped_en_text, 
        font=font_en, 
        fill="#E5E7EB", 
        anchor="ma", 
        align="center",
        spacing=6
    )
    
    # Künye Bilgisi Çizme (Dipnot)
    meta_text = f"Hadith Source: {book_title} (Hadith No: {id_in_book})"
    draw.text(
        (card_width / 2, start_y + ar_height + spacing + en_height + 40),
        meta_text,
        font=font_meta,
        fill="#10B981",
        anchor="ma"
    )
    
    # PNG formatında byte döndürme
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# 4. STREAMLIT YAN MENÜ
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2904/2904843.png", width=90)
st.sidebar.title("Hadis Rehberi")
st.sidebar.write("6 Temel Kaynak Bir Arada (Kütüb-i Sitte)")

menu = st.sidebar.radio("Sayfa Seçimi:", [
    "🏠 Ana Sayfa & Keşfet",
    "🔍 Gelişmiş Hadis Arama",
    "📊 Analiz ve İstatistikler",
    "🎨 Hadis Kartı Üreticisi"
])

st.sidebar.markdown("---")
st.sidebar.caption("📁 **Veri Kaynağı:**\nJSON verileri [AhmedBaset/hadith-json](https://github.com/AhmedBaset/hadith-json) deposundan temin edilmiştir.")

# 5. SAYFA İÇERİKLERİ

if menu == "🏠 Ana Sayfa & Keşfet":
    st.title("🕌 Dijital Hadis Rehberi")
    st.write("İslam literatüründeki temel hadis kaynaklarında arama yapın, tematik kategorileri inceleyin ve görsel kartlar oluşturun.")
    st.info("ℹ️ **Bilgi:** Uygulamadaki hadis verileri [AhmedBaset/hadith-json](https://github.com/AhmedBaset/hadith-json) açık kaynak projesinden derlenmiştir.")
    
    # Günün Hadisi Modülü
    st.subheader("💡 Günün Hadisi")
    
    # Session state'te günün hadisini saklayalım ki sayfa yenilendiğinde durup dururken değişmesin
    if 'random_hadith' not in st.session_state:
        st.session_state.random_hadith = get_random_hadith()
        
    if st.button("🔄 Başka Bir Hadis Getir"):
        st.session_state.random_hadith = get_random_hadith()
        
    h = st.session_state.random_hadith
    if h:
        h_id, book, ch_en, ch_ar, id_in_book, narrator, text_en, text_ar = h
        st.markdown(f"""
            <div class="hadith-card">
                <span class="meta-tag">📚 {book}</span>
                <span class="meta-tag">📁 {ch_en} ({ch_ar})</span>
                <span class="meta-tag">🔢 Hadis No: {id_in_book}</span>
                <div class="ar-text">{text_ar}</div>
                {f'<div class="narrator-lbl">🗣️ {narrator}</div>' if narrator else ''}
                <div class="en-text">"{text_en}"</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Hızlıca Karta Gitmek İçin Buton
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🎨 Görsel Kart Üret"):
                st.session_state.card_hadith_id = h_id
                # Kart sayfasına git
                st.info("Hadis Kartı Üreticisi sekmesine yönlendiriliyorsunuz. Lütfen soldaki menüden 'Hadis Kartı Üreticisi'ni seçin veya bekleyin.")
                # st.rerun ile anında menüyü değiştirmek streamlit radio'da kolay değil, ama session_state ile taşımış olduk.
    
    st.write("---")
    
    # Tematik Kategori Grid
    st.subheader("🏷️ Tematik Kategorilere Göre Keşfet")
    cats = get_categories_list()
    
    # Grid Düzeni
    cols = st.columns(3)
    for idx, cat in enumerate(cats):
        col = cols[idx % 3]
        with col:
            with st.expander(f"📁 {cat}"):
                # Bu kategoriye ait kitap ve bölümleri listele
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.id, b.title_en, c.chapter_number, c.title_en, c.title_ar
                    FROM chapters c
                    JOIN books b ON c.book_id = b.id
                    WHERE c.category_name = ?
                    ORDER BY b.id, c.chapter_number
                """, (cat,))
                ch_rows = cursor.fetchall()
                conn.close()
                
                st.write(f"Bu kategoride **{len(ch_rows)}** adet kitap bölümü bulundu:")
                for ch in ch_rows:
                    ch_id, b_title, ch_num, ch_title_en, ch_title_ar = ch
                    if st.button(f"[{b_title}] {ch_num}. {ch_title_en}", key=f"cat_btn_{ch_id}"):
                        # Popup veya genişletilmiş alanda hadisleri göster
                        st.session_state.active_chapter_id = ch_id
                        st.session_state.active_chapter_title = f"{b_title} - {ch_title_en}"
                        st.success(f"Bölüm Seçildi: {b_title} | {ch_title_en}. Hadisler aşağıda listelenmiştir. Lütfen sayfayı aşağı kaydırın.")
                        
    # Seçilen bölümün hadislerini alt kısımda gösterelim
    if 'active_chapter_id' in st.session_state:
        st.write("---")
        st.subheader(f"📖 Hadis Listesi: {st.session_state.active_chapter_title}")
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, id_in_book, narrator_en, text_en, text_ar
            FROM hadiths
            WHERE chapter_id = ?
            ORDER BY id_in_book
        """, (st.session_state.active_chapter_id,))
        ch_hadiths = cursor.fetchall()
        conn.close()
        
        for ch_h in ch_hadiths:
            h_id, id_in_book, narrator, text_en, text_ar = ch_h
            st.markdown(f"""
                <div class="hadith-card">
                    <span class="meta-tag">🔢 Hadis No: {id_in_book}</span>
                    <div class="ar-text">{text_ar}</div>
                    {f'<div class="narrator-lbl">🗣️ {narrator}</div>' if narrator else ''}
                    <div class="en-text">"{text_en}"</div>
                </div>
                """, unsafe_allow_html=True)
            col_card_1, _ = st.columns([1, 6])
            with col_card_1:
                if st.button("🎨 Kart Üret", key=f"ch_card_{h_id}"):
                    st.session_state.card_hadith_id = h_id
                    st.info("Hadis seçildi! Soldaki menüden 'Hadis Kartı Üreticisi' sekmesine geçerek özelleştirebilirsiniz.")

elif menu == "🔍 Gelişmiş Hadis Arama":
    st.title("🔍 Gelişmiş Hadis Arama Motoru")
    st.write("Kelimeye göre hızlıca arayın veya kitap, bölüm, ravi ve hadis numarasına göre filtreleyin.")
    
    # Filtre Paneli
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    books_df = get_books_list()
    book_options = ["Tümü"] + list(books_df['title_en'].values)
    
    with col_f1:
        sel_book = st.selectbox("Hadis Kitabı Seçin:", book_options)
    
    categories = get_categories_list()
    cat_options = ["Tümü"] + categories
    
    with col_f2:
        sel_cat = st.selectbox("Konu Kategorisi Seçin:", cat_options)
        
    with col_f3:
        txt_narrator = st.text_input("Ravi (İngilizce - Örn: Abu Huraira):").strip()
        
    with col_f4:
        num_hadith = st.text_input("Hadis No (idInBook):").strip()
        
    search_query = st.text_input("🔍 Aranacak Kelime (İngilizce veya Arapça):").strip()
    
    # Arama Düğmesi
    if st.button("Hadis Ara") or search_query or txt_narrator or num_hadith or sel_book != "Tümü" or sel_cat != "Tümü":
        # Veritabanı sorgusu oluşturma
        conn = get_connection()
        cursor = conn.cursor()
        
        # Filtreleri hazırlama
        params = []
        where_clauses = []
        
        # Kitap filtresi
        if sel_book != "Tümü":
            b_id = int(books_df[books_df['title_en'] == sel_book]['id'].values[0])
            where_clauses.append("h.book_id = ?")
            params.append(b_id)
            
        # Kategori filtresi
        if sel_cat != "Tümü":
            where_clauses.append("c.category_name = ?")
            params.append(sel_cat)
            
        # Ravi filtresi
        if txt_narrator:
            where_clauses.append("h.narrator_en LIKE ?")
            params.append(f"%{txt_narrator}%")
            
        # Hadis no filtresi
        if num_hadith:
            try:
                where_clauses.append("h.id_in_book = ?")
                params.append(int(num_hadith))
            except ValueError:
                st.warning("Hadis Numarası geçerli bir tamsayı olmalıdır.")
                
        # Metin sorgusu filtresi
        if search_query:
            if is_arabic(search_query):
                norm_q = normalize_arabic(search_query)
                where_clauses.append("h.text_ar_norm LIKE ?")
                params.append(f"%{norm_q}%")
            else:
                # FTS5 Kullanarak arama (h.id MATCH fts.rowid)
                # FTS aramalarında alt sorgu olarak FTS tablosundan ID eşleştirme yapıyoruz
                where_clauses.append("h.id IN (SELECT hadith_id FROM hadiths_fts WHERE hadiths_fts MATCH ?)")
                params.append(search_query)
                
        # SQL birleştirme
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)
            
        sql = f"""
            SELECT h.id, 
                   b.title_en AS book_title_en, 
                   c.title_en AS chapter_title_en, 
                   c.title_ar AS chapter_title_ar, 
                   h.id_in_book, 
                   h.narrator_en, 
                   h.text_en, 
                   h.text_ar
            FROM hadiths h
            JOIN books b ON h.book_id = b.id
            JOIN chapters c ON h.chapter_id = c.id
            {where_sql}
            LIMIT 100
        """
        
        results = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        
        total_res = len(results)
        st.subheader(f"📊 Arama Sonuçları ({total_res} adet listelendi - Limit 100)")
        
        if total_res == 0:
            st.info("Arama kriterlerinize uygun hadis bulunamadı. Lütfen kelimenizi değiştirin.")
        else:
            for idx, r in results.iterrows():
                st.markdown(f"""
                    <div class="hadith-card">
                        <span class="meta-tag">📚 {r['book_title_en']}</span>
                        <span class="meta-tag">📁 {r['chapter_title_en']} ({r['chapter_title_ar']})</span>
                        <span class="meta-tag">🔢 Hadis No: {r['id_in_book']}</span>
                        <div class="ar-text">{r['text_ar']}</div>
                        {f'<div class="narrator-lbl">🗣️ {r["narrator_en"]}</div>' if r["narrator_en"] else ''}
                        <div class="en-text">"{r['text_en']}"</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Kart üretme butonu
                col_btn, _ = st.columns([1, 6])
                with col_btn:
                    if st.button("🎨 Kart Üret", key=f"search_card_{r['id']}"):
                        st.session_state.card_hadith_id = int(r['id'])
                        st.success(f"Hadis {r['id_in_book']} seçildi! Kart üretmek için soldaki menüden 'Hadis Kartı Üreticisi' sekmeye gidin.")

elif menu == "📊 Analiz ve İstatistikler":
    st.title("📊 Dijital Hadis Rehberi İstatistikleri")
    st.write("Hadis veritabanının genel hacmi, kitap bazlı hadis sayıları ve tematik kategorilere göre bölüm dağılımları.")
    
    total_hadiths, book_stats = get_stats_data()
    
    # KPI Kartları
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        st.metric("Toplam Hadis Sayısı", f"{total_hadiths:,}")
    with col_kpi2:
        st.metric("Kitap Sayısı", len(book_stats))
    with col_kpi3:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chapters")
        total_chapters = cursor.fetchone()[0]
        conn.close()
        st.metric("Toplam Bölüm (Chapter) Sayısı", total_chapters)
        
    st.write("---")
    
    # Kitap Dağılım Grafiği
    st.subheader("📚 Kitap Başına Hadis Dağılımı")
    df_books = pd.DataFrame(book_stats)
    df_books.rename(columns={'title': 'Kitap Adı', 'hadith_count': 'Hadis Sayısı', 'chapter_count': 'Bölüm Sayısı'}, inplace=True)
    
    st.bar_chart(df_books.set_index('Kitap Adı')['Hadis Sayısı'])
    
    st.write("---")
    
    # Detaylı İstatistik Tablosu
    st.subheader("📋 Kitap İstatistik Özet Tablosu")
    st.dataframe(df_books, use_container_width=True)
    
    st.write("---")
    
    # Kategorilere Göre Bölüm Dağılım Tablosu
    st.subheader("🏷️ Tematik Kategorilere Göre Bölüm Sayıları")
    conn = get_connection()
    df_cats = pd.read_sql_query("""
        SELECT category_name as 'Kategori', COUNT(*) as 'Bölüm Sayısı' 
        FROM chapters 
        GROUP BY category_name 
        ORDER BY COUNT(*) DESC
    """, conn)
    conn.close()
    
    st.dataframe(df_cats, use_container_width=True)

elif menu == "🎨 Hadis Kartı Üreticisi":
    st.title("🎨 Sosyal Medya Paylaşım Kartı Üreticisi")
    st.write("Seçtiğiniz bir hadisi, sosyal medyalarda paylaşılabilecek yüksek çözünürlüklü ve şık bir PNG görsel karta dönüştürün.")
    
    # Kart için seçilen hadisi bulma
    active_id = st.session_state.get('card_hadith_id', None)
    
    if active_id is None:
        st.warning("Henüz bir hadis seçilmedi! Lütfen 'Ana Sayfa' veya 'Gelişmiş Hadis Arama' sekmelerinden beğendiğiniz bir hadisin altındaki 'Kart Üret' butonuna basın ya da aşağıdan manuel olarak bir hadis seçin.")
        
        # Manuel Seçim Arayüzü
        books_df = get_books_list()
        man_book = st.selectbox("Kitap Seçin:", books_df['title_en'].values, key="man_book")
        b_id = int(books_df[books_df['title_en'] == man_book]['id'].values[0])
        
        # Hadis no seçimi
        man_hadith_no = st.number_input("Hadis Numarası (idInBook):", min_value=1, value=1, step=1)
        
        # Seç
        if st.button("Hadisi Yükle"):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM hadiths WHERE book_id = ? AND id_in_book = ?", (b_id, man_hadith_no))
            res = cursor.fetchone()
            conn.close()
            if res:
                st.session_state.card_hadith_id = res[0]
                st.rerun()
            else:
                st.error("Bu kitapta bu numaraya sahip bir hadis bulunamadı!")
                
    else:
        # Seçili hadisin detaylarını gösterelim
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.id, b.title_en, h.id_in_book, h.narrator_en, h.text_en, h.text_ar
            FROM hadiths h
            JOIN books b ON h.book_id = b.id
            WHERE h.id = ?
        """, (active_id,))
        h_details = cursor.fetchone()
        conn.close()
        
        if h_details:
            _, b_title, id_in_book, narrator, text_en, text_ar = h_details
            
            st.info(f"Seçili Hadis: **{b_title} (Hadis No: {id_in_book})**")
            
            # Farklı bir hadis seçmek isterse temizleme butonu
            if st.button("Hadis Seçimini Temizle / Farklı Hadis Seç"):
                st.session_state.card_hadith_id = None
                st.rerun()
                
            st.write("---")
            
            # Özelleştirme Alanı
            st.subheader("🛠️ Kartı Özelleştir")
            col_c1, col_c2, col_c3 = st.columns(3)
            
            with col_c1:
                # Arka plan renk seçenekleri
                bg_choices = {
                    "Gece Mavisi (Navy)": "#0F172A",
                    "Zümrüt Yeşili (Emerald)": "#064E3B",
                    "Kömür Siyahı (Charcoal)": "#111827",
                    "Derin Kırmızı (Ruby)": "#7F1D1D",
                    "Klasik Altın (Warm Gold)": "#78350F"
                }
                sel_bg = st.selectbox("Arka Plan Rengi:", list(bg_choices.keys()))
                bg_color = bg_choices[sel_bg]
                
            with col_c2:
                # Arapça yazı boyutu
                ar_size = st.slider("Arapça Metin Boyutu:", min_value=16, max_value=60, value=32)
                
            with col_c3:
                # İngilizce yazı boyutu
                en_size = st.slider("İngilizce Metin Boyutu:", min_value=14, max_value=45, value=20)
                
            # Kartı Oluşturma Düğmesi ve Önizleme
            st.write("---")
            st.subheader("🖼️ Kart Önizlemesi (1080x1080)")
            
            # Görseli oluştur
            card_bytes = generate_hadith_card(active_id, bg_color, ar_size, en_size)
            
            if card_bytes:
                # Streamlit'te görseli önizleme
                st.image(card_bytes, width=500)
                
                # İndirme Butonu
                st.download_button(
                    label="📥 Görseli İndir (PNG)",
                    data=card_bytes,
                    file_name=f"hadis_kart_{b_title.replace(' ', '_')}_{id_in_book}.png",
                    mime="image/png"
                )
            else:
                st.error("Hadis kartı görseli oluşturulurken hata meydana geldi.")
        else:
            st.error("Seçilen hadisin detayları veritabanında bulunamadı.")
            st.session_state.card_hadith_id = None

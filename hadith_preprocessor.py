# -*- coding: utf-8 -*-
"""
Hadis Veri Ön İşleme ve SQLite Veritabanı Oluşturma Betiği
"""

import os
import json
import sqlite3
import re

# Sabitler
JSON_FILES = {
    1: 'bukhari.json',
    2: 'muslim.json',
    3: 'nasai.json',
    4: 'abudawud.json',
    5: 'tirmidhi.json',
    6: 'ibnmajah.json'
}
DB_NAME = 'hadiths.db'

# Tematik Sınıflandırma Sözlüğü
CATEGORIES = {
    'Faith & Creed (İman ve Akide)': [
        'belief', 'faith', 'creed', 'iman', 'oneness', 'monotheism', 'tawheed', 'qadar', 'divine will', 
        'إiman', 'إيمان', 'توحيد', 'القدر'
    ],
    'Revelation & Knowledge (Vahiy ve İlim)': [
        'revelation', 'knowledge', 'ilm', 'wahy', 'qur\'an', 'book', 'accepting information', 'truthful person',
        'وحى', 'علم', 'قرآن', 'أخبار الآحاد'
    ],
    'Purification (Taharah / Temizlik)': [
        'purification', 'taharah', 'ablution', 'wudu', 'ghusl', 'bathing', 'tayammum', 'menstru', 'taharat', 
        'طهارة', 'وضوء', 'غسل', 'تيمم', 'حيض'
    ],
    'Prayer & Mosque (Salat / Namaz)': [
        'prayer', 'salat', 'adhan', 'adhaan', 'call to', 'mosque', 'masjid', 'friday', 'witr', 'istisqa', 
        'eclipse', 'prostration', 'tahajjud', 'funeral', 'janaza', 'eid', 'festivals', 'fear prayer', 'shortening', 
        'صلاة', 'أذان', 'جمعة', 'خوف', 'كسوف', 'سجود', 'تهجد', 'جنائز', 'عيد', 'وتر'
    ],
    'Zakat & Charity (Zekat ve Sadaka)': [
        'zakat', 'charity', 'sadaqah', 'tithe', 'tax', 'alms', 
        'زكاة', 'صدقة', 'صدقات'
    ],
    'Sawm (Oruç)': [
        'fasting', 'siyam', 'sawm', 'ramadan', 'taraweeh', 'i\'tikaf', 'night of qadr', 
        'صوم', 'صيام', 'رمضان', 'اعتكاف', 'تراويح'
    ],
    'Hajj & Umrah (Hac ve Umre)': [
        'hajj', 'umrah', 'pilgrim', 'makkah', 'rites', 
        'حج', 'عمرة', 'مناسك'
    ],
    'Commercial Law & Transactions (Ticaret ve Muamelat)': [
        'sales', 'trade', 'business', 'hiring', 'borrowing', 'loans', 'partnership', 'mortgage', 'debt', 
        'tijarah', 'buyu', 'commerce', 'shuf\'a', 'kafalah', 'agriculture', 'water', 'lost things', 'luqatah', 
        'representation', 'proxy', 'gifts', 'hibah', 'endowment', 'wasaayaa', 'wills', 'inheritance', 'fara\'id', 
        'faraid', 'shares', 
        'تجارة', 'بيع', 'بيوع', 'شركة', 'رهن', 'قرض', 'حوالة', 'وكالة', 'شفعة', 'كفالة', 'مزارعة', 'مساقاة', 
        'لقطة', 'هبة', 'وصايا', 'وصية', 'فرائض'
    ],
    'Marriage, Family & Social Life (Evlilik ve Sosyal Hayat)': [
        'marriage', 'nikah', 'wedlock', 'divorce', 'talaq', 'supporting', 'suckling', 'breastfeeding', 'slave', 
        'manumission', 'makaatib', 'liberation', 'peacemaking', 'conditions', 'witnesses', 'curses', 'li\'an',
        'nkha', 'sulh', 'shurut', 
        'نكاح', 'طلاق', 'نفقات', 'عتق', 'مكاتب', 'صلح', 'شروط', 'شهادات', 'لعan', 'لعان'
    ],
    'Ethics & Manners (Ahlak, Adab ve Dua)': [
        'good manners', 'ethics', 'character', 'adab', 'invocations', 'duas', 'good behavior', 'virtues', 
        'wishes', 'oaths', 'vows', 'expiation', 'heart tender', 'riqaq', 'asceticism', 'zuhd', 'dreams', 
        'interpretation', 'intercession', 'asking permission', 'greetings', 'poetry', 'istiz\'an',
        'أدب', 'دعوات', 'أيمان', 'نذور', 'أخلاق', 'رقاق', 'تعبير', 'استئذان', 'سلام', 'شعر'
    ],
    'Food, Drink & Clothing (Yiyecek, İçecek ve Giyim)': [
        'food', 'meals', 'drink', 'dress', 'clothing', 'hunting', 'slaughter', 'sacrifice', 'aqiqa', 'utensils', 
        'أطعمة', 'أشربة', 'لباس', 'صيد', 'ذبائح', 'عقيقة'
    ],
    'Medicine & Health (Tıp ve Sağlık)': [
        'medicine', 'health', 'tibb', 'patients', 'disease', 'illness', 'cupping', 'hygiene', 
        'طب', 'مرضى'
    ],
    'Jihad & Campaigns (Cihat ve Gazveler)': [
        'jihaad', 'jihad', 'fighting', 'booty', 'khumus', 'jizyah', 'expeditions', 'maghaazi', 'military', 
        'tribute', 'truce', 
        'جهاد', 'خمس', 'جزية', 'مغازى'
    ],
    'Virtues & Merits (Faziletler ve Kıssalar)': [
        'virtues of', 'merits', 'companions', 'madinah', 'prophets', 'creation', 
        'مناقب', 'فضائل', 'أنبياء', 'خلق'
    ],
    'Law, Government & Rulings (Hukuk, Yönetim ve Hükümler)': [
        'trials', 'afflictions', 'fitnah', 'fitan', 'malahim', 'limits', 'punishments', 'hudood', 'blood money', 
        'diyat', 'apostates', 'coercion', 'tricks', 'judgments', 'decisions', 'government', 'imarah', 'judicial',
        'oppression',
        'حدود', 'ديات', 'ارتداد', 'إكراه', 'حيل', 'أقضية', 'إمارة', 'حكم', 'فتن', 'مظالم'
    ]
}

def normalize_arabic(text):
    """
    Arapça aramalarda tam eşleşme sağlamak için hareke temizleme ve karakter normalleştirme işlemi yapar.
    """
    if not text:
        return ""
    # Harekeleri temizle (Tashkeel)
    text = re.sub(r'[\u064B-\u0652]', '', text)
    # Elifleri normalleştir (أ, إ, آ -> ا)
    text = re.sub(r'[أإآ]', 'ا', text)
    # Noktalı ye / Elif Maksura normalleştir (ى -> ي)
    text = re.sub(r'ى', 'i', text)  # Python re.sub'da bazen karaktere göre y -> i dönüşümü veya ى -> ي
    text = re.sub(r'ى', 'ي', text)
    # Ta Marbuta normalleştir (ة -> ه)
    text = re.sub(r'ة', 'ه', text)
    return text

def determine_category(eng_title, ar_title):
    """
    İngilizce ve Arapça bölüm başlıklarına göre otomatik tematik kategori belirler.
    """
    eng_lower = eng_title.lower() if eng_title else ""
    ar_lower = ar_title.lower() if ar_title else ""
    
    for category, keywords in CATEGORIES.items():
        if any(kw in eng_lower or kw in ar_lower for kw in keywords):
            return category
            
    return 'General & Others (Genel ve Diğer)'

def create_db_schema(conn):
    """
    SQLite veritabanı şemasını oluşturur.
    """
    cursor = conn.cursor()
    
    # Kitaplar tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title_en TEXT NOT NULL,
            title_ar TEXT,
            author_en TEXT,
            author_ar TEXT,
            introduction_en TEXT,
            introduction_ar TEXT,
            length INTEGER
        )
    """)
    
    # Bölümler (Chapters) tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            chapter_number INTEGER,
            title_en TEXT,
            title_ar TEXT,
            category_name TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id),
            UNIQUE(book_id, chapter_number)
        )
    """)
    
    # Hadisler tablosu (Arapça arama desteği için text_ar_norm eklendi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hadiths (
            id INTEGER PRIMARY KEY,
            book_id INTEGER,
            chapter_id INTEGER,
            id_in_book INTEGER,
            narrator_en TEXT,
            text_en TEXT,
            text_ar TEXT,
            text_ar_norm TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (chapter_id) REFERENCES chapters (id)
        )
    """)
    
    # Arama motoru için FTS5 sanal tablosu (Sadece İngilizce aramalar için)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS hadiths_fts USING fts5(
            hadith_id UNINDEXED,
            narrator_en,
            text_en
        )
    """)
    
    # Hızlı okumak için istatistik tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            val_int INTEGER,
            val_text TEXT
        )
    """)
    
    conn.commit()

def process_and_populate():
    """
    JSON dosyalarını okur, temizler ve SQLite veritabanına aktarır.
    """
    if os.path.exists(DB_NAME):
        print(f"Eski veritabanı siliniyor: {DB_NAME}")
        os.remove(DB_NAME)
        
    conn = sqlite3.connect(DB_NAME)
    create_db_schema(conn)
    cursor = conn.cursor()
    
    total_hadith_count = 0
    book_stats = []
    
    for book_id, filename in JSON_FILES.items():
        if not os.path.exists(filename):
            print(f"Uyarı: {filename} dosyası bulunamadı, atlanıyor...")
            continue
            
        print(f"\nİşleniyor: {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        metadata = data.get('metadata', {})
        english_meta = metadata.get('english', {})
        arabic_meta = metadata.get('arabic', {})
        
        # Kitap bilgisi ekleme
        cursor.execute("""
            INSERT OR REPLACE INTO books (id, title_en, title_ar, author_en, author_ar, introduction_en, introduction_ar, length)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            book_id,
            english_meta.get('title', 'Unknown Book'),
            arabic_meta.get('title', ''),
            english_meta.get('author', ''),
            arabic_meta.get('author', ''),
            english_meta.get('introduction', ''),
            arabic_meta.get('introduction', ''),
            metadata.get('length', 0)
        ))
        
        # Bölümleri ekleme
        chapter_map = {} # (book_id, chapter_number) -> chapter_db_id
        for chapter in data.get('chapters', []):
            ch_num = chapter.get('id')
            title_en = chapter.get('english', '')
            title_ar = chapter.get('arabic', '')
            category = determine_category(title_en, title_ar)
            
            cursor.execute("""
                INSERT OR IGNORE INTO chapters (book_id, chapter_number, title_en, title_ar, category_name)
                VALUES (?, ?, ?, ?, ?)
            """, (book_id, ch_num, title_en, title_ar, category))
            
            cursor.execute("SELECT id FROM chapters WHERE book_id = ? AND chapter_number = ?", (book_id, ch_num))
            db_id = cursor.fetchone()[0]
            chapter_map[ch_num] = db_id
            
        # Hadisleri ekleme ve FTS tablosunu besleme
        hadith_list = data.get('hadiths', [])
        hadith_records = []
        fts_records = []
        
        print(f"  {len(hadith_list)} adet hadis okunuyor...")
        
        for h in hadith_list:
            h_id = h.get('id')
            id_in_book = h.get('idInBook')
            ch_num = h.get('chapterId')
            ch_db_id = chapter_map.get(ch_num)
            
            eng_data = h.get('english') or {}
            narrator_en = eng_data.get('narrator', '')
            text_en = eng_data.get('text', '')
            text_ar = h.get('arabic', '')
            
            # None değerleri boş metne dönüştürelim
            if narrator_en is None: narrator_en = ''
            if text_en is None: text_en = ''
            if text_ar is None: text_ar = ''
            
            # Arapça normalleştirilmiş metin
            text_ar_norm = normalize_arabic(text_ar)
            
            hadith_records.append((
                h_id, book_id, ch_db_id, id_in_book, narrator_en, text_en, text_ar, text_ar_norm
            ))
            
            # FTS formatında ekle (Sadece İngilizce sütunlar)
            fts_records.append((
                h_id, narrator_en, text_en
            ))
            
        # Toplu yazma (Bulk Insert) performansı artırır
        cursor.executemany("""
            INSERT OR REPLACE INTO hadiths (id, book_id, chapter_id, id_in_book, narrator_en, text_en, text_ar, text_ar_norm)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, hadith_records)
        
        cursor.executemany("""
            INSERT INTO hadiths_fts (hadith_id, narrator_en, text_en)
            VALUES (?, ?, ?)
        """, fts_records)
        
        book_hadith_count = len(hadith_list)
        total_hadith_count += book_hadith_count
        
        book_stats.append({
            'book_id': book_id,
            'title': english_meta.get('title', 'Unknown'),
            'hadith_count': book_hadith_count,
            'chapter_count': len(data.get('chapters', []))
        })
        print(f"  {english_meta.get('title')} başarıyla tamamlandı. Hadis Sayısı: {book_hadith_count}, Bölüm Sayısı: {len(data.get('chapters', []))}")
        
    # İstatistik özetini SQLite tablosuna yazma
    cursor.execute("INSERT OR REPLACE INTO stats (key, val_int, val_text) VALUES (?, ?, ?)", 
                   ('total_hadiths', total_hadith_count, None))
    cursor.execute("INSERT OR REPLACE INTO stats (key, val_int, val_text) VALUES (?, ?, ?)", 
                   ('book_stats_json', None, json.dumps(book_stats)))
    
    conn.commit()
    conn.close()
    
    print("\nVeritabanı oluşturma işlemi tamamlandı!")
    print(f"Toplam Aktarılan Hadis Sayısı: {total_hadith_count}")
    print(f"Oluşturulan veritabanı: {os.path.abspath(DB_NAME)}")

if __name__ == "__main__":
    process_and_populate()

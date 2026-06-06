# -*- coding: utf-8 -*-
"""
Hadis Veritabanı Doğrulama Testi
"""

import sqlite3
import json
import re

def normalize_arabic(text):
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة', 'ه', text)
    return text

def test_database():
    print("Doğrulama Testleri Başlatılıyor...")
    
    conn = sqlite3.connect("hadiths.db")
    cursor = conn.cursor()
    
    # 1. Tablo Varlık Kontrolü
    tables = ["books", "chapters", "hadiths", "hadiths_fts", "stats"]
    for t in tables:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
        res = cursor.fetchone()
        assert res is not None, f"Hata: {t} tablosu bulunamadı!"
        print(f"  [OK] Tablo mevcut: {t}")
        
    # 2. Toplam Hadis Sayısı Kontrolü
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    hadith_cnt = cursor.fetchone()[0]
    print(f"  [INFO] Hadisler tablosundaki satır sayısı: {hadith_cnt}")
    assert hadith_cnt == 34178, f"Hata: Beklenen hadis sayısı 34178, bulunan {hadith_cnt}!"
    print("  [OK] Toplam hadis sayısı doğru.")
    
    # 3. İstatistik Tablosu Kontrolü
    cursor.execute("SELECT val_int FROM stats WHERE key='total_hadiths'")
    stat_val = cursor.fetchone()[0]
    assert stat_val == 34178, f"Hata: Stats tablosundaki hadis sayısı hatalı: {stat_val}!"
    print("  [OK] Stats tablosundaki toplam hadis sayısı doğru.")
    
    # 4. FTS (Full-Text Search) Arama Kontrolü
    print("  [INFO] FTS araması test ediliyor ('intention' kelimesi)...")
    cursor.execute("""
        SELECT h.id, b.title_en, c.title_en, h.narrator_en, h.text_en
        FROM hadiths h
        JOIN books b ON h.book_id = b.id
        JOIN chapters c ON h.chapter_id = c.id
        JOIN hadiths_fts fts ON h.id = fts.hadith_id
        WHERE hadiths_fts MATCH 'intention'
        LIMIT 5
    """)
    results = cursor.fetchall()
    print(f"  [INFO] 'intention' için {len(results)} sonuç alındı (Limit 5):")
    for r in results:
        print(f"    - [ID: {r[0]}] [{r[1]}] Bölüm: {r[2]} | Ravi: {r[3]}")
    assert len(results) > 0, "Hata: FTS araması hiç sonuç döndürmedi!"
    print("  [OK] FTS arama motoru çalışıyor.")
    
    # 5. Kategori Dağılım Kontrolü
    cursor.execute("""
        SELECT category_name, COUNT(*) 
        FROM chapters 
        GROUP BY category_name 
        ORDER BY COUNT(*) DESC
    """)
    categories = cursor.fetchall()
    print("  [INFO] Kategorilerin bölüm sayılarına göre dağılımı:")
    for cat in categories:
        print(f"    - {cat[0]}: {cat[1]} bölüm")
    
    # 6. Arapça Arama Kontrolü
    print("  [INFO] Arapça araması test ediliyor ('النيات' kelimesi)...")
    query_norm = normalize_arabic("النيات")
    cursor.execute("""
        SELECT id, text_ar
        FROM hadiths
        WHERE text_ar_norm LIKE ?
        LIMIT 5
    """, (f"%{query_norm}%",))
    ar_res = cursor.fetchall()
    print(f"  [INFO] Arapça '{query_norm}' araması için {len(ar_res)} sonuç alındı:")
    for ar in ar_res:
        print(f"    - Hadis ID: {ar[0]} | Metin: {ar[1][:100]}...")
    assert len(ar_res) > 0, "Hata: Arapça arama sonuç vermedi!"
    print(f"  [OK] Arapça arama çalışıyor.")
    
    conn.close()
    print("\nTüm testler başarıyla geçildi! Veritabanı sorunsuz görünüyor.")

if __name__ == "__main__":
    test_database()

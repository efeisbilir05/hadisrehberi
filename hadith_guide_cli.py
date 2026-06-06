# -*- coding: utf-8 -*-
"""
Dijital Hadis Rehberi - Komut Satırı Arayüzü (CLI)
"""

import sqlite3
import re
import json
import sys

DB_NAME = 'hadiths.db'

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

def display_hadith(h):
    """
    Format and print a single Hadith record.
    h structure: (hadith_id, book_title_en, ch_title_en, ch_title_ar, id_in_book, narrator_en, text_en, text_ar)
    """
    h_id, book, ch_en, ch_ar, id_in_book, narrator, text_en, text_ar = h
    print("=" * 60)
    print(f"📖 KİTAP    : {book}")
    print(f"📁 BÖLÜM    : {ch_en} ({ch_ar})")
    print(f"🔢 HADİS NO : {id_in_book} (Global ID: {h_id})")
    print("-" * 60)
    if narrator:
        print(f"🗣️  RAVİ     : {narrator}")
        print("-" * 60)
    print("🟢 ARAPÇA METİN:")
    print(text_ar)
    print("-" * 60)
    print("🔵 İNGİLİZCE ÇEVİRİ:")
    print(text_en)
    print("=" * 60 + "\n")

def search_hadiths():
    query = input("\n🔍 Arama kelimesi girin (Arapça veya İngilizce): ").strip()
    if not query:
        print("❌ Arama kelimesi boş olamaz.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    if is_arabic(query):
        norm_query = normalize_arabic(query)
        print(f"⏳ Arapça metin aranıyor (Normalleştirilmiş: {norm_query})...")
        cursor.execute("""
            SELECT h.id, b.title_en, c.title_en, c.title_ar, h.id_in_book, h.narrator_en, h.text_en, h.text_ar
            FROM hadiths h
            JOIN books b ON h.book_id = b.id
            JOIN chapters c ON h.chapter_id = c.id
            WHERE h.text_ar_norm LIKE ?
        """, (f"%{norm_query}%",))
    else:
        print(f"⏳ İngilizce metin aranıyor: '{query}'...")
        # FTS5 matches tokens
        cursor.execute("""
            SELECT h.id, b.title_en, c.title_en, c.title_ar, h.id_in_book, h.narrator_en, h.text_en, h.text_ar
            FROM hadiths h
            JOIN books b ON h.book_id = b.id
            JOIN chapters c ON h.chapter_id = c.id
            JOIN hadiths_fts fts ON h.id = fts.hadith_id
            WHERE hadiths_fts MATCH ?
        """, (query,))

    results = cursor.fetchall()
    conn.close()

    total_results = len(results)
    if total_results == 0:
        print("ℹ️ Hiçbir sonuç bulunamadı.")
        return

    print(f"🎉 {total_results} adet eşleşme bulundu!\n")
    
    limit = 5
    for i, h in enumerate(results[:limit]):
        print(f"--- Sonuç {i+1} / {total_results} ---")
        display_hadith(h)

    if total_results > limit:
        more = input(f"👉 Diğer {total_results - limit} sonucu görmek istiyor musunuz? (e/h): ").strip().lower()
        if more == 'e':
            for i, h in enumerate(results[limit:]):
                print(f"--- Sonuç {limit+i+1} / {total_results} ---")
                display_hadith(h)

def browse_by_book():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title_en, title_ar FROM books ORDER BY id")
    books = cursor.fetchall()

    print("\n📚 HADİS KİTAPLARI:")
    for idx, b in enumerate(books):
        print(f"  {idx + 1}. {b[1]} ({b[2]})")

    try:
        choice = int(input("\nBir kitap seçin (Sayı): ")) - 1
        if choice < 0 or choice >= len(books):
            print("❌ Geçersiz seçim.")
            conn.close()
            return
    except ValueError:
        print("❌ Lütfen geçerli bir sayı girin.")
        conn.close()
        return

    book_id = books[choice][0]
    book_title = books[choice][1]

    cursor.execute("SELECT id, chapter_number, title_en, title_ar, category_name FROM chapters WHERE book_id = ? ORDER BY chapter_number", (book_id,))
    chapters = cursor.fetchall()

    print(f"\n📁 {book_title} BÖLÜMLERİ:")
    for c in chapters:
        print(f"  Bölüm {c[1]}: {c[2]} ({c[3]}) [{c[4]}]")

    try:
        ch_num = int(input("\nGitmek istediğiniz bölüm numarasını girin: "))
    except ValueError:
        print("❌ Geçersiz bölüm numarası.")
        conn.close()
        return

    cursor.execute("""
        SELECT h.id, b.title_en, c.title_en, c.title_ar, h.id_in_book, h.narrator_en, h.text_en, h.text_ar
        FROM hadiths h
        JOIN books b ON h.book_id = b.id
        JOIN chapters c ON h.chapter_id = c.id
        WHERE h.book_id = ? AND c.chapter_number = ?
        ORDER BY h.id_in_book
    """, (book_id, ch_num))
    
    hadiths = cursor.fetchall()
    conn.close()

    if not hadiths:
        print("ℹ️ Bu bölümde hadis bulunamadı veya geçersiz bölüm numarası.")
        return

    print(f"\n🎉 Bu bölümde {len(hadiths)} hadis bulundu!\n")
    for h in hadiths:
        display_hadith(h)

def browse_by_category():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT category_name FROM chapters ORDER BY category_name")
    categories = [row[0] for row in cursor.fetchall()]

    print("\n🏷️  TEMATİK KATEGORİLER:")
    for idx, cat in enumerate(categories):
        print(f"  {idx + 1}. {cat}")

    try:
        choice = int(input("\nBir kategori seçin (Sayı): ")) - 1
        if choice < 0 or choice >= len(categories):
            print("❌ Geçersiz seçim.")
            conn.close()
            return
    except ValueError:
        print("❌ Lütfen geçerli bir sayı girin.")
        conn.close()
        return

    cat_name = categories[choice]

    cursor.execute("""
        SELECT c.id, b.title_en, c.chapter_number, c.title_en, c.title_ar
        FROM chapters c
        JOIN books b ON c.book_id = b.id
        WHERE c.category_name = ?
        ORDER BY b.id, c.chapter_number
    """, (cat_name,))
    chapters = cursor.fetchall()

    print(f"\n📂 '{cat_name}' Kategorisine Ait Bölümler:")
    for idx, c in enumerate(chapters):
        print(f"  {idx + 1}. [{c[1]}] Bölüm {c[2]}: {c[3]} ({c[4]})")

    try:
        ch_choice = int(input("\nHangi bölümdeki hadisleri okumak istersiniz? (Sayı): ")) - 1
        if ch_choice < 0 or ch_choice >= len(chapters):
            print("❌ Geçersiz seçim.")
            conn.close()
            return
    except ValueError:
        print("❌ Lütfen geçerli bir sayı girin.")
        conn.close()
        return

    ch_id = chapters[ch_choice][0]

    cursor.execute("""
        SELECT h.id, b.title_en, c.title_en, c.title_ar, h.id_in_book, h.narrator_en, h.text_en, h.text_ar
        FROM hadiths h
        JOIN books b ON h.book_id = b.id
        JOIN chapters c ON h.chapter_id = c.id
        WHERE h.chapter_id = ?
        ORDER BY h.id_in_book
    """, (ch_id,))
    
    hadiths = cursor.fetchall()
    conn.close()

    print(f"\n🎉 Seçilen bölümde {len(hadiths)} hadis bulundu!\n")
    for h in hadiths:
        display_hadith(h)

def show_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT val_int FROM stats WHERE key='total_hadiths'")
    total_hadiths = cursor.fetchone()[0]

    cursor.execute("SELECT val_text FROM stats WHERE key='book_stats_json'")
    book_stats_json = cursor.fetchone()[0]
    book_stats = json.loads(book_stats_json)

    print("\n📊 DİJİTAL HADİS REHBERİ İSTATİSTİKLERİ:")
    print("=" * 50)
    print(f"📚 Toplam Hadis Sayısı   : {total_hadiths}")
    print(f"📖 Toplam Kitap Sayısı   : {len(book_stats)}")
    print("-" * 50)
    print(f"{'Hadis Kitabı':<25} | {'Hadis Sayısı':<12} | {'Bölüm Sayısı':<12}")
    print("-" * 50)
    for b in book_stats:
        print(f"{b['title']:<25} | {b['hadith_count']:<12} | {b['chapter_count']:<12}")
    print("=" * 50 + "\n")

    # Kategori dağılımını göster
    cursor.execute("""
        SELECT category_name, COUNT(*) 
        FROM chapters 
        GROUP BY category_name 
        ORDER BY COUNT(*) DESC
    """)
    categories = cursor.fetchall()
    print("🏷️ KATEGORİLERE GÖRE BÖLÜM DAĞILIMI:")
    for cat in categories:
        print(f"  - {cat[0]:<50} : {cat[1]} bölüm")
    print()
    conn.close()

def main_menu():
    print("""
===================================================
🌟 DİJİTAL HADİS REHBERİ (DIGITAL HADITH GUIDE) 🌟
===================================================
Kütüb-i Sitte (6 Temel Hadis Kaynağı) İçerir.
Veri Kaynağı: https://github.com/AhmedBaset/hadith-json
===================================================
    """)
    while True:
        print("1. 🔍 Hadis Arama (İngilizce / Arapça)")
        print("2. 📚 Kitap ve Bölümlere Göre Keşfet")
        print("3. 🏷️  Tematik Kategorilere Göre Keşfet")
        print("4. 📊 Genel İstatistikler")
        print("5. ❌ Çıkış")
        
        choice = input("\nLütfen bir seçenek girin (1-5): ").strip()
        
        if choice == '1':
            search_hadiths()
        elif choice == '2':
            browse_by_book()
        elif choice == '3':
            browse_by_category()
        elif choice == '4':
            show_statistics()
        elif choice == '5':
            print("\nRehberden çıkılıyor. Hayırlı günler! 👋")
            sys.exit(0)
        else:
            print("\n❌ Geçersiz seçenek, lütfen tekrar deneyin.\n")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Rehberden çıkılıyor. Hayırlı günler!")
        sys.exit(0)

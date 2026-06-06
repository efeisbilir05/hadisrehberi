# 🕌 Dijital Hadis Rehberi (Digital Hadith Guide)

Bu proje, İslam literatüründeki temel 6 hadis kaynağını (Kütüb-i Sitte: Buhari, Müslim, Nesai, Ebu Davud, Tirmizi ve İbn Mace) tek bir yüksek performanslı SQLite veritabanında birleştirir. Hem komut satırı arayüzü (CLI) hem de gelişmiş bir Streamlit web arayüzü sunar.

JSON formatındaki hadis verileri [AhmedBaset/hadith-json](https://github.com/AhmedBaset/hadith-json) deposundan temin edilmiştir.

---

## 🏗️ Architecture & Implementation Details

The project consists of three main modules:
1. **Data Ingestion & Normalization (`hadith_preprocessor.py`)**
2. **Interactive Command-Line Interface (`hadith_guide_cli.py`)**
3. **Streamlit Web Interface (`hadith_rehber_web.py`)**

### 1. SQLite Database Schema
The database (`hadiths.db`) is fully optimized with structural tables, foreign keys, and indexes:
- `books`: Stores title (English/Arabic), translator, and metadata.
- `chapters`: Stores chapter numbers, titles, and automated thematic category mapping.
- `hadiths`: Stores narrator, Arabic text, English translation, and a pre-compiled `text_ar_norm` (normalized Arabic text without diacritics/tashkeel to allow diacritic-insensitive substring searching).
- `hadiths_fts` (Virtual Table): SQLite FTS5 index mapping to `hadiths(id)` for high-speed full-text English queries.
- `stats`: Key-value table storing global metrics (total hadiths, book distribution metadata).

### 2. Thematic Classification Engine
An automated keyword-based rule engine maps all chapters across **15 distinct Islamic topics** (e.g., *Purification*, *Salat*, *Zakat*, *Transactions*, *Ethics & Manners*), allowing uniform browsing across different collections.

### 3. Arabic Normalization
To prevent searching issues due to diacritic variation (such as Fatha, Damma, Kasra, Shadda, etc.), the preprocessor strips tashkeel and normalizes different forms of Alef, Teh Marbuta, and Yeh. Search queries are normalized using the same logic and matched using SQLite's `LIKE` query on `text_ar_norm`.

---

## 💻 CLI Interface (`hadith_guide_cli.py`)
Provides a fast, terminal-based utility to search and explore the Hadith collections:
- **Search**: Auto-detects English or Arabic queries and selects FTS5 or normalized substring matching respectively.
- **Browse**: Allows selecting a book and chapter to page through its contents.
- **Thematic Exploration**: Browse hadiths by selecting one of the 15 categories.
- **Statistics**: Shows global database counts and collection breakdowns in ASCII tables.

---

## 🌐 Streamlit Web Dashboard (`hadith_rehber_web.py`)
A premium, responsive, dark-themed Streamlit dashboard providing search, analytics, and sharing features:
- **Ana Sayfa & Keşfet**: Presents a "Hadith of the Day" with a refresh button and a category-based expander grid for visual navigation.
- **Gelişmiş Hadis Arama**: Multi-filter search interface allowing users to filter by Book, Category, Narrator, Hadith Number, and bilingual queries. Resolves duplicate naming issues using explicit SQL column aliases.
- **Analiz ve İstatistikler**: Visualizes database volumes with bar charts and detailed summaries.
- **Hadis Kartı Üreticisi (Social Card Generator)**:
  - Generates sharing-ready 1080x1080 square PNG cards.
  - Automatically handles Arabic line-wrapping and connected RTL rendering using Pillow's native `direction="rtl"` (HarfBuzz) engine with the custom-loaded **Amiri** Google Font.
  - Allows selecting from different premium backgrounds (Navy, Emerald, Charcoal, Ruby, Warm Gold) and adjusting font sizes interactively.

---

## ✅ Verification & Testing

### 1. Database Integrity Test (`hadith_test.py`)
Running `python hadith_test.py` validates database schema consistency, total hadith counts, FTS performance, and Arabic normalization accuracy. All tests pass successfully:
- Total Hadiths: **34,178**
- English search query test ('intention'): **Passed**
- Arabic normalized search test ('النيات'): **Passed**
- Six books verification: **Passed**


### 2. CLI Execution Verification
Testing with simulated terminal pipes:
```bash
echo -e "4\n5" | ./hadith_venv/bin/python hadith_guide_cli.py
```
This output correctly fetches and prints book distributions and category chapter counts, then exits cleanly.

### 3. Card Generator Preview
Below is a screenshot of the generated social card preview within the Streamlit dashboard:

![Hadith Card Generator Preview](/home/Efe/.gemini/antigravity/brain/9d652097-8559-44ab-9eb1-87c64089ddf0/.system_generated/click_feedback/click_feedback_1780741530912.png)

> [!TIP]
> Native RTL rendering via Pillow's `direction="rtl"` uses HarfBuzz under the hood, ensuring that glyph connections and diacritics are drawn perfectly without manual string reversal hacks.

---

## 🚀 Kurulum ve Çalıştırma (Installation & Running)

### 1. Sanal Ortam Oluşturma ve Bağımlılıkları Yükleme (Virtual Environment Setup)
Proje dizininde bir sanal ortam oluşturup gerekli kütüphaneleri yükleyin:
```bash
# Sanal ortam oluşturma
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükleme
pip install -r requirements.txt
```

### 2. Veritabanını Oluşturma (Database Generation)
Altı adet hadis kitabını (`.json` dosyalarını) SQLite veritabanına aktarmak için preprocessor betiğini çalıştırın:
```bash
python hadith_preprocessor.py
```
Bu işlem otomatik olarak `hadiths.db` veritabanını oluşturacaktır.

### 3. CLI Uygulamasını Çalıştırma (Running CLI)
Terminal üzerinden hadis aramak ve keşfetmek için:
```bash
python hadith_guide_cli.py
```

### 4. Streamlit Arayüzünü Çalıştırma (Running Web App)
Gelişmiş web kontrol panelini ve Hadis Kartı Üreticisi'ni başlatmak için:
```bash
streamlit run hadith_rehber_web.py
```


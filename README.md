# 🌿 Agriculture NLP Information Retrieval System & GUI

A modular, web-based Natural Language Processing (NLP) and Information Retrieval (IR) workspace built for agricultural research documents.

---

## 🌟 Key Features

- **📁 Multi-Format Document Upload & Parsing**: Supports **PDF (`.pdf`)**, **Word (`.docx`)**, **CSV (`.csv`)**, **JSON (`.json`)**, **JSONL (`.jsonl`)**, and **Text (`.txt`)**.
- **📊 Document Statistics & Assignment Matrix**: Live assigned document matrix with real-time search filtering, format badges, and text preview drawers.
- **🔤 Tokenization Comparison**: Compare **NLTK**, **spaCy**, **Custom rules**, and **Hybrid** tokenizers.
- **⚙️ Preprocessing Pipeline**: Stop-word removal, Porter / Snowball / Lancaster stemmers, and NLTK / spaCy lemmatization.
- **🏷️ Linguistics & Domain POS**: Standard POS tagging and custom agricultural domain-specific part-of-speech rules.
- **🏷️ Named Entity Recognition (NER)**: Extract agricultural entities, dates, locations, organizations, and monetary values.
- **🔤 Byte Pair Encoding (BPE)**: Subword tokenization and vocabulary splits.
- **📊 N-Gram Analysis**: Frequency distributions for 1-Grams through 5-Grams.
- **🔍 Inverted Index Explorer**: Vocabulary term lookup, document frequency (`df`), collection frequency (`cf`), and postings lists.
- **🔎 Agricultural Retrieval Engine**: Keyword search, Phrase search, and Boolean logic (AND / OR / NOT) with execution timing and document snippets.
- **📈 Pipeline Comparison & Evaluation**: Compare Pipeline A, B, and C with MAP, Precision@K, Recall@K, and F1 metrics.

---

## 🚀 Quick Start for Teammates

### 1. Clone & Install Dependencies

```bash
# Clone the repository
git clone <YOUR_GIT_REPO_URL>
cd student-result-management

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# OR
.\.venv\Scripts\activate          # Windows PowerShell

# Install required Python packages
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
python backend/app.py
```

The server will start at: **http://127.0.0.1:5000**

### 3. Open the Web GUI

Open your browser and navigate to:
```
http://127.0.0.1:5000
```
Or double-click `frontend/index.html`.

---

## 📂 Project Structure

```
.
├── backend/
│   ├── app.py                # Flask REST API & static server
│   ├── nlp_engine.py         # NLP algorithms, tokenization, index & retrieval engine
│   └── saved_model/          # Pre-compiled corpus state & pipeline model
├── frontend/
│   ├── index.html            # Multi-page dashboard HTML template
│   ├── style.css             # Modern stylesheet & visual UI components
│   └── script.js             # SPA Router, API client, and visual renderers
├── data/
│   └── corpus_documents.jsonl # Default agricultural corpus dataset
├── results/                  # Inverted index JSON data & evaluation outputs
├── requirements.txt          # Project dependencies list
└── README.md                 # Setup & usage documentation
```

---

## 👥 Team Collaboration & Git Sharing

To push this repository to GitHub/GitLab:

```bash
git init
git add .
git commit -m "Initial commit: Agriculture NLP Information Retrieval System & GUI"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

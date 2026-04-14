# 🔍 Lost & Found Reunion
### Multi-Modal Semantic Search Engine — Progress Project 1

---

## 📖 What is this project?

Lost & Found Reunion is an AI-powered search engine that helps students find their lost items on campus. Instead of manually searching through spreadsheets, students can describe what they lost in plain English or upload a photo — and the system finds the closest matches instantly.

> **Example:** Searching *"gold wireless headphones"* correctly finds *"Apple AirPods Max"* even though the words don't match exactly.

---

## ✨ Features

- 📝 **Text Search** — describe your lost item in plain English
- 📸 **Image Search** — upload a photo to find visually similar items
- 🔀 **Combined Search** — use both text and image together
- 🧠 **Semantic Understanding** — "AirPods" matches "wireless earbuds"
- 🤖 **AI Explanations** — Ollama llama3.2 explains each match
- 📊 **Confidence Scores** — every result shows a % match score
- 🗄️ **119 items** indexed in ChromaDB vector database

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core language |
| BeautifulSoup + Requests | Web scraping |
| pandas + Pillow | Data cleaning & image processing |
| Sentence-Transformers | Text embeddings (384 dims) |
| CLIP (OpenAI) | Image embeddings (512 dims) |
| ChromaDB | Persistent vector database |
| Ollama llama3.2 | Local LLM for explanations |
| Streamlit | Web UI |

---

## 📁 Project Structure

```
lost_found_reunion/
│
├── phase1_scrape.py           # Scrape products + generate lost descriptions
├── phase2_clean.py            # Clean and standardise the dataset
├── phase3_embeddings.py       # Create embeddings + store in ChromaDB
├── search_engine.py           # Core search logic (text + image + combined)
├── llm_explain.py             # Ollama AI match explanations
├── app.py                     # Streamlit web app (main entry point)
├── requirements.txt           # All dependencies
│
├── images/                    # Downloaded product images
├── data/                      # CSV files (scraped + cleaned)
├── embeddings/                # Saved embeddings (.pkl)
├── chroma_db/                 # ChromaDB vector database files
└── venv/                      # Python virtual environment
```

---

## ⚙️ Prerequisites

Before running, install these on your machine:

1. **Python 3.11+** — https://python.org
2. **Ollama** — https://ollama.com
3. **Git** — https://git-scm.com

After installing Ollama, pull the model:
```bash
ollama pull llama3.2
```

---

## 🚀 How to Run

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/internship-project1.git
cd internship-project1
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Ollama (in a separate terminal)
```bash
ollama serve
```

### 5. Run the pipeline phases in order
```bash
# Phase 1 — Scrape products and generate lost item descriptions
python phase1_scrape.py

# Phase 2 — Clean and standardise the dataset
python phase2_clean.py

# Phase 3 — Create embeddings and store in ChromaDB
python phase3_embeddings.py
```

### 6. Launch the app
```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

### 7. Share via ngrok
```bash
ngrok http 8501
```
Copy the public URL (e.g. `https://abc123.ngrok-free.app`) and share it.

---

## 🔍 How to Search

1. Type a description of your lost item in the text box
2. Optionally upload a photo of the item
3. Select a category filter if needed
4. Click **Search Lost & Found Database**
5. View results with confidence scores and AI explanations
6. Note the **Item ID** and show it to Lost & Found staff to claim your item

---

## 📊 Pipeline Overview

```
Phase 1: Scrape Products
    ↓ BeautifulSoup + Requests + Ollama
    ↓ 119 products with images + lost descriptions
    ↓ Output: data/scraped_products.csv

Phase 2: Clean Data
    ↓ pandas + Pillow
    ↓ Remove duplicates, verify images, standardise categories
    ↓ Output: data/lost_found_dataset_cleaned.csv

Phase 3: Create Embeddings
    ↓ Sentence-Transformers (text) + CLIP (images)
    ↓ Store in ChromaDB vector database
    ↓ Output: chroma_db/ + embeddings/lost_found_embeddings.pkl

Phase 4: Search + UI
    ↓ ChromaDB cosine similarity search
    ↓ Ollama llama3.2 explanations
    ↓ Streamlit web interface
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `venv\Scripts\activate` first, then `pip install -r requirements.txt` |
| Ollama not working | Run `ollama serve` in a separate terminal |
| `KeyError: color` | Your CSV doesn't have a color column — the code handles this automatically |
| ChromaDB error | Delete the `chroma_db/` folder and re-run `phase3_embeddings.py` |
| Port 8501 in use | Run `streamlit run app.py --server.port 8502` |

---

## 💡 Future Improvements

- Real-time scraping from Amazon / Flipkart
- Student login so they can register lost items themselves
- Email notifications when a match is found
- Mobile app using React Native
- Admin dashboard for Lost & Found staff

---

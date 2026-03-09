# app.py
# Save in: lost_found_reunion/app.py
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
import os
import tempfile

from search_engine import LostAndFoundSearchEngine
from llm_explain   import explain_match

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "Lost & Found Reunion",
    page_icon  = "🔍",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)

# ─────────────────────────────────────────────────────────────
# FORCE LIGHT MODE + FULL CSS OVERHAUL
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Force light background everywhere ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
    background-color: #f4f6fb !important;
    color: #1a1a2e !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
    color: white !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #cccccc !important;
}

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 50%, #e94560 100%);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(26,26,46,0.18);
}
.hero-title {
    font-size: 3rem;
    font-weight: 900;
    color: #ffffff !important;
    letter-spacing: -1px;
    margin-bottom: 0.3rem;
}
.hero-subtitle {
    font-size: 1rem;
    color: #b0c4de !important;
    margin-bottom: 1.2rem;
}
.hero-badges {
    display: flex;
    justify-content: center;
    gap: 0.6rem;
    flex-wrap: wrap;
}
.badge {
    background: rgba(255,255,255,0.15);
    color: white !important;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.2);
}

/* ── Stat cards ── */
.stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-top: 4px solid #e94560;
}
.stat-card.blue  { border-top-color: #0f3460; }
.stat-card.green { border-top-color: #27ae60; }
.stat-card.gold  { border-top-color: #f39c12; }
.stat-num   { font-size: 1.5rem; font-weight: 800; color: #1a1a2e !important; }
.stat-label { font-size: 0.75rem; color: #666 !important;
              text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

/* ── Search panel ── */
.search-panel {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.search-panel-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #1a1a2e !important;
    margin-bottom: 1rem;
}

/* ── All text inputs & textareas ── */
.stTextArea textarea {
    background: #f8faff !important;
    border: 2px solid #e0e7ff !important;
    border-radius: 10px !important;
    color: #1a1a2e !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: #0f3460 !important;
    box-shadow: 0 0 0 3px rgba(15,52,96,0.1) !important;
}
.stTextArea label {
    color: #1a1a2e !important;
    font-weight: 600 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #f8faff !important;
    border: 2px dashed #c5cae9 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"] * {
    color: #1a1a2e !important;
}

/* ── Search button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e94560, #c0392b) !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    box-shadow: 0 4px 15px rgba(233,69,96,0.4) !important;
    transition: transform 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(233,69,96,0.5) !important;
}

/* ── Result cards ── */
.result-card {
    background: white;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 3px 16px rgba(0,0,0,0.08);
    border-left: 5px solid #27ae60;
}
.result-card.medium { border-left-color: #f39c12; }
.result-card.low    { border-left-color: #e74c3c; }

.result-rank {
    display: inline-block;
    background: #1a1a2e;
    color: white !important;
    width: 32px; height: 32px;
    border-radius: 50%;
    text-align: center;
    line-height: 32px;
    font-weight: 800;
    font-size: 0.9rem;
    margin-right: 0.5rem;
}
.result-name {
    font-size: 1.15rem;
    font-weight: 800;
    color: #1a1a2e !important;
}
.result-meta {
    font-size: 0.85rem;
    color: #666 !important;
    margin-top: 2px;
}

/* ── Confidence badge ── */
.conf-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
}
.conf-high   { background: #d5f5e3; color: #1e8449 !important; }
.conf-medium { background: #fef9e7; color: #d35400 !important; }
.conf-low    { background: #fadbd8; color: #922b21 !important; }

/* ── Progress bar ── */
.prog-wrap {
    background: #eee;
    border-radius: 6px;
    height: 10px;
    margin: 0.5rem 0 1rem;
    overflow: hidden;
}
.prog-fill {
    height: 100%;
    border-radius: 6px;
    transition: width 0.5s;
}
.prog-high   { background: linear-gradient(90deg,#27ae60,#2ecc71); }
.prog-medium { background: linear-gradient(90deg,#e67e22,#f39c12); }
.prog-low    { background: linear-gradient(90deg,#c0392b,#e74c3c); }

/* ── Detail rows inside result ── */
.detail-grid {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 0.4rem 0.8rem;
    margin: 0.8rem 0;
    font-size: 0.9rem;
}
.detail-key {
    font-weight: 700;
    color: #555 !important;
}
.detail-val {
    color: #1a1a2e !important;
}

/* ── Item ID pill ── */
.item-id-pill {
    display: inline-block;
    background: #1a1a2e;
    color: white !important;
    padding: 5px 16px;
    border-radius: 20px;
    font-family: monospace;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 1px;
}

/* ── Lost report box ── */
.lost-box {
    background: #eaf4fb;
    border-left: 4px solid #2980b9;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    font-style: italic;
    font-size: 0.9rem;
    color: #1a5276 !important;
    margin: 0.8rem 0;
}

/* ── AI explanation box ── */
.ai-box {
    background: linear-gradient(135deg, #eaf4fb, #d6eaf8);
    border: 1px solid #aed6f1;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-top: 0.8rem;
    font-size: 0.92rem;
    color: #1a1a2e !important;
}
.ai-box b { color: #0f3460 !important; }

/* ── Claim box ── */
.claim-box {
    background: linear-gradient(135deg, #1a1a2e, #0f3460);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-top: 0.8rem;
    color: white !important;
    font-size: 0.9rem;
}

/* ── Insights panel ── */
.insight-card {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    color: white !important;
}
.insight-card.green {
    background: linear-gradient(135deg, #11998e, #38ef7d);
}
.insight-card.orange {
    background: linear-gradient(135deg, #f7971e, #ffd200);
}
.insight-num   { font-size: 2rem; font-weight: 900; color: white !important; }
.insight-label { font-size: 0.75rem; opacity: 0.9; color: white !important; margin-top: 4px; }

/* ── Section headers ── */
.section-header {
    font-size: 1.3rem;
    font-weight: 800;
    color: #1a1a2e !important;
    margin: 1.5rem 0 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 3px solid #e94560;
    display: inline-block;
}

/* ── Expander fix ── */
[data-testid="stExpander"] {
    background: white !important;
    border-radius: 12px !important;
    border: 1px solid #e0e7ff !important;
    margin-bottom: 0.8rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    background: white !important;
    color: #1a1a2e !important;
    font-weight: 600 !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stExpander"] summary:hover {
    background: #f8faff !important;
}

/* ── Footer ── */
.footer {
    text-align: center;
    color: #999 !important;
    font-size: 0.82rem;
    padding: 1rem 0;
    margin-top: 2rem;
    border-top: 1px solid #e0e0e0;
}

/* ── Selectbox & slider labels ── */
.stSelectbox label, .stSlider label {
    color: #1a1a2e !important;
    font-weight: 600 !important;
}

/* ── Success/warning/error boxes ── */
.stAlert {
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# LOAD ENGINE
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🔄 Loading search engine…")
def load_engine():
    return LostAndFoundSearchEngine()

engine = load_engine()
stats  = engine.stats()


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='color:white;font-weight:800;'>🔍 Lost & Found</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#aaa;font-size:0.85rem;'>BLDEACET Campus</p>",
        unsafe_allow_html=True
    )
    st.divider()

    st.markdown(
        "<p style='color:white;font-weight:700;'>⚙️ Search Settings</p>",
        unsafe_allow_html=True
    )
    top_k = st.slider("Number of results", 1, 10, 5)

    show_ai = st.toggle(
        "🤖 Ollama AI Explanations",
        value=True
    )
    show_lost = st.toggle(
        "📋 Show lost item report",
        value=True
    )

    st.divider()
    st.markdown(
        "<p style='color:white;font-weight:700;'>🗂️ Filter by Category</p>",
        unsafe_allow_html=True
    )
    cat_filter = st.selectbox(
        "Category",
        ["All", "electronics", "bags", "clothing", "stationery",
         "sports & fitness", "personal care", "books", "jewelry",
         "food & grocery", "accessories", "home & decor",
         "footwear", "watches & jewelry"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("""
<p style='color:white;font-weight:700;'>🛠️ Tech Stack</p>
<ul style='color:#ccc;font-size:0.82rem;line-height:2;'>
  <li>BeautifulSoup + Requests</li>
  <li>pandas + Pillow</li>
  <li>Sentence-Transformers</li>
  <li>CLIP (OpenAI)</li>
  <li>ChromaDB</li>
  <li>Ollama llama3.2</li>
  <li>Streamlit</li>
</ul>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("""
<p style='color:white;font-weight:700;'>💡 How to use</p>
<ol style='color:#ccc;font-size:0.82rem;line-height:2;'>
  <li>Describe your lost item</li>
  <li>Upload a photo (optional)</li>
  <li>Click Search</li>
  <li>Show Item ID to staff</li>
</ol>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🔍 Lost &amp; Found Reunion</div>
    <div class="hero-subtitle">
        Multi-Modal Semantic Search Engine · BLDEACET Campus
    </div>
    <div class="hero-badges">
        <span class="badge">📝 Text Search</span>
        <span class="badge">📸 Image Search</span>
        <span class="badge">🧠 Sentence-Transformers</span>
        <span class="badge">🖼️ CLIP Embeddings</span>
        <span class="badge">🗄️ ChromaDB</span>
        <span class="badge">🤖 Ollama llama3.2</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# STATS CARDS
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-num">{stats['total_items']}</div>
        <div class="stat-label">📦 Items in Database</div>
    </div>
    <div class="stat-card blue">
        <div class="stat-num">384</div>
        <div class="stat-label">🧠 Text Embedding Dims</div>
    </div>
    <div class="stat-card green">
        <div class="stat-num">512</div>
        <div class="stat-label">🖼️ Image Embedding Dims</div>
    </div>
    <div class="stat-card gold">
        <div class="stat-num">llama3.2</div>
        <div class="stat-label">🤖 Local LLM Model</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SEARCH FORM
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="section-header">🔎 Search for Your Lost Item</div>',
    unsafe_allow_html=True
)

left_col, right_col = st.columns([3, 2], gap="large")

with left_col:
    query_text = st.text_area(
        "📝 Describe your lost item",
        placeholder=(
            "e.g. I lost my gold wireless headphones with a leather "
            "case near the library on Monday morning..."
        ),
        height=150,
    )

with right_col:
    st.markdown(
        "<p style='font-weight:700;color:#1a1a2e;margin-bottom:0.3rem;'>"
        "📸 Upload a photo of your lost item</p>"
        "<p style='font-size:0.82rem;color:#888;margin-bottom:0.5rem;'>"
        "Optional — helps find visually similar items</p>",
        unsafe_allow_html=True
    )
    uploaded = st.file_uploader(
        "Upload",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )
    if uploaded:
        st.image(
            uploaded,
            caption="Your uploaded photo",
            width="stretch"
        )

search_clicked = st.button(
    "🔍  Search Lost & Found Database",
    type="primary",
    use_container_width=True
)


# ─────────────────────────────────────────────────────────────
# SEARCH LOGIC
# ─────────────────────────────────────────────────────────────
if search_clicked:

    if not query_text and not uploaded:
        st.warning("⚠️ Please enter a description or upload a photo.")
        st.stop()

    # Save uploaded image temporarily
    temp_img_path = None
    if uploaded:
        suffix   = "." + uploaded.name.split(".")[-1]
        tmp      = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded.read())
        tmp.close()
        temp_img_path = tmp.name

    # Run search
    with st.spinner("🔍 Searching through database..."):
        results = engine.search_combined(
            query_text = query_text.strip() if query_text else None,
            image_path = temp_img_path,
            top_k      = top_k,
        )

    # Cleanup temp file
    if temp_img_path and os.path.exists(temp_img_path):
        os.unlink(temp_img_path)

    # Apply category filter
    if cat_filter != "All":
        results = [
            r for r in results
            if r.get("category", "") == cat_filter
        ]

    st.divider()

    # No results
    if not results:
        st.error(
            "😔 No matches found. "
            "Try different keywords or remove the category filter."
        )
        st.stop()

    # Mode label
    mode_labels = {
        "text":     "📝 Text Search",
        "image":    "📸 Image Search",
        "combined": "🔀 Text + Image Combined",
    }
    mode = results[0].get("match_type", "text")

    st.markdown(
        f'<div class="section-header">'
        f'✅ {len(results)} Match{"es" if len(results)>1 else ""} Found'
        f' &nbsp;·&nbsp; {mode_labels.get(mode, mode)}'
        f'</div>',
        unsafe_allow_html=True
    )

    # ─────────────────────────────────────────────────────────
    # RESULTS
    # ─────────────────────────────────────────────────────────
    for rank, r in enumerate(results, 1):
        conf     = r.get("confidence", 0)
        name     = r.get("name", "Unknown")
        category = r.get("category", "")
        color    = r.get("color", "")
        price    = r.get("price", 0)
        price_b  = r.get("price_bucket", "")
        desc     = r.get("description", "")
        lost_d   = r.get("lost_description", "")
        img_path = r.get("image_path", "")
        item_id  = r.get("item_id", "")

        # Confidence styling
        if conf >= 60:
            conf_cls  = "conf-high"
            prog_cls  = "prog-high"
            card_cls  = ""
            icon      = "🟢"
            label     = "Strong Match"
        elif conf >= 30:
            conf_cls  = "conf-medium"
            prog_cls  = "prog-medium"
            card_cls  = "medium"
            icon      = "🟡"
            label     = "Possible Match"
        else:
            conf_cls  = "conf-low"
            prog_cls  = "prog-low"
            card_cls  = "low"
            icon      = "🔴"
            label     = "Weak Match"

        with st.expander(
            f"{icon}  #{rank}  ·  {name}  ·  {conf:.1f}%  —  {label}",
            expanded=(rank <= 2)
        ):
            img_col, info_col = st.columns([1, 2], gap="large")

            # ── Image column ─────────────────────────────────
            with img_col:
                if img_path and os.path.exists(img_path):
                    st.image(img_path, width="stretch")
                else:
                    st.markdown(
                        "<div style='background:#f0f2f5;border-radius:12px;"
                        "height:200px;display:flex;align-items:center;"
                        "justify-content:center;font-size:4rem;'>📦</div>",
                        unsafe_allow_html=True
                    )
                # Item ID under image
                st.markdown(
                    f"<div style='text-align:center;margin-top:0.8rem;'>"
                    f"<span class='item-id-pill'>{item_id}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # ── Info column ──────────────────────────────────
            with info_col:

                # Name + confidence badge
                st.markdown(
                    f"<div style='margin-bottom:0.5rem;'>"
                    f"<span class='result-name'>{name}</span>&nbsp;&nbsp;"
                    f"<span class='conf-badge {conf_cls}'>"
                    f"{icon} {conf:.1f}% — {label}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Progress bar
                st.markdown(
                    f"<div class='prog-wrap'>"
                    f"<div class='prog-fill {prog_cls}' "
                    f"style='width:{min(conf,100):.1f}%'></div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Detail rows
                color_row = (
                    f"<div class='detail-key'>🎨 Color</div>"
                    f"<div class='detail-val'>{color.title()}</div>"
                    if color and color not in ("N/A", "unknown", "")
                    else ""
                )
                st.markdown(f"""
<div class="detail-grid">
    <div class="detail-key">📂 Category</div>
    <div class="detail-val">{category.replace('_',' ').title()}</div>
    {color_row}
    <div class="detail-key">💰 Price</div>
    <div class="detail-val">
        ₹{float(price):,.2f} &nbsp;·&nbsp; {price_b.title()}
    </div>
    <div class="detail-key">📄 Description</div>
    <div class="detail-val">{desc}</div>
</div>
""", unsafe_allow_html=True)

                # Lost item report
                if show_lost and lost_d:
                    st.markdown(
                        f"<div class='lost-box'>"
                        f"💬 <b>Lost item report in database:</b><br>{lost_d}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Claim instructions
                st.markdown(
                    f"<div class='claim-box'>"
                    f"🏷️ <b>To claim this item:</b> Visit the Lost &amp; "
                    f"Found office and show Item ID: "
                    f"<span style='font-family:monospace;font-size:1.1rem;"
                    f"background:rgba(255,255,255,0.2);padding:2px 8px;"
                    f"border-radius:6px;'>{item_id}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Ollama AI explanation
                if show_ai and query_text:
                    with st.spinner(
                        f"🤖 Getting Ollama explanation for #{rank}..."
                    ):
                        explanation = explain_match(query_text, r, conf)
                    st.markdown(
                        f"<div class='ai-box'>"
                        f"🤖 <b>Why this might be yours</b> "
                        f"<i style='color:#666;font-size:0.82rem;'>"
                        f"(Ollama llama3.2)</i><br><br>"
                        f"{explanation}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

    # ─────────────────────────────────────────────────────────
    # INSIGHTS
    # ─────────────────────────────────────────────────────────
    if len(results) > 1:
        st.markdown(
            '<div class="section-header">📊 Search Insights</div>',
            unsafe_allow_html=True
        )

        ic1, ic2, ic3 = st.columns(3, gap="medium")

        with ic1:
            st.markdown(f"""
<div class="insight-card">
    <div class="insight-num">{results[0]['confidence']:.1f}%</div>
    <div class="insight-label">🏆 Top Match Confidence</div>
</div>""", unsafe_allow_html=True)

        with ic2:
            cats = len({r.get("category","") for r in results})
            st.markdown(f"""
<div class="insight-card green">
    <div class="insight-num">{cats}</div>
    <div class="insight-label">📂 Categories Matched</div>
</div>""", unsafe_allow_html=True)

        with ic3:
            avg = sum(r["confidence"] for r in results) / len(results)
            st.markdown(f"""
<div class="insight-card orange">
    <div class="insight-num">{avg:.1f}%</div>
    <div class="insight-label">📈 Average Confidence</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Confidence bar chart
        st.markdown(
            "<p style='font-weight:700;color:#1a1a2e;"
            "margin-bottom:0.3rem;'>Confidence by result:</p>",
            unsafe_allow_html=True
        )
        chart_df = pd.DataFrame({
            "Item":       [r["name"][:28] for r in results],
            "Confidence": [round(r["confidence"], 1) for r in results],
        }).set_index("Item")
        st.bar_chart(chart_df, color="#e94560")


# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Lost &amp; Found Reunion · BLDEACET Progress Project 1 ·
    Sentence-Transformers + CLIP + ChromaDB + Ollama llama3.2 + Streamlit
</div>
""", unsafe_allow_html=True)
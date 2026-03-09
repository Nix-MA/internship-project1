# search_engine.py
# Save in: lost_found_reunion/search_engine.py

import numpy as np
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from transformers import CLIPModel, CLIPProcessor
import chromadb

CHROMA_DIR       = "chroma_db"
TEXT_MODEL_NAME  = "all-MiniLM-L6-v2"
IMAGE_MODEL_NAME = "openai/clip-vit-base-patch32"


class LostAndFoundSearchEngine:

    def __init__(self):
        print("Initialising search engine...")

        print("  Loading Sentence-Transformers...")
        self.text_model = SentenceTransformer(TEXT_MODEL_NAME)

        print("  Loading CLIP model...")
        self.clip_model     = CLIPModel.from_pretrained(IMAGE_MODEL_NAME)
        self.clip_processor = CLIPProcessor.from_pretrained(IMAGE_MODEL_NAME)
        self.clip_model.eval()

        print("  Connecting to ChromaDB...")
        self.client           = chromadb.PersistentClient(path=CHROMA_DIR)
        self.text_collection  = self.client.get_collection("lost_found_text")
        self.image_collection = self.client.get_collection("lost_found_image")

        total = self.text_collection.count()
        print(f"  Search engine ready — {total} items indexed")

    def stats(self):
        return {
            "total_items": self.text_collection.count()
        }

    def _embed_text(self, query):
        emb = self.text_model.encode(
            [query],
            normalize_embeddings=True
        )
        return emb.tolist()

    def _embed_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        inputs = self.clip_processor(
            images=image,
            return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.clip_model.get_image_features(**inputs)
        emb = outputs.detach().cpu().numpy().flatten()
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return [emb.tolist()]

    def _format(self, chroma_results, match_type):
        results   = []
        ids       = chroma_results["ids"][0]
        metadatas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]

        for item_id, meta, dist in zip(ids, metadatas, distances):
            confidence = max(0.0, (1 - dist) * 100)
            results.append({
                "item_id":          item_id,
                "name":             meta.get("name", ""),
                "category":         meta.get("category", ""),
                "color":            meta.get("color", "N/A"),
                "price":            meta.get("price", 0),
                "price_bucket":     meta.get("price_bucket", ""),
                "description":      meta.get("description", ""),
                "lost_description": meta.get("lost_description", ""),
                "image_path":       meta.get("image_path", ""),
                "confidence":       round(confidence, 2),
                "match_type":       match_type,
            })
        return results

    def search_by_text(self, query, top_k=5):
        q_emb = self._embed_text(query)
        raw   = self.text_collection.query(
            query_embeddings=q_emb,
            n_results=top_k
        )
        return self._format(raw, match_type="text")

    def search_by_image(self, image_path, top_k=5):
        q_emb = self._embed_image(image_path)
        raw   = self.image_collection.query(
            query_embeddings=q_emb,
            n_results=top_k
        )
        return self._format(raw, match_type="image")

    def search_combined(self, query_text=None, image_path=None, top_k=5):
        if not query_text and not image_path:
            return []

        scores = {}

        if query_text:
            text_results = self.search_by_text(query_text, top_k * 2)
            for r in text_results:
                scores[r["item_id"]] = {
                    **r,
                    "confidence": r["confidence"] * 0.65
                }

        if image_path:
            image_results = self.search_by_image(image_path, top_k * 2)
            for r in image_results:
                if r["item_id"] in scores:
                    scores[r["item_id"]]["confidence"] += (
                        r["confidence"] * 0.35
                    )
                    scores[r["item_id"]]["match_type"] = "combined"
                else:
                    scores[r["item_id"]] = {
                        **r,
                        "confidence": r["confidence"] * 0.35
                    }

        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["confidence"],
            reverse=True
        )

        if query_text and image_path:
            mode = "combined"
        elif query_text:
            mode = "text"
        else:
            mode = "image"

        for r in sorted_results:
            r["match_type"] = mode

        return sorted_results[:top_k]
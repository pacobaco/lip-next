from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging
import numpy as np
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger("lip")


def compute_sentiment(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    try:
        return TextBlob(text).sentiment.polarity
    except Exception:
        return 0.0


def compute_tfidf_scores(
    texts: List[str], query_keywords: Optional[List[str]] = None
) -> List[float]:
    if not texts:
        return []
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=8000,
            ngram_range=(1, 2),
        )
        matrix = vectorizer.fit_transform(texts)

        if query_keywords:
            query_vec = vectorizer.transform([" ".join(query_keywords)])
            scores = (matrix * query_vec.T).toarray().ravel()
        else:
            scores = np.asarray(matrix.mean(axis=1)).ravel()

        return scores.tolist()
    except Exception as e:
        logger.warning(f"TF-IDF failed: {e}")
        return [0.0] * len(texts)


def rank_articles(
    articles: List[Dict],
    seed_keywords: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Rank articles by relevance + sentiment + recency.
    Each article dict should contain at least 'text' and 'url'.
    """
    if not articles:
        return []

    texts = [
        (a.get("text") or "") + " " + (a.get("title") or "") + " " + (a.get("body") or "")
        for a in articles
    ]

    sentiments = [compute_sentiment(t) for t in texts]
    relevances = compute_tfidf_scores(texts, seed_keywords)

    now = datetime.now(timezone.utc)
    ranked = []

    for art, sent, rel in zip(articles, sentiments, relevances):
        recency = 1.0
        pub = art.get("published_at")
        if pub:
            if isinstance(pub, str):
                try:
                    pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except Exception:
                    pub = None
            if isinstance(pub, datetime):
                age_hours = (now - pub).total_seconds() / 3600
                recency = max(0.05, 1.0 - (age_hours / 96))  # 4-day decay

        # Weighted score (tunable)
        score = (
            0.45 * float(rel)
            + 0.25 * ((float(sent) + 1) / 2)  # map -1..1 → 0..1
            + 0.30 * recency
        )

        ranked.append(
            {
                **art,
                "sentiment": float(sent),
                "relevance": float(rel),
                "recency": float(recency),
                "score": float(score),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

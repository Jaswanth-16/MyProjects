"""Bounded supervised text classifier; no paid APIs or keyword-only mock AI."""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from caselake.sample_data import CATEGORIES


def redact(text):
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", " EMAIL ", text)
    text = re.sub(r"\b\d{7,}\b", " NUMBER ", text)
    return text.lower()


def fit_model(rows, min_macro_f1=0.65):
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]
    if len(rows) > 5000:
        raise ValueError("Training demo is capped at 5000 current tickets")
    if {r["ticket_id"] for r in train} & {r["ticket_id"] for r in test}:
        raise ValueError("Train/test ticket leakage")
    for part in (train, test):
        if {r["category"] for r in part} != set(CATEGORIES):
            raise ValueError("Every category must appear in train and test")
    model = Pipeline([
        ("tfidf", TfidfVectorizer(preprocessor=redact, lowercase=True,
                                  ngram_range=(1, 2), min_df=1, max_features=10000)),
        ("classifier", LogisticRegression(max_iter=300, class_weight="balanced", random_state=42)),
    ])
    model.fit([r["text"] for r in train], [r["category"] for r in train])
    predicted = model.predict([r["text"] for r in test])
    actual = [r["category"] for r in test]
    metrics = {"accuracy": float(accuracy_score(actual, predicted)),
               "macro_f1": float(f1_score(actual, predicted, average="macro")),
               "train_rows": len(train), "test_rows": len(test),
               "labels": list(CATEGORIES),
               "confusion_matrix": confusion_matrix(actual, predicted, labels=list(CATEGORIES)).tolist()}
    if metrics["macro_f1"] < min_macro_f1:
        raise ValueError(f"Model quality gate failed: {metrics}")
    return model, metrics


def score(model, rows, threshold=0.7):
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if not rows:
        return []
    probabilities = model.predict_proba([r["text"] for r in rows])
    vocabulary = model.named_steps["tfidf"].transform([r["text"] for r in rows])
    result = []
    for index, (row, probs) in enumerate(zip(rows, probabilities)):
        best = int(np.argmax(probs))
        confidence = float(probs[best])
        # An all-OOV message must abstain even if the class prior is skewed.
        accepted = vocabulary[index].nnz > 0 and confidence >= threshold
        result.append({"ticket_id": row["ticket_id"], "event_id": row["event_id"],
                       "suggested_category": str(model.classes_[best]) if accepted else "human_review",
                       "confidence": confidence, "needs_review": not accepted})
    return result

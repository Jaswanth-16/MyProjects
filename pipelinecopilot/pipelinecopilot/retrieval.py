"""Deterministic BM25 retrieval over a versioned, curated runbook corpus."""
import math
import re
from collections import Counter

STOP = set('a an the is are was were to of for in on and or with my i it this that how why can do does please'.split())
ALIASES = {'forbidden': 'authorization', 'denied': 'authorization', 'permission': 'authorization',
           'permissions': 'authorization', 'timed': 'timeout', 'mapping': 'schema',
           'columns': 'column', 'expired': 'authentication', 'credentials': 'authentication',
           'throttled': 'throttling', 'unavailable': 'offline', 'duplicates': 'duplicate'}

def tokens(text):
    words = re.findall(r'[a-z0-9]+', text.lower())
    return [ALIASES.get(w, w) for w in words if w not in STOP]

class Index:
    def __init__(self, documents):
        if not documents or len({d['id'] for d in documents}) != len(documents):
            raise ValueError('Corpus requires unique document IDs')
        self.documents = documents
        self.counts = [Counter(tokens(' '.join([d['title'], d['symptoms'], ' '.join(d['checks']), ' '.join(d['codes'])]))) for d in documents]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / len(documents)
        self.df = Counter(t for counts in self.counts for t in counts)

    def search(self, query, limit=3):
        if not 1 <= limit <= 5:
            raise ValueError('limit must be 1-5')
        q = set(tokens(query)); result = []
        for doc, counts, length in zip(self.documents, self.counts, self.lengths):
            score = 0.0
            for term in q:
                frequency = counts[term]
                if frequency:
                    inverse = math.log(1 + (len(self.documents) - self.df[term] + .5) / (self.df[term] + .5))
                    score += inverse * frequency * 2.5 / (frequency + 1.5 * (.25 + .75 * length / self.average))
            matched_codes = [code for code in doc['codes'] if re.search(r'(?<!\w)' + re.escape(code) + r'(?!\w)', query, re.I)]
            if matched_codes:
                score += 15
            if score > 0:
                result.append({'document': doc, 'score': round(score, 4), 'matched_codes': matched_codes})
        return sorted(result, key=lambda r: (-r['score'], r['document']['id']))[:limit]

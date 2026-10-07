import json
import time
from pathlib import Path
from .retrieval import Index
from .safety import validate_request, redact
from .llm import generate, ModelError

DATA = Path(__file__).resolve().parent.parent / 'data'

class Assistant:
    def __init__(self, documents=None, use_llm=False):
        self.index = Index(documents if documents is not None else json.loads((DATA / 'runbooks.json').read_text()))
        self.use_llm = use_llm

    def ask(self, payload):
        start = time.perf_counter()
        question, log = validate_request(payload)
        hits = self.index.search(question + '\n' + log)
        strong = hits and (hits[0]['matched_codes'] or hits[0]['score'] >= 3.5)
        result = {'mode': 'retrieval', 'status': 'insufficient_evidence', 'summary': 'No sufficiently matching runbook. Provide the activity error code and a sanitised log.',
                  'checks': [], 'citations': [], 'redacted_log': log, 'warning': None}
        conflicting_codes = sum(bool(h['matched_codes']) for h in hits) > 1
        if conflicting_codes:
            result.update(status='ambiguous_evidence', summary='The input contains error codes from multiple failure categories. Provide one activity failure at a time.')
            strong = False
        if strong:
            doc = hits[0]['document']
            result.update(status='supported', summary='Possible issue: ' + doc['title'] + '. Confirm with the checks below.', checks=doc['checks'])
            selected = [hits[0]]
            if self.use_llm:
                try:
                    answer = generate(question, log, hits)
                    result.update(mode='llm', summary=redact(answer['summary']), checks=[redact(s) for s in answer['checks']])
                    selected = [h for h in hits if h['document']['id'] in answer['citation_ids']]
                except ModelError:
                    result['warning'] = 'LLM unavailable or output rejected; showing the extractive runbook fallback.'
            result['citations'] = [{'id': h['document']['id'], 'title': h['document']['title'], 'url': h['document']['source_url'],
                                    'score': h['score']} for h in selected]
        result['elapsed_ms'] = round((time.perf_counter() - start) * 1000, 2)
        return result

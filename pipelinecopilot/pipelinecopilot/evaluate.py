import json
from .core import Assistant, DATA

def evaluate():
    assistant = Assistant(); cases = json.loads((DATA / 'eval_cases.json').read_text())
    supported = rejected = correct = abstained = 0; details = []
    for case in cases:
        answer = assistant.ask({'question': case['question'], 'log': case.get('log', '')})
        found = answer['citations'][0]['id'] if answer['citations'] else None
        if case['expected'] is None:
            rejected += 1; abstained += found is None
        else:
            supported += 1; correct += found == case['expected']
        details.append({'id': case['id'], 'expected': case['expected'], 'actual': found, 'pass': found == case['expected']})
    return {'evaluation': 'Curated lexical retrieval benchmark, not live LLM answer quality', 'cases': len(cases),
            'supported_cases': supported, 'unsupported_cases': rejected,
            'top1_accuracy': round(correct / supported, 4), 'abstention_accuracy': round(abstained / rejected, 4), 'details': details}

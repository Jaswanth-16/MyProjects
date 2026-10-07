"""Best-effort redaction; never a substitute for sanitised input."""
import re

def redact(text):
    # Includes common JSON, connection-string and HTTP header forms.
    text = re.sub(r'(?i)(authorization\s*:\s*(?:bearer|basic)\s+)\S+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)((?:api[-_]?key|accountkey|password|secret|access[-_]?token)\s*["\']?\s*[:=]\s*["\']?)[^\s;"\',}]+', r'\1[REDACTED]', text)
    text = re.sub(r'(?i)([?&](?:sig|token|code)=)[^&\s"\']+', r'\1[REDACTED]', text)
    text = re.sub(r'\bsk-[A-Za-z0-9_-]{12,}\b', '[REDACTED]', text)
    return text

class InputError(ValueError):
    pass

def validate_request(payload):
    if not isinstance(payload, dict) or set(payload) - {'question', 'log'}:
        raise InputError('Use an object with question and optional log only')
    question = payload.get('question'); log = payload.get('log', '')
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise InputError('Question must contain 1-2000 characters')
    if not isinstance(log, str) or len(log) > 16000:
        raise InputError('Log must be text, at most 16000 characters')
    return redact(question.strip()), redact(log)

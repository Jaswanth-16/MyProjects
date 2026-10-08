"""Best-effort redaction and local input limits."""
import re
from .contracts import ContractError

def redact(text):
    text = re.sub(r'(?i)(authorization\s*:\s*(?:bearer|basic)\s+)\S+', r'\1[REDACTED]', text)
    text = re.sub(r"(?i)((?:api[-_]?key|accountkey|password|secret|access[-_]?token)\s*[\"']?\s*[:=]\s*[\"']?)[^\s;\"',}]+", r'\1[REDACTED]', text)
    text = re.sub(r"(?i)([?&](?:sig|token|code)=)[^&\s\"']+", r'\1[REDACTED]', text)
    text = re.sub(r'\bsk-(?:ant-)?[A-Za-z0-9_-]{12,}\b', '[REDACTED]', text)
    return text

def clean_text(value, max_length=16000):
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise ContractError('Expected non-empty text within input limit')
    return redact(value.strip())

def scrub(value):
    if isinstance(value, str):return redact(value)
    if isinstance(value, list):return [scrub(x) for x in value]
    if isinstance(value, dict):return {k:scrub(v) for k,v in value.items()}
    return value

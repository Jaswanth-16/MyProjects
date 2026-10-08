from .core import analyse
from .contracts import validate,obj,string

def handle(payload,provider):
    validate(payload,obj({'log':string(16000)}))
    return analyse(payload['log'],provider)

def options():return {}

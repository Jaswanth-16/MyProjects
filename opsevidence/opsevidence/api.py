from .contracts import validate,obj,string
from .agent import investigate
from .tools import Tools

def handle(payload,provider):
    validate(payload,obj({'incident_id':string(40),'question':string(2000)}))
    return investigate(payload['incident_id'],payload['question'],provider)

def options():return {'incidents':Tools.incidents()}

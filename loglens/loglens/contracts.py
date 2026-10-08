"""Small strict validator for the JSON schema subset used in these labs."""
class ContractError(ValueError):
    pass

def validate(value, schema, path='$'):
    if 'anyOf' in schema:
        for option in schema['anyOf']:
            try:
                validate(value, option, path); return
            except ContractError:
                pass
        raise ContractError(path + ': no accepted type')
    kind = schema.get('type')
    valid = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str), 'integer': type(value) is int,
             'number': type(value) in (int, float), 'boolean': type(value) is bool,
             'null': value is None}
    if kind and not valid.get(kind, False):
        raise ContractError(path + ': invalid type')
    if 'enum' in schema and value not in schema['enum']:
        raise ContractError(path + ': unexpected value')
    if kind == 'object':
        props = schema.get('properties', {})
        if any(k not in value for k in schema.get('required', [])):
            raise ContractError(path + ': required field missing')
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ContractError(path + ': unknown field')
        for key, item in value.items():
            if key in props:
                validate(item, props[key], path + '.' + key)
    elif kind == 'array':
        if not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', 1000):
            raise ContractError(path + ': array length out of bounds')
        for i, item in enumerate(value):
            validate(item, schema['items'], path + '[' + str(i) + ']')
    elif kind == 'string':
        if not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', 100000):
            raise ContractError(path + ': string length out of bounds')
    elif kind in ('integer', 'number'):
        if not schema.get('minimum', float('-inf')) <= value <= schema.get('maximum', float('inf')):
            raise ContractError(path + ': number out of bounds')

def obj(properties, required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}

def string(limit=1000):
    return {'type':'string','minLength':1,'maxLength':limit}

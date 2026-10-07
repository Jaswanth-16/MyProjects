"""Configure ADF after Bicep deployment and Function publish. Requires az login.

Function keys are captured in memory and passed to Key Vault in a temporary file;
they are never printed, committed or placed in command-line arguments.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def az(*args):
    result = subprocess.run(['az', *args, '--only-show-errors'], capture_output=True, text=True)
    if result.returncode:
        # Avoid echoing provider responses that could contain credential material.
        raise RuntimeError(f'Azure CLI operation failed: {args[0]}. Check login, RBAC propagation and resource names.')
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource-group', required=True)
    parser.add_argument('--deployment', default='transitpulse')
    args = parser.parse_args()
    outputs = json.loads(az('deployment', 'group', 'show', '-g', args.resource_group,
                            '-n', args.deployment, '--query', 'properties.outputs', '-o', 'json'))
    value = lambda name: outputs[name]['value']
    function_key = az('functionapp', 'keys', 'list', '-g', args.resource_group,
                      '-n', value('functionAppName'), '--query', 'functionKeys.default', '-o', 'tsv')
    if not function_key or function_key == 'null':
        raise RuntimeError('Function host key unavailable; publish the function and wait for startup before retrying.')
    with tempfile.TemporaryDirectory(prefix='transitpulse-config-') as tmp:
        secret_path = Path(tmp) / 'function-key'
        secret_path.write_text(function_key, encoding='utf-8')
        os.chmod(secret_path, 0o600)
        az('keyvault', 'secret', 'set', '--vault-name', value('keyVaultName'),
           '--name', 'transitpulse-function-key', '--file', str(secret_path), '-o', 'none')
        secret_path.unlink()
        subscription = az('account', 'show', '--query', 'id', '-o', 'tsv')
        base = f'https://management.azure.com/subscriptions/{subscription}/resourceGroups/{args.resource_group}/providers/Microsoft.DataFactory/factories/{value("factoryName")}'
        replacements = {'__STORAGE_DFS_URL__': value('storageDfsUrl'), '__KEYVAULT_URL__': value('keyVaultUrl'), '__FUNCTION_URL__': value('functionUrl')}
        config_root = Path(__file__).resolve().parents[1] / 'azure/adf'
        for name, resource_type in [('ls_lake', 'linkedservices'), ('ls_keyvault', 'linkedservices'),
                                    ('ls_function', 'linkedservices'), ('ds_batch', 'datasets'), ('pl_transitpulse', 'pipelines')]:
            text = (config_root / f'{name}.json').read_text(encoding='utf-8')
            for token, replacement in replacements.items():
                text = text.replace(token, replacement)
            payload = Path(tmp) / f'{name}.json'
            payload.write_text(json.dumps(json.loads(text)), encoding='utf-8')
            az('rest', '--method', 'put', '--url', f'{base}/{resource_type}/{name}?api-version=2018-06-01',
               '--body', '@' + str(payload), '-o', 'none')
            print(f'Configured {name}')


if __name__ == '__main__':
    main()

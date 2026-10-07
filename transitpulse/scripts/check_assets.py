"""Check internal configuration references, docs links and demo evidence."""

import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def main():
    root = Path(__file__).resolve().parents[1]
    files = list((root / 'azure/adf').glob('*.json'))
    assets = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in files}
    for asset in assets.values():
        serialized = json.dumps(asset)
        for name in re.findall(r'"referenceName": "([^"]+)"', serialized):
            if name not in assets:
                raise ValueError(f'ADF reference has no matching asset: {name}')
    pipeline = assets['pl_transitpulse']['properties']
    if pipeline['concurrency'] != 1:
        raise ValueError('demo pipeline must serialize ADF executions')
    activities = {a['name']: a for a in pipeline['activities']}
    dependencies = activities['ValidateMergePublish']['dependsOn']
    if dependencies != [{'activity': 'ArchiveBronze', 'dependencyConditions': ['Succeeded']}]:
        raise ValueError('processing must depend on successful bronze archival')
    for path in [root / 'host.json', root / 'powerbi/theme.json', root / 'docs/demo-results.json']:
        json.loads(path.read_text(encoding='utf-8'))
    for doc in [root / 'README.md', *(root / 'docs').glob('*.md'), root / 'powerbi/README.md']:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if target.startswith(('https:', 'http:', '#', 'mailto:')):
                continue
            if not (doc.parent / target.split('#')[0]).exists():
                raise ValueError(f'broken relative link in {doc.name}: {target}')
    evidence = json.loads((root / 'docs/demo-results.json').read_text())
    if evidence['unique_trips'] != evidence['initial']['inserted'] + evidence['delta']['inserted']:
        raise ValueError('demo evidence does not reconcile')
    ET.parse(root / 'docs/preview.svg')
    print('ADF references, dependencies, JSON, SVG, documentation links and demo evidence are valid.')


if __name__ == '__main__':
    main()

"""Install only reviewed agent files listed in the repository manifest."""
import argparse
import json
from pathlib import Path
import sys

from worker_files import digest, install_many


def setup(root, home, replace=False):
    root = Path(root)
    entries = json.loads((root / 'extensions/agent-files.json').read_text())
    prepared = []
    for entry in entries:
        source = Path(entry['source'])
        target = entry['destination']
        if source.is_absolute() or '..' in source.parts or not source.parts or source.parts[:2] != ('config', 'agents'):
            raise ValueError(f'Invalid agent source: {source}')
        if target not in ('.codex/config.toml', '.codex/AGENTS.md', '.claude/settings.json', '.cursor/cli-config.json') and not target.startswith(('.agents/skills/', '.claude/skills/')):
            raise ValueError(f'Invalid agent destination: {target}')
        data = (root / source).read_bytes()
        if digest(data) != entry['sha256']:
            raise ValueError(f'Agent snapshot checksum mismatch: {source}')
        prepared.append((target, data, 0o700 if entry.get('executable') else 0o600, replace))
    install_many(home, prepared)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--home', required=True)
    parser.add_argument('--replace-config', action='store_true')
    args = parser.parse_args()
    try:
        setup(args.root, args.home, args.replace_config)
    except (ValueError, OSError) as error:
        print(f'Error: Agent configuration: {error}', file=sys.stderr)
        sys.exit(1)

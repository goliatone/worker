"""Inspect Go build metadata without executing the target binary."""
import subprocess


def metadata(path):
    result = subprocess.run(['go', 'version', '-m', str(path)], capture_output=True, text=True, check=True)
    values = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == 'path':
            values['path'] = parts[1]
        elif len(parts) >= 3 and parts[0] == 'mod':
            values['version'] = parts[2]
        elif len(parts) == 2 and parts[0] == 'build' and '=' in parts[1]:
            key, value = parts[1].split('=', 1)
            values[key] = value
    return values


def validate_binary(path, package, arch, version=None):
    info = metadata(path)
    if info.get('path') != package or info.get('GOOS') != 'darwin' or info.get('GOARCH') != arch:
        raise ValueError(f'Wrong package or architecture in {path}; need {package} for darwin/{arch}.')
    if version is not None and info.get('version') != version:
        raise ValueError(f'Wrong version in {path}; need {version}.')
    return info


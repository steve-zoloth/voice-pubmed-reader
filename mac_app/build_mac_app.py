"""Build a Terminal-free launcher for an already configured Mac reader install."""
from pathlib import Path
import argparse
import plistlib
import subprocess
import sys


def build(destination, repository, python):
    destination = Path(destination).expanduser().resolve()
    repository = Path(repository).expanduser().resolve()
    if destination.exists():
        raise SystemExit('Destination already exists; choose a new path to preserve it.')
    if not (repository / 'run_realtime_pubmed.command').is_file():
        raise SystemExit('Choose the existing voice_pubmed_bot repository.')
    contents = destination / 'Contents'
    executable = contents / 'MacOS' / 'VoicePubMedReader'
    executable.parent.mkdir(parents=True)
    info = {'CFBundleName': 'Voice PubMed Reader', 'CFBundleDisplayName': 'Voice PubMed Reader',
            'CFBundleIdentifier': 'local.voicepubmed.reader', 'CFBundleExecutable': executable.name,
            'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': '1.0', 'CFBundleVersion': '1',
            'NSHighResolutionCapable': True, 'ReaderFolder': str(repository), 'ReaderPython': str(Path(python).resolve())}
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    subprocess.run(['/usr/bin/swiftc', str(Path(__file__).with_name('MacLauncher.swift')),
                    '-o', str(executable), '-framework', 'AppKit'], check=True)
    subprocess.run(['/usr/bin/codesign', '--force', '--sign', '-', str(destination)], check=True)
    print(destination)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--repository', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    build(args.destination, args.repository, args.python)

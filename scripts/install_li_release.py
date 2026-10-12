"""Install the immutable Li dependency without merging caches/raw files into Git."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.domain_bridge.bridge import PINNED_COMMIT, PINNED_DB_SHA256, PINNED_SOURCE_SHA256, verify_release


def selected(path):
    return ((path.parts[0] == 'tax_graph' and path.suffix in ('.py', '.csv', '.json', '.md')) or
            (path.parts[:2] == ('official', 'tools') and path.suffix == '.py') or
            (path.parts[0] == 'official' and path.suffix == '.csv') or
            (len(path.parts) == 2 and path.parts[0] == 'official' and path.suffix in ('.md', '.txt')))


def download(url, path, maximum):
    size = 0
    with urllib.request.urlopen(url, timeout=60) as response, path.open('wb') as target:
        while block := response.read(1024 * 1024):
            size += len(block)
            if size > maximum:
                raise ValueError('release download too large')
            target.write(block)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--system-trust', action='store_true', help='Use OS trusted CA store through installed truststore')
    parser.add_argument('--from-directory', type=Path)
    parser.add_argument('--target', type=Path, default=ROOT / 'data/li/releases' / PINNED_COMMIT)
    args = parser.parse_args(argv)
    if args.system_trust:
        import truststore
        truststore.inject_into_ssl()
    target = args.target.resolve()
    if target.exists():
        verify_release(target)
        print(json.dumps({'status': 'already_installed', 'path': str(target), 'release': PINNED_COMMIT}))
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.li-install-', dir=target.parent) as temporary:
        work = Path(temporary)
        release = work / 'release'
        release.mkdir()
        if args.from_directory:
            source = args.from_directory.resolve()
            verify_release(source)
            for path in source.rglob('*'):
                relative = path.relative_to(source)
                if path.is_file() and (selected(relative) or relative.as_posix() == 'official/official.sqlite'):
                    destination = release / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, destination)
        else:
            archive = work / 'source.tar.gz'
            download(f'https://codeload.github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/tar.gz/{PINNED_COMMIT}', archive, 300_000_000)
            with tarfile.open(archive) as tar:
                for member in tar:
                    relative = Path(*Path(member.name).parts[1:])
                    if '..' in relative.parts or relative.is_absolute() or not member.isfile() or not selected(relative):
                        continue
                    destination = release / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as origin, destination.open('wb') as output:
                        shutil.copyfileobj(origin, output)
            download(f'https://media.githubusercontent.com/media/ZhihongWu-dev/Asia-Tax-AI-Agent/{PINNED_COMMIT}/official/official.sqlite',
                     release / 'official/official.sqlite', 260_000_000)
        verify_release(release)
        manifest = {'release': PINNED_COMMIT, 'database_sha256': PINNED_DB_SHA256,
                    'source_sha256': PINNED_SOURCE_SHA256, 'format': 'li-release-v1'}
        (release / 'release.json').write_text(json.dumps(manifest, indent=2) + '\n')
        release.rename(target)
    print(json.dumps({'status': 'installed', 'path': str(target), **manifest}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

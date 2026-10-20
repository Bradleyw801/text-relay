#!/usr/bin/env python3
"""Vet new APKs before the index is built. The publish workflow runs this from fdroid/.

New builds arrive in incoming/, whole or split into NAME.apk.part00, .part01, and so on
(by git push or GitHub's "Upload files"), or are dropped straight into repo/.

For each app this keeps the newest build signed with the key pinned in
metadata/<package>.yml (AllowedAPKSigningKeys) and deletes its older builds. A new build
is refused, and deleted, when the repository has no metadata for its package, when it is
signed with a different key, or when it is not newer than the build already published. If
no build of an app matches its pinned key at all, nothing of that app is touched, so a typo
in a pin can never take an app out of the repository.

Refusals go to the file named by REFUSED_FILE, one per line, so the workflow can publish
everything else first and then fail the run to report them. A one-line summary of what
changed goes to SUMMARY_FILE for the commit message.
"""

import glob
import hashlib
import logging
import os
import shutil
import sys

import yaml

logging.disable(logging.WARNING)  # androguard is chatty about harmless things

from fdroidserver import common  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def join_parts():
    """Join incoming/NAME.apk.part00, .part01, ... into incoming/NAME.apk."""
    joined = []
    for first in sorted(glob.glob('incoming/*.apk.part00')):
        name = os.path.basename(first)[: -len('.part00')]
        parts = sorted(glob.glob(os.path.join('incoming', glob.escape(name) + '.part*')))
        with open(os.path.join('incoming', name), 'wb') as out:
            for part in parts:
                with open(part, 'rb') as f:
                    shutil.copyfileobj(f, out)
        for part in parts:
            os.remove(part)
        joined.append(f'{name} ({len(parts)} pieces)')
    return joined


def pinned_keys(appid):
    """Return the set of allowed signer fingerprints, an empty set if the app pins none,
    or None if the repository has no metadata for this package."""
    path = os.path.join('metadata', appid + '.yml')
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    keys = data.get('AllowedAPKSigningKeys') or []
    if isinstance(keys, str):
        keys = [keys]
    return {str(k).strip().lower() for k in keys}


def app_name(appid):
    path = os.path.join('metadata', appid + '.yml')
    try:
        with open(path, encoding='utf-8') as f:
            return (yaml.safe_load(f) or {}).get('Name') or appid
    except OSError:
        return appid


def main():
    refused = []  # (path, reason)
    superseded = []  # paths removed because a newer build replaces them
    published = []  # descriptions of builds moved into repo/
    duplicates = []  # incoming copies of builds already published

    joined = join_parts()

    builds = []
    for path in sorted(glob.glob('incoming/*.apk')) + sorted(glob.glob('repo/*.apk')):
        try:
            appid, vercode, vername = common.get_apk_id(path)
            signer = (common.apk_signer_fingerprint(path) or '').lower()
        except Exception as e:  # not an APK, or a broken one
            if path.startswith('incoming/'):
                refused.append((path, f'not a readable APK ({e.__class__.__name__})'))
            else:
                print(f'warning: {path} is not a readable APK; left alone')
            continue
        builds.append({
            'path': path,
            'appid': appid,
            'vercode': int(vercode),
            'vername': vername,
            'signer': signer,
            'incoming': path.startswith('incoming/'),
            'sha256': sha256(path),
        })

    by_app = {}
    for b in builds:
        by_app.setdefault(b['appid'], []).append(b)

    errors = []
    moves = []
    for appid, items in sorted(by_app.items()):
        name = app_name(appid)
        keys = pinned_keys(appid)
        if keys is None:
            for b in items:
                if b['incoming']:
                    refused.append((b['path'], f'{appid} is not an app in this repository (there is no metadata/{appid}.yml)'))
                else:
                    print(f'warning: {b["path"]} has no metadata/{appid}.yml; left alone')
            continue

        good = [b for b in items if not keys or b['signer'] in keys]
        bad = [b for b in items if b not in good]
        if not good:
            errors.append(f'No build of {name} matches the key pinned in metadata/{appid}.yml; nothing of {name} was changed.')
            continue
        for b in bad:
            refused.append((b['path'], f'signed with a different key than {name} (signer {b["signer"][:16]}...)'))

        live = [b for b in good if not b['incoming']]
        live_top = max(live, key=lambda b: b['vercode']) if live else None
        live_hashes = {b['sha256'] for b in live}

        # Newest first; on equal version codes the published build wins.
        good.sort(key=lambda b: (b['vercode'], not b['incoming']), reverse=True)
        winner = good[0]
        for b in good[1:]:
            if b['incoming'] and b['sha256'] in live_hashes:
                duplicates.append(b['path'])
            elif b['incoming'] and live_top is not None and b['vercode'] <= live_top['vercode']:
                refused.append((b['path'], f'version {b["vername"]} ({b["vercode"]}) is not newer than the published '
                                           f'{live_top["vername"]} ({live_top["vercode"]})'))
            else:
                superseded.append(b['path'])
        if winner['incoming']:
            moves.append(winner)

    for path, _reason in refused:
        if os.path.exists(path):
            os.remove(path)
    for path in superseded + duplicates:
        if os.path.exists(path):
            os.remove(path)
    for b in moves:
        dest = os.path.join('repo', os.path.basename(b['path']))
        os.replace(b['path'], dest)
        published.append(f'{app_name(b["appid"])} {b["vername"]} ({os.path.basename(dest)})')

    for line in joined:
        print(f'joined {line}')
    for line in published:
        print(f'published {line}')
    for path in superseded:
        print(f'removed {path} (superseded)')
    for path in duplicates:
        print(f'removed {path} (already published)')
    for path, reason in refused:
        print(f'REFUSED {os.path.basename(path)}: {reason}')
    for line in errors:
        print(f'ERROR {line}')

    refused_file = os.environ.get('REFUSED_FILE')
    if refused_file:
        with open(refused_file, 'w', encoding='utf-8') as f:
            for path, reason in refused:
                f.write(f'{os.path.basename(path)}: {reason}\n')
            for line in errors:
                f.write(line + '\n')
    summary_file = os.environ.get('SUMMARY_FILE')
    if summary_file:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(('Publish ' + ', '.join(published)) if published else 'Tidy incoming APKs')
    return 0


if __name__ == '__main__':
    sys.exit(main())

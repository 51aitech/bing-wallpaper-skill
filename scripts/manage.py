"""Install or manage the current user's daily wallpaper job."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

LABEL = 'io.github.bing-wallpaper.daily'
ROOT = Path.home() / 'Library/Application Support/Bing Wallpaper'
PLIST = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
DOMAIN = 'gui/' + str(os.getuid())


def job(hour, market):
    environment = {k: v for k, v in os.environ.items() if k.lower() in
                   ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')}
    environment['BING_WALLPAPER_MARKET'] = market
    return {'Label': LABEL,
            'ProgramArguments': [sys.executable, str(ROOT / 'update.py')],
            'RunAtLoad': True, 'StartInterval': 3600,
            'StartCalendarInterval': {'Hour': hour, 'Minute': 0},
            'ProcessType': 'Background', 'EnvironmentVariables': environment,
            'StandardOutPath': str(ROOT / 'update.log'),
            'StandardErrorPath': str(ROOT / 'error.log')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'status', 'disable'])
    parser.add_argument('--hour', type=int, choices=range(24), default=9)
    parser.add_argument('--market', default='en-US')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('macOS is required')
    if args.action == 'status':
        result = subprocess.run(['launchctl', 'list', LABEL], capture_output=True, text=True)
        print('Job loaded' if result.returncode == 0 else 'Job not loaded')
        state = ROOT / 'current.json'
        if state.exists():
            print(state.read_text())
        return
    if args.dry_run:
        print(json.dumps({'action': args.action, 'hour': args.hour,
                          'market': args.market, 'label': LABEL,
                          'proxy_inherited': any(k.lower().endswith('_proxy') for k in os.environ)}))
        return
    if args.action == 'disable':
        loaded = subprocess.run(['launchctl', 'list', LABEL], capture_output=True).returncode == 0
        if loaded:
            subprocess.run(['launchctl', 'bootout', DOMAIN + '/' + LABEL], check=True)
        if PLIST.exists():
            PLIST.replace(PLIST.with_suffix('.plist.disabled'))
        print('Disabled; photos and state retained')
        return
    conflicts = [p for p in PLIST.parent.glob('*bing-wallpaper*.plist') if p != PLIST]
    if conflicts:
        parser.error('Another Bing wallpaper job exists. Review it before installing a second job.')
    if PLIST.exists() or (ROOT / 'update.py').exists():
        parser.error('An installation exists. Inspect and back it up before replacing it.')
    ROOT.mkdir(parents=True, exist_ok=True)
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).with_name('update.py'), ROOT / 'update.py')
    PLIST.write_bytes(plistlib.dumps(job(args.hour, args.market)))
    PLIST.chmod(0o600)
    subprocess.run(['plutil', '-lint', str(PLIST)], check=True)
    subprocess.run(['launchctl', 'bootstrap', DOMAIN, str(PLIST)], check=True)
    print('Scheduled. Check status and the update/error logs for the first result.')


if __name__ == '__main__':
    main()

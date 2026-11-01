import fcntl
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

root = Path.home() / 'Library/Application Support/Bing Wallpaper'
pictures = Path.home() / 'Pictures/Bing Wallpaper'
def fetch(url):
    # Honor the existing network environment; never retry by removing its proxy.
    command = ['/usr/bin/curl', '--fail', '--silent', '--show-error',
               '--location', '--retry', '2', '--connect-timeout', '10',
               '--max-time', '40']
    proxy = next((os.environ[k] for k in
                  ('HTTPS_PROXY', 'https_proxy', 'ALL_PROXY', 'all_proxy')
                  if os.environ.get(k)), None)
    if proxy:
        command += ['--proxy', proxy, '--noproxy', '']
    return subprocess.check_output(command + [url], timeout=150)


def main():
    root.mkdir(parents=True, exist_ok=True)
    pictures.mkdir(parents=True, exist_ok=True)
    with (root / 'update.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit(0)
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            state_path = root / 'current.json'
            state = json.loads(state_path.read_text()) if state_path.exists() else {}
            if '--force' not in sys.argv[1:] and state.get('checked_on') == today and Path(state.get('file', '')).is_file():
                print(today + ' already updated', flush=True)
                sys.exit(0)
            from urllib.parse import urlencode
            query = urlencode({'format': 'js', 'idx': 0, 'n': 1, 'mkt': os.environ.get('BING_WALLPAPER_MARKET', 'en-US')})
            metadata = json.loads(fetch('https://www.bing.com/HPImageArchive.aspx?' + query))['images'][0]
            if not metadata.get('wp'):
                raise RuntimeError('Bing image is not available as wallpaper')
            base = metadata['urlbase']
            if not base.startswith('/th?id=OHR.'):
                raise RuntimeError('Unexpected image URL')
            import re
            identifier = base[len('/th?id='):]
            if not re.fullmatch(r'OHR\.[A-Za-z0-9_-]+', identifier):
                raise RuntimeError('Unexpected image identifier')
            filename = identifier + '_UHD.jpg'
            target = pictures / filename
            if not target.exists():
                content = fetch('https://www.bing.com' + base + '_UHD.jpg')
                if not content.startswith(b'\xff\xd8\xff') or len(content) < 10000:
                    raise RuntimeError('Invalid wallpaper image')
                temporary = target.with_suffix('.download')
                temporary.write_bytes(content)
                temporary.replace(target)
            javascript = '''ObjC.import('AppKit');
    function run(argv) {
      var w=$.NSWorkspace.sharedWorkspace, screens=$.NSScreen.screens;
      var url=$.NSURL.fileURLWithPath(argv[0]);
      if (screens.count < 1) throw Error('No active screen');
      for (var i=0;i<screens.count;i++) {
        var err=Ref(), screen=screens.objectAtIndex(i);
        if (!w.setDesktopImageURLForScreenOptionsError(url,screen,$.NSDictionary.dictionary,err))
          throw Error('Wallpaper application failed');
      }
      return 'Wallpaper applied to '+screens.count+' screen(s)';
    }'''
            result = subprocess.check_output(['/usr/bin/osascript', '-l', 'JavaScript', '-e', javascript, str(target)], text=True, timeout=30)
            verify = "ObjC.import('AppKit'); var w=$.NSWorkspace.sharedWorkspace,s=$.NSScreen.screens,a=[]; for(var i=0;i<s.count;i++) a.push(ObjC.unwrap(w.desktopImageURLForScreen(s.objectAtIndex(i)).path)); JSON.stringify(a);"
            deadline = time.monotonic() + 10
            while True:
                applied = json.loads(subprocess.check_output(['/usr/bin/osascript', '-l', 'JavaScript', '-e', verify], text=True, timeout=10))
                if applied and all(p == str(target) for p in applied):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError('Wallpaper path verification failed')
                time.sleep(0.25)
            new_state = {'checked_on': today, 'file': str(target), 'image': metadata, 'result': result.strip()}
            temporary = state_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(new_state, ensure_ascii=True, indent=2))
            temporary.replace(state_path)
            print(today + ' ' + result.strip() + ' ' + filename, flush=True)
        except Exception as error:
            print(datetime.now().isoformat() + ' UPDATE FAILED: ' + (str(error) if isinstance(error, RuntimeError) else type(error).__name__), file=sys.stderr, flush=True)
            sys.exit(1)


if __name__ == '__main__':
    main()

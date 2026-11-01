# Bing Wallpaper Skill for macOS

A reusable AI-agent skill and lightweight daily Bing wallpaper updater. Uses Python's standard library, macOS native desktop APIs and a user LaunchAgent. No third-party Python dependencies or browser extensions.

This is an independent project, not Microsoft's official Bing Wallpaper app.

Follow [@51aitech on X](https://x.com/51aitech) for project updates.

## Install the skill

Clone this repository into your agent's skill directory under the name `bing-wallpaper`. For Codex:

```sh
git clone https://github.com/CCAIClaude/bing-wallpaper-skill.git ~/.codex/skills/bing-wallpaper
```

Start a new agent session, then ask: `Use $bing-wallpaper to set up daily Bing wallpaper.`

## Use without an agent

Requires macOS, an active logged-in desktop, Python 3, curl and osascript. The native wallpaper path was tested on macOS 15; other versions have not been verified.

```sh
python3 scripts/manage.py install --dry-run
python3 scripts/manage.py install --hour 9 --market en-US
python3 scripts/manage.py status
```

The script runs at login, daily at the selected local hour, and hourly for catch-up. After a successful update, same-day checks skip networking. It does not wake a sleeping Mac. First launch runs in the background; inspect the logs to verify success.

Refresh today manually:

```sh
python3 scripts/update.py --force
```

Disable daily updates:

```sh
python3 scripts/manage.py disable
```

Photos and state are retained. An existing installation is never overwritten automatically. To reinstall, first disable the old job and back up/move the old `update.py` and disabled plist before installing again.

## Proxy and region

The updater honors inherited proxy settings. If your network requires a proxy, export your own `HTTPS_PROXY` before installation. Its value is captured locally in the user-only plist, not in this repository. No proxy server or credentials are bundled. With a configured proxy, requests do not fall back to a direct connection.

`--market` selects Bing's regional feed, for example `en-US`, `en-GB` or `zh-CN`. For a manual invocation set `BING_WALLPAPER_MARKET` in the environment (default `en-US`). Daily images may include animals, architecture and events as well as landscapes.

## Local files

- `~/Library/Application Support/Bing Wallpaper/`: updater, state and logs
- `~/Pictures/Bing Wallpaper/`: downloaded UHD photographs
- `~/Library/LaunchAgents/io.github.bing-wallpaper.daily.plist`: current-user schedule

Downloads accumulate; there is no automatic photo deletion. Updates target current screens, and macOS Spaces may have separate wallpaper settings. The updater uses a file lock to prevent overlap and fresh-process polling to verify native wallpaper application. If a download fails, the existing wallpaper is retained. A failure during multi-screen application can leave some screens changed; inspect the error log.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Tests isolate local files, mock network/native commands, and check update state, proxy preservation and failure behavior. Live daily rollover is not simulated as a claim of real future execution.

## License and photography

Code: MIT, see [LICENSE](LICENSE). Bing photographs are not included and retain their original copyright and usage terms. Attribution is saved in local `current.json`. The code license does not grant rights to redistribute the photographs.

Sources: [Microsoft Bing Wallpaper](https://www.microsoft.com/en-us/bing/bing-wallpaper), [Bing daily image metadata](https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US).

---
name: bing-wallpaper
description: Set up, check, refresh or disable automatic daily Bing wallpaper on macOS using a lightweight Python updater and a user LaunchAgent.
---

# Bing Wallpaper

Use this skill for daily Bing photography on macOS. This is an independent local automation, not Microsoft's official wallpaper application. Requires Python 3, macOS curl and osascript; no pip dependencies.

## Inspect and preserve

Check the existing wallpaper script, `~/Library/LaunchAgents/*bing-wallpaper*.plist`, and `~/Library/Application Support/Bing Wallpaper/current.json` before installation. Reuse an existing working job. Do not create competing jobs or overwrite another installation. Preserve the user's network/proxy settings; never retry by removing their proxy. Never commit local configuration, logs, photos, credentials or current.json.

## Set up

Only create a recurring job when requested. From this skill directory run:

```sh
python3 scripts/manage.py install --dry-run
python3 scripts/manage.py install --hour 9 --market en-US
python3 scripts/manage.py status
```

The installer captures the current proxy environment into a private user plist. Determine the required network route before running it. Market and hour are user preferences; use en-US and 09:00 only when unspecified. The installer uses the current UID and Python executable. It refuses existing installations; inspect and back up before any intentional replacement.

For a one-time change, run `python3 scripts/update.py`. This writes photos and state but does not install a job. Use `--force` only when the user requests reapplying today's image.

## Verify

Read `current.json`, `update.log` and `error.log` under `~/Library/Application Support/Bing Wallpaper/`. Confirm the actual desktop image and job exit status (`launchctl list io.github.bing-wallpaper.daily`). The NSWorkspace setter can return before its getter updates; preserve the updater's fresh-process verification loop. A current successful run does not prove a future day rollover has occurred.

## Disable

Run `python3 scripts/manage.py disable`. It unloads only this job, moves its plist out of active use, and retains photos/state. Changing the wallpaper by itself does not disable scheduled updates.

## Behavior

The job runs at login, the selected hour, and hourly for catch-up; successful days skip network requests. The Mac must be awake with a logged-in desktop; it is not scheduled to wake. Downloads have bounded retries. Network failures retain the previous wallpaper. Images remain in `~/Pictures/Bing Wallpaper/`; no automatic cleanup is performed.

Bing's editorial feed can include animals, cities and events, not only landscapes. Preserve attribution and do not promise a scenery-only feed. See [README.md](README.md) for installation and licensing details.

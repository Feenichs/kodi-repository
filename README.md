# Feenichs Add-ons – Kodi repository

**Deutsch:** Kodi-Repository für meine Add-ons. Kodi installiert damit Updates automatisch.

| Add-on | ID |
|---|---|
| Spotify TV | `plugin.audio.spotify.tv` |
| YouTube für TV | `plugin.video.youtube.tv` |
| MediathekView TV | `plugin.video.mediathekview.tv` |
| Amazon VOD TV | `plugin.video.amazon.tv` |

Dazu die Module `script.module.amazoncaptcha`, `script.module.mechanicalsoup` und `script.module.pyautogui` aus
[Sandmann79s Repository](https://github.com/Sandmann79/xbmc), die Amazon VOD TV braucht und die nicht im
offiziellen Kodi-Repository sind.

### Installation

1. Kodi: *Einstellungen → System → Add-ons* → *Unbekannte Quellen* aktivieren.
2. *Einstellungen → Dateimanager → Quelle hinzufügen* → `https://feenichs.github.io/kodi-repository/` eingeben,
   Name z. B. „Feenichs“.
3. *Add-ons → Aus ZIP-Datei installieren* → „Feenichs“ → `repository.feenichs-….zip`.
4. *Add-ons → Aus Repository installieren* → *Feenichs Add-ons* → gewünschtes Add-on installieren.

Die ZIP des Repositorys gibt es auch direkt unter
[feenichs.github.io/kodi-repository](https://feenichs.github.io/kodi-repository/).

**Umstieg von einer per ZIP installierten älteren Version:** Die Add-ons haben seit dem Repository eigene IDs und
ersetzen die Originale nicht mehr. Wie man Anmeldung und Einstellungen übernimmt, steht im README des jeweiligen
Add-ons.

## English

Kodi repository for my add-ons, so that Kodi installs updates automatically. Install: enable *Unknown sources*, add
the source `https://feenichs.github.io/kodi-repository/` in the file manager, install
`repository.feenichs-….zip` from it via *Add-ons → Install from zip file*, then install the add-ons via
*Install from repository → Feenichs Add-ons*.

## Building

`python3 build.py` builds `dist/` from the release tags listed in `ADDONS` in `build.py` (the forks are expected
next to this folder) and the module zips of Sandmann79's repository. `python3 build.py --worktree` builds the
working trees instead, for testing. `dist/` is published as the branch `gh-pages`.

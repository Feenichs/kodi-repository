#!/usr/bin/env python3
"""
Builds the Kodi repository "Feenichs Add-ons" into dist/.

    python3 build.py              the add-ons at the git refs in ADDONS (release tags)
    python3 build.py --worktree   the add-ons as they are in their working trees, for testing

dist/ is what is published (GitHub Pages, branch gh-pages):

    addons.xml, addons.xml.md5       the add-ons and their versions
    <id>/<id>-<version>.zip(.sha256) one zip per add-on, only the latest version
    <id>/<assets>                    icon, fanart and screenshots, shown before installing
    repository.feenichs-<v>.zip      also at the top, to install the repository from a zip
    index.html                       a link to it, Kodi's file manager can browse it
"""

import argparse
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ElementTree
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.dirname(HERE)
DIST = os.path.join(HERE, "dist")
REPOSITORY_ID = "repository.feenichs"
PAGES_URL = "https://feenichs.github.io/kodi-repository/"

# git checkout, release ref, and the files of the add-on (None: all but the excluded)
ADDONS = [
    {
        "id": "plugin.audio.spotify.tv",
        "git": os.path.join(PROJECTS, "spotify_kodi", "repo"),
        "ref": "v2.0.1",
        "exclude": [".scripts"],
    },
    {
        "id": "plugin.video.youtube.tv",
        "git": os.path.join(PROJECTS, "youtube_kodi"),
        "ref": "v7.4.4.14",
        "include": ["addon.xml", "changelog.txt", "LICENSES", "README.md", "resources"],
    },
    {
        "id": "plugin.video.mediathekview.tv",
        "git": os.path.join(PROJECTS, "mediathekview_kodi", "repo"),
        "ref": "v2.0.0",
        "include": [
            "addon.py", "addon.xml", "contextMenu.py", "LICENSE.txt", "mvupdate", "mvupdate3",
            "README.md", "resources", "script.py", "service.py",
        ],
    },
    {
        "id": "plugin.video.amazon.tv",
        "git": os.path.join(PROJECTS, "amazon_kodi", "repo"),
        "ref": "v2.0.0",
        "include": [
            "addon.xml", "clearlogo.png", "default.py", "fanart.png", "icon.png", "LICENSE",
            "README.md", "resources", "script.py", "service.py",
        ],
    },
]

# Modules Amazon VOD TV needs that are not in the official Kodi repository, as
# released in Sandmann79's repository (MIT and BSD licensed)
SANDMANN79 = "https://raw.githubusercontent.com/Sandmann79/xbmc/master/packages-py3/"
EXTERNAL_ZIPS = [
    SANDMANN79 + "script.module.amazoncaptcha/script.module.amazoncaptcha-0.5.11+matrix.1.zip",
    SANDMANN79 + "script.module.mechanicalsoup/script.module.mechanicalsoup-1.0.0+matrix.1.zip",
    SANDMANN79 + "script.module.pyautogui/script.module.pyautogui-0.9.51+matrix.1.zip",
]


def git(repo: str, *args: str) -> bytes:
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout


def build_addon_zip(addon: dict, worktree: bool) -> bytes:
    repo = addon["git"]
    ref = addon["ref"]
    if worktree:
        # the working tree with its uncommitted changes of tracked files
        ref = git(repo, "stash", "create").decode().strip() or "HEAD"
    paths = addon.get("include") or ["."]
    paths += [f":!{path}" for path in addon.get("exclude", [])]
    return git(repo, "archive", "--format=zip", f"--prefix={addon['id']}/", ref, "--", *paths)


def repository_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        source = os.path.join(HERE, REPOSITORY_ID)
        for name in sorted(os.listdir(source)):
            archive.write(os.path.join(source, name), f"{REPOSITORY_ID}/{name}")
    return buffer.getvalue()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "kodi-repository-build"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def read_addon_xml(data: bytes) -> tuple:
    """(addon id, version, addon.xml text) of an add-on zip"""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [name for name in archive.namelist() if re.fullmatch(r"[^/]+/addon\.xml", name)]
        if len(names) != 1:
            raise ValueError(f"expected one addon.xml at the top, found {names}")
        text = archive.read(names[0]).decode("utf-8-sig")
    root = ElementTree.fromstring(text)
    if names[0].split("/")[0] != root.get("id"):
        raise ValueError(f"folder {names[0]} does not match the id {root.get('id')}")
    return root.get("id"), root.get("version"), text


def extract_assets(data: bytes, addon_id: str, addon_xml: str) -> None:
    root = ElementTree.fromstring(addon_xml)
    assets = [element.text for element in root.iter() if element.tag in (
        "icon", "fanart", "clearlogo", "screenshot", "banner", "poster") and element.text]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for asset in assets:
            name = f"{addon_id}/{asset}"
            if name not in archive.namelist():
                print(f"  missing asset {asset}", file=sys.stderr)
                continue
            target = os.path.join(DIST, addon_id, asset)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as file:
                file.write(archive.read(name))


def add_to_dist(data: bytes) -> str:
    addon_id, version, addon_xml = read_addon_xml(data)
    folder = os.path.join(DIST, addon_id)
    os.makedirs(folder, exist_ok=True)
    zip_path = os.path.join(folder, f"{addon_id}-{version}.zip")
    with open(zip_path, "wb") as file:
        file.write(data)
    with open(zip_path + ".sha256", "w") as file:
        file.write(hashlib.sha256(data).hexdigest())
    extract_assets(data, addon_id, addon_xml)
    print(f"{addon_id} {version} ({len(data) / 1e6:.1f} MB)")
    # without the XML declaration, addons.xml has one for all
    return re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", addon_xml).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--worktree", action="store_true", help="use the working trees")
    args = parser.parse_args()

    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    entries = []
    repo_zip = repository_zip()
    entries.append(add_to_dist(repo_zip))
    for addon in ADDONS:
        entries.append(add_to_dist(build_addon_zip(addon, args.worktree)))
    for url in EXTERNAL_ZIPS:
        entries.append(add_to_dist(download(url)))

    addons_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
        + "\n".join(entries)
        + "\n</addons>\n"
    ).encode("utf-8")
    ElementTree.fromstring(addons_xml)  # well-formed
    with open(os.path.join(DIST, "addons.xml"), "wb") as file:
        file.write(addons_xml)
    with open(os.path.join(DIST, "addons.xml.md5"), "w") as file:
        file.write(hashlib.md5(addons_xml).hexdigest())

    # to install the repository itself, also browsable in Kodi's file manager
    _, version, _ = read_addon_xml(repo_zip)
    repo_zip_name = f"{REPOSITORY_ID}-{version}.zip"
    shutil.copy(os.path.join(DIST, REPOSITORY_ID, repo_zip_name), os.path.join(DIST, repo_zip_name))
    with open(os.path.join(DIST, "index.html"), "w") as file:
        file.write(
            "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"><title>Feenichs Add-ons</title></head>\n"
            f"<body><a href=\"{repo_zip_name}\">{repo_zip_name}</a></body></html>\n"
        )
    # GitHub Pages must not run Jekyll, it would hide nothing here but is slow
    open(os.path.join(DIST, ".nojekyll"), "w").close()
    print(f"dist/ ready, repository zip {repo_zip_name}")


if __name__ == "__main__":
    main()

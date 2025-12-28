#!/usr/bin/env python3
"""
Fetches the remote assets this app normally downloads at runtime and saves
them under public/offline-data so Electron builds can run fully offline.

Usage:
  python scripts/fetch_offline_data.py --versions 1.21.11 1.21.6

By default it downloads:
- mcmeta summary payloads (versions list, registries, blocks, item components, sounds)
- summary assets for the latest version to satisfy dynamic latest lookups
- atlas metadata and atlas sprite
- base language files (en_us + deprecated) for each requested version
- vanilla mcdoc symbols
- technical changes, bugfixes per version, and what's new feed

You can extend the payloads by adding more endpoints to the FETCH_MAP below.
"""

import argparse
import json
import pathlib
import sys
import urllib.request
from typing import Iterable, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public" / "offline-data"

MCMETA_BASE = "https://raw.githubusercontent.com/misode/mcmeta"
VANILLA_MCDOC_BASE = "https://raw.githubusercontent.com/SpyglassMC/vanilla-mcdoc"
TECHNICAL_CHANGES_BASE = "https://raw.githubusercontent.com/misode/technical-changes"
MCFIXES_BASE = "https://raw.githubusercontent.com/misode/mcfixes"
WHATS_NEW_URL = "https://whats-new.misode.workers.dev"


def fetch(url: str, dest: pathlib.Path) -> None:
	dest.parent.mkdir(parents=True, exist_ok=True)
	with urllib.request.urlopen(url) as response:
		data = response.read()
	dest.write_bytes(data)
	print(f"[saved] {dest.relative_to(ROOT)}")


def build_mcmeta_paths(version: str) -> List[Tuple[str, pathlib.Path]]:
	pairs: List[Tuple[str, pathlib.Path]] = []
	summary_root = PUBLIC / "mcmeta" / f"{version}-summary"
	assets_root = PUBLIC / "mcmeta" / f"{version}-assets"
	atlas_root = PUBLIC / "mcmeta" / f"{version}-atlas"

	summary_segments = [
		("versions/data.min.json", summary_root / "versions/data.min.json"),
		("registries/data.min.json", summary_root / "registries/data.min.json"),
		("blocks/data.min.json", summary_root / "blocks/data.min.json"),
		("item_components/data.min.json", summary_root / "item_components/data.min.json"),
		("sounds/data.min.json", summary_root / "sounds/data.min.json"),
		("block_definition/data.min.json", summary_root / "block_definition/data.min.json"),
		("model/data.min.json", summary_root / "model/data.min.json"),
		("item_definition/data.min.json", summary_root / "item_definition/data.min.json"),
	]

	asset_segments = [
		("assets/minecraft/lang/en_us.json", assets_root / "assets/minecraft/lang/en_us.json"),
		("assets/minecraft/lang/deprecated.json", assets_root / "assets/minecraft/lang/deprecated.json"),
	]

	atlas_segments = [
		("all/data.min.json", atlas_root / "all/data.min.json"),
		("all/atlas.png", atlas_root / "all/atlas.png"),
	]

	for rel, dest in summary_segments:
		pairs.append((f"{MCMETA_BASE}/{version}-summary/{rel}", dest))
	for rel, dest in asset_segments:
		pairs.append((f"{MCMETA_BASE}/{version}-assets/{rel}", dest))
	for rel, dest in atlas_segments:
		pairs.append((f"{MCMETA_BASE}/{version}-atlas/{rel}", dest))
	return pairs


def build_dynamic_latest(version: str) -> List[Tuple[str, pathlib.Path]]:
	"""Mirror the latest version under mcmeta/summary to satisfy dynamic lookups."""
	target_root = PUBLIC / "mcmeta" / "summary"
	segments = [
		("versions/data.min.json", target_root / "versions/data.min.json"),
		("registries/data.min.json", target_root / "registries/data.min.json"),
		("blocks/data.min.json", target_root / "blocks/data.min.json"),
		("item_components/data.min.json", target_root / "item_components/data.min.json"),
		("sounds/data.min.json", target_root / "sounds/data.min.json"),
		("block_definition/data.min.json", target_root / "block_definition/data.min.json"),
		("model/data.min.json", target_root / "model/data.min.json"),
		("item_definition/data.min.json", target_root / "item_definition/data.min.json"),
		("assets/minecraft/lang/en_us.json", PUBLIC / "mcmeta" / "assets" / "assets/minecraft/lang/en_us.json"),
		("assets/minecraft/lang/deprecated.json", PUBLIC / "mcmeta" / "assets" / "assets/minecraft/lang/deprecated.json"),
		("all/data.min.json", PUBLIC / "mcmeta" / "atlas" / "all/data.min.json"),
		("all/atlas.png", PUBLIC / "mcmeta" / "atlas" / "all/atlas.png"),
	]
	return [
		(f"{MCMETA_BASE}/{version}-summary/{rel}", dest) if "all/" not in rel and not rel.startswith("assets/") else
		(f"{MCMETA_BASE}/{version}-assets/{rel}", dest) if rel.startswith("assets/") else
		(f"{MCMETA_BASE}/{version}-atlas/{rel}", dest)
		for rel, dest in segments
	]


def build_global_payloads(versions: Iterable[str]) -> List[Tuple[str, pathlib.Path]]:
	pairs: List[Tuple[str, pathlib.Path]] = [
		(f"{VANILLA_MCDOC_BASE}/generated/symbols.json", PUBLIC / "vanilla-mcdoc/generated/symbols.json"),
		(f"{TECHNICAL_CHANGES_BASE}/generated/changes.json", PUBLIC / "technical-changes/generated/changes.json"),
		(WHATS_NEW_URL, PUBLIC / "whats-new/index.json"),
	]
	for version in versions:
		pairs.append((
			f"{MCFIXES_BASE}/main/versions/{version}.json",
			PUBLIC / "mcfixes/main/versions" / f"{version}.json"
		))
	return pairs


def write_manifest(versions: List[str]) -> None:
	manifest = {
		"versions": versions,
	}
	manifest_path = PUBLIC / "manifest.json"
	manifest_path.parent.mkdir(parents=True, exist_ok=True)
	manifest_path.write_text(json.dumps(manifest, indent=2))
	print(f"[saved] {manifest_path.relative_to(ROOT)}")


def main(argv: List[str]) -> int:
	parser = argparse.ArgumentParser(description="Fetch offline data for DatapackHelper.")
	parser.add_argument("--versions", nargs="+", default=["1.21.11"],
	                    help="Version identifiers to pre-download (e.g. 1.21.11 1.21.6).")
	parser.add_argument("--latest", default=None,
	                    help="Version to mirror under mcmeta/summary for dynamic latest lookups (default: first version).")
	args = parser.parse_args(argv)

	versions = args.versions
	latest = args.latest or versions[0]

	all_tasks: List[Tuple[str, pathlib.Path]] = []
	all_tasks.extend(build_dynamic_latest(latest))
	for v in versions:
		all_tasks.extend(build_mcmeta_paths(v))
	all_tasks.extend(build_global_payloads(versions))

	for url, dest in all_tasks:
		try:
			fetch(url, dest)
		except Exception as exc:
			print(f"[warn] failed to fetch {url}: {exc}", file=sys.stderr)

	write_manifest(versions)
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

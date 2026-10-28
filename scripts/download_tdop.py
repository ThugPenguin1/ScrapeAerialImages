#!/usr/bin/env python3
"""Download official HKMS TDOP tiles by clicking each product page's Download control.

The default mode is a dry run. This script does not solve or bypass CAPTCHAs.
If a human verification page appears, it pauses in the visible browser for a person
or stops in headless mode.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

BASE_URL = "https://open.hkmapservice.gov.hk/OpenData/productView"
PRODUCT = "TDOP"
PRODUCT_FORMAT = "TIFF"
LOCALE = "en"
APPROX_TILE_MB = 520

# Edit this list to control the default selection. When neither --pdf nor --sheet
# is supplied, the downloader reads these sheet IDs in order. These 192 IDs come
# from the supplied December 2024–January 2025 TDOP specification PDF.
TDOP_SHEETS = [
    "1-SE-D", "2-NE-C", "2-NE-D", "2-SE-A", "2-SE-B", "2-SE-C",
    "2-SE-D", "2-SW-B", "2-SW-C", "2-SW-D", "3-NE-A", "3-NE-B",
    "3-NE-C", "3-NE-D", "3-NW-A", "3-NW-B", "3-NW-C", "3-NW-D",
    "3-SE-A", "3-SE-B", "3-SE-C", "3-SE-D", "3-SW-A", "3-SW-B",
    "3-SW-C", "3-SW-D", "4-NW-A", "4-NW-B", "4-NW-C", "4-NW-D",
    "4-SE-A", "4-SE-C", "4-SE-D", "4-SW-A", "4-SW-B", "4-SW-C",
    "4-SW-D", "5-NE-B", "5-NE-C", "5-NE-D", "5-SE-A", "5-SE-B",
    "5-SE-C", "5-SE-D", "5-SW-B", "5-SW-D", "6-NE-A", "6-NE-B",
    "6-NE-C", "6-NE-D", "6-NW-A", "6-NW-B", "6-NW-C", "6-NW-D",
    "6-SE-A", "6-SE-B", "6-SE-C", "6-SE-D", "6-SW-A", "6-SW-B",
    "6-SW-C", "6-SW-D", "7-NE-A", "7-NE-B", "7-NE-C", "7-NE-D",
    "7-NW-A", "7-NW-B", "7-NW-C", "7-NW-D", "7-SE-A", "7-SE-B",
    "7-SE-C", "7-SE-D", "7-SW-A", "7-SW-B", "7-SW-C", "7-SW-D",
    "8-NE-A", "8-NE-B", "8-NE-C", "8-NE-D", "8-NW-A", "8-NW-B",
    "8-NW-C", "8-NW-D", "8-SE-A", "8-SE-B", "8-SE-C", "8-SE-D",
    "8-SW-A", "8-SW-B", "8-SW-C", "8-SW-D", "9-NE-A", "9-NE-B",
    "9-NE-C", "9-NE-D", "9-NW-B", "9-NW-D", "9-SE-A", "9-SE-B",
    "9-SE-C", "9-SE-D", "9-SW-A", "9-SW-B", "9-SW-C", "9-SW-D",
    "10-NE-A", "10-NE-B", "10-NE-C", "10-NE-D", "10-NW-A", "10-NW-B",
    "10-NW-C", "10-NW-D", "10-SE-A", "10-SE-B", "10-SE-C", "10-SW-A",
    "10-SW-B", "10-SW-C", "10-SW-D", "11-NE-A", "11-NE-B", "11-NE-C",
    "11-NE-D", "11-NW-A", "11-NW-B", "11-NW-C", "11-NW-D", "11-SE-A",
    "11-SE-B", "11-SE-C", "11-SE-D", "11-SW-A", "11-SW-B", "11-SW-C",
    "11-SW-D", "12-NE-A", "12-NE-B", "12-NE-C", "12-NE-D", "12-NW-A",
    "12-NW-B", "12-NW-C", "12-NW-D", "12-SE-A", "12-SE-C", "12-SW-A",
    "12-SW-B", "12-SW-C", "12-SW-D", "13-NE-A", "13-NE-B", "13-NE-C",
    "13-NE-D", "13-NW-A", "13-NW-B", "13-NW-C", "13-NW-D", "13-SE-A",
    "13-SE-C", "13-SW-B", "14-NE-A", "14-NE-B", "14-NE-C", "14-NE-D",
    "14-NW-A", "14-NW-B", "14-NW-C", "14-NW-D", "14-SE-B", "14-SW-A",
    "15-NE-A", "15-NE-B", "15-NE-C", "15-NE-D", "15-NW-A", "15-NW-B",
    "15-NW-C", "15-NW-D", "15-SE-B", "15-SE-D", "15-SW-A", "16-NW-A",
    "16-SW-A", "16-SW-B", "16-SW-C", "17-NW-A", "17-NW-C", "17-SW-C",
]

SHEET_RE = re.compile(r"^(?P<map_no>\d{1,2})-(?P<quadrant>NE|NW|SE|SW)-(?P<quarter>[A-D])$", re.I)
# In the supplied TDOP specification, the file-name/extent table has one row per
# available tile: sheet number, file stem, then four HK80 extent coordinates.
PDF_ROW_RE = re.compile(
    r"^\s*(?P<sheet>\d{1,2}-(?:NE|NW|SE|SW)-[A-D])\s+"
    r"(?P<stem>tdop[\w-]+)\s+"
    r"(?:-?\d+\s+){3}-?\d+\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Tile:
    sheet_no: str
    file_stem: str = ""

    @property
    def query_sheet_name(self) -> str:
        # The PDF uses e.g. 1-SE-D; the productView URL uses T1-SE-D.
        return f"T{self.sheet_no}"


def normalize_sheet(value: str) -> str:
    """Normalize a PDF tile number or productView name such as T1-SE-D."""
    sheet = value.strip().upper()
    if sheet.startswith("T"):
        sheet = sheet[1:]
    if not SHEET_RE.fullmatch(sheet):
        raise ValueError(
            f"Invalid TDOP sheet number {value!r}; expected a value like 1-SE-D or T1-SE-D"
        )
    return sheet


def build_product_url(sheet_no: str) -> str:
    sheet = normalize_sheet(sheet_no)
    query = urlencode(
        {
            "productName": PRODUCT,
            "sheetName": f"T{sheet}",
            "productFormat": PRODUCT_FORMAT,
            "locale": LOCALE,
        }
    )
    return f"{BASE_URL}?{query}"


def parse_tiles_from_pdf(pdf_path: Path) -> list[Tile]:
    """Read TDOP sheet numbers and file stems from the specification PDF."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF parsing requires pypdf. Install dependencies with: pip install -r requirements.txt"
        ) from exc

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    full_text = "\n".join(pages)
    marker = "Table of File Name and Tile Extent"
    marker_at = full_text.lower().find(marker.lower())
    table_text = full_text[marker_at:] if marker_at >= 0 else full_text

    tiles: list[Tile] = []
    seen: set[str] = set()
    for line in table_text.splitlines():
        match = PDF_ROW_RE.match(line)
        if not match:
            continue
        sheet = normalize_sheet(match.group("sheet"))
        if sheet in seen:
            continue
        seen.add(sheet)
        tiles.append(Tile(sheet_no=sheet, file_stem=match.group("stem").lower()))

    if not tiles:
        raise ValueError(
            "No TDOP tile rows found in the PDF. Expected the 'Table of File Name and Tile Extent' "
            "with rows such as '1-SE-D tdop1sed20250009 ...'."
        )
    return tiles


def select_tiles(
    pdf_tiles: list[Tile] | None,
    requested_sheets: Iterable[str] | None,
    limit: int | None,
) -> list[Tile]:
    requested_values = list(requested_sheets or [])
    if pdf_tiles is None and not requested_values:
        requested_values = TDOP_SHEETS
    requested = [normalize_sheet(s) for s in requested_values]
    if pdf_tiles is None:
        # De-duplicate while preserving the array/CLI order.
        tiles = []
        seen: set[str] = set()
        for sheet in requested:
            if sheet not in seen:
                tiles.append(Tile(sheet_no=sheet))
                seen.add(sheet)
    elif requested:
        by_sheet = {tile.sheet_no: tile for tile in pdf_tiles}
        missing = [sheet for sheet in requested if sheet not in by_sheet]
        if missing:
            raise ValueError(
                "These requested sheet(s) are not in the supplied PDF: " + ", ".join(missing)
            )
        # Keep the user's requested order, while removing repeated IDs.
        tiles = []
        seen: set[str] = set()
        for sheet in requested:
            if sheet not in seen:
                tiles.append(by_sheet[sheet])
                seen.add(sheet)
    else:
        tiles = list(pdf_tiles)

    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be at least 1")
        tiles = tiles[:limit]
    if not tiles:
        raise ValueError("No sheets selected")
    return tiles


def append_manifest(manifest: Path, row: dict[str, str]) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "recorded_utc",
        "sheet_no",
        "pdf_file_stem",
        "query_sheet_name",
        "url",
        "status",
        "filename",
        "bytes",
        "message",
    ]
    new_file = not manifest.exists() or manifest.stat().st_size == 0
    with manifest.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        if new_file:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})
        stream.flush()


def completed_sheets(manifest: Path, output_dir: Path) -> set[str]:
    """Return previously verified downloads that still exist at the recorded size."""
    if not manifest.is_file():
        return set()
    latest: dict[str, dict[str, str]] = {}
    with manifest.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row.get("sheet_no"):
                latest[row["sheet_no"]] = row

    completed: set[str] = set()
    for sheet, row in latest.items():
        if row.get("status") != "downloaded" or not row.get("filename"):
            continue
        path = output_dir / Path(row["filename"]).name
        if not path.is_file():
            continue
        try:
            expected_bytes = int(row.get("bytes") or "0")
        except ValueError:
            continue
        if expected_bytes > 0 and path.stat().st_size == expected_bytes:
            completed.add(sheet)
    return completed


def safe_filename(value: str, fallback: str) -> str:
    # Keep only the basename so a server-provided name cannot escape output_dir.
    name = Path(value.replace("\\", "/")).name.strip()
    if not name or name in {".", ".."}:
        name = fallback
    return name


def looks_like_html(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            head = stream.read(512).lstrip().lower()
    except OSError:
        return False
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


async def challenge_present(page) -> bool:
    body = ""
    try:
        body = await page.locator("body").inner_text(timeout=5_000)
    except Exception:
        pass
    if re.search(
        r"captcha|recaptcha|verify you are human|i am not a robot|human verification",
        body,
        re.IGNORECASE,
    ):
        return True
    for selector in (
        'iframe[src*="recaptcha"]',
        'iframe[title*="recaptcha" i]',
        ".g-recaptcha",
        "[data-sitekey]",
    ):
        try:
            if await page.locator(selector).count():
                return True
        except Exception:
            continue
    return False


async def download_tiles(args: argparse.Namespace, tiles: list[Tile]) -> int:
    try:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Browser downloads require Playwright. Install dependencies with: pip install -r requirements.txt"
        ) from exc

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.out_dir / "manifest.csv"
    done = completed_sheets(manifest, args.out_dir)
    total_bytes_estimate = len(tiles) * APPROX_TILE_MB * 1_000_000
    free_bytes = shutil.disk_usage(args.out_dir).free
    if free_bytes < APPROX_TILE_MB * 1_000_000:
        raise RuntimeError(
            f"Less than one approximate tile ({APPROX_TILE_MB} MB) of free disk space is available."
        )
    if free_bytes < total_bytes_estimate:
        print(
            f"Warning: estimated selection is {total_bytes_estimate / 1e9:.1f} GB, "
            f"but this filesystem has {free_bytes / 1e9:.1f} GB free.",
            file=sys.stderr,
        )

    failures = 0
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=args.headless)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        page.set_default_navigation_timeout(args.navigation_timeout * 1000)
        page.set_default_timeout(args.navigation_timeout * 1000)

        for position, tile in enumerate(tiles, start=1):
            if tile.sheet_no in done:
                print(f"[{position}/{len(tiles)}] SKIP {tile.sheet_no}: already verified in manifest")
                continue

            url = build_product_url(tile.sheet_no)
            record = {
                "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "sheet_no": tile.sheet_no,
                "pdf_file_stem": tile.file_stem,
                "query_sheet_name": tile.query_sheet_name,
                "url": url,
            }
            print(f"[{position}/{len(tiles)}] Opening {tile.sheet_no}: {url}")
            try:
                response = await page.goto(url, wait_until="domcontentloaded")
                if response is not None and response.status >= 400:
                    raise RuntimeError(f"Product page returned HTTP {response.status}")

                if await challenge_present(page):
                    if args.headless:
                        raise RuntimeError(
                            "A human-verification challenge appeared. This script will not bypass it; "
                            "rerun without --headless and complete it manually if authorized."
                        )
                    print(
                        "Human verification detected. Complete it in the visible browser; "
                        "the script will continue only after you confirm."
                    )
                    await asyncio.to_thread(
                        input, "After completing the official verification, press Enter here... "
                    )
                    if await challenge_present(page):
                        raise RuntimeError("Verification is still present; stopping this tile.")

                download_link = page.get_by_role("link", name=re.compile(r"^\s*download\s*$", re.I))
                download_button = page.get_by_role("button", name=re.compile(r"^\s*download\s*$", re.I))
                target = download_link if await download_link.count() else download_button
                if not await target.count():
                    # Fallback for a non-semantic clickable element; exact text avoids
                    # clicking the separate "TDOP Resource File (TIFF)" link.
                    target = page.get_by_text("Download", exact=True)
                if not await target.count():
                    raise RuntimeError("Could not find the product's exact 'Download' control.")

                async with page.expect_download(timeout=args.download_timeout * 1000) as download_event:
                    await target.first.click()
                download = await download_event.value
                suggested = download.suggested_filename or ""
                fallback = f"{tile.file_stem or ('tdop_' + tile.sheet_no.lower().replace('-', ''))}.tif"
                filename = safe_filename(suggested, fallback)
                destination = args.out_dir / filename
                if destination.exists():
                    destination = args.out_dir / f"{tile.sheet_no.replace('-', '_')}_{filename}"
                await download.save_as(str(destination))
                failure = await download.failure()
                if failure:
                    raise RuntimeError(f"Browser download failed: {failure}")
                if destination.stat().st_size == 0:
                    raise RuntimeError("Downloaded file is empty")
                if looks_like_html(destination):
                    diagnostic = destination.with_suffix(destination.suffix + ".error.html")
                    destination.replace(diagnostic)
                    raise RuntimeError(
                        f"The server returned an HTML page instead of a TIFF/download; saved as {diagnostic.name}. "
                        "Check the visible page and official access requirements."
                    )

                record.update(
                    {
                        "status": "downloaded",
                        "filename": destination.name,
                        "bytes": str(destination.stat().st_size),
                        "message": "",
                    }
                )
                append_manifest(manifest, record)
                done.add(tile.sheet_no)
                print(
                    f"    Saved {destination} ({destination.stat().st_size / 1_000_000:.1f} MB)"
                )
            except PlaywrightTimeoutError as exc:
                failures += 1
                record.update({"status": "failed", "message": f"Playwright timeout: {exc}"})
                append_manifest(manifest, record)
                print(f"    FAILED {tile.sheet_no}: browser/download timed out", file=sys.stderr)
            except Exception as exc:
                failures += 1
                record.update({"status": "failed", "message": str(exc)[:1000]})
                append_manifest(manifest, record)
                print(f"    FAILED {tile.sheet_no}: {exc}", file=sys.stderr)
                if re.search(
                    r"HTTP (403|429)|verification|CAPTCHA|captcha|access denied|could not find the product's exact",
                    str(exc),
                    re.I,
                ):
                    print("Stopping to avoid retrying a blocked or challenged endpoint.", file=sys.stderr)
                    break

            if position < len(tiles):
                await asyncio.sleep(args.delay)

        await context.close()
        await browser.close()

    print(f"Finished: {len(done)} verified sheet(s); {failures} failed attempt(s).")
    print(f"Manifest: {manifest}")
    return 1 if failures else 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read TDOP sheets from the built-in array or a LandsD PDF, then click official download buttons."
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Optional TDOP specification PDF; without it, use TDOP_SHEETS or explicit --sheet values",
    )
    parser.add_argument(
        "--sheet",
        action="append",
        help="Only process this sheet (repeatable), e.g. 1-SE-D; accepts T1-SE-D too",
    )
    parser.add_argument("--limit", type=int, help="Limit the selected tiles to the first N")
    parser.add_argument("--list-sheets", action="store_true", help="Print selected sheet IDs and exit")
    download_mode = parser.add_mutually_exclusive_group()
    download_mode.add_argument("--download", action="store_true", help="Actually open the browser and click Download")
    download_mode.add_argument("--dry-run", action="store_true", help="Only print URLs; this is the default")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt for a real download run")
    parser.add_argument("--headless", action="store_true", help="Run Chromium headlessly (no manual challenge handling)")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path.home() / "Downloads" / "HKMS_TDOP",
        help="Output directory (default: ~/Downloads/HKMS_TDOP; kept outside this repository)",
    )
    parser.add_argument("--delay", type=float, default=2.0, help="Pause between tiles in seconds (default: 2)")
    parser.add_argument("--navigation-timeout", type=int, default=120, help="Page/control timeout in seconds")
    parser.add_argument("--download-timeout", type=int, default=1800, help="Download-start timeout in seconds")
    return parser


def main() -> int:
    parser = make_parser()
    args = parser.parse_args()

    if args.delay < 0:
        parser.error("--delay cannot be negative")

    try:
        pdf_tiles = parse_tiles_from_pdf(args.pdf) if args.pdf else None
        tiles = select_tiles(pdf_tiles, args.sheet, args.limit)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Selected {len(tiles)} TDOP tile(s). Approximate transfer size: "
          f"{len(tiles) * APPROX_TILE_MB / 1000:.2f} GB.")
    for tile in tiles:
        print(f"  {tile.sheet_no:10} -> {build_product_url(tile.sheet_no)}")

    if args.list_sheets:
        return 0
    if not args.download:
        print("Dry run only. Add --download to open the official pages and click Download.")
        return 0

    if not args.yes:
        if not sys.stdin.isatty():
            parser.error("real downloads require an interactive confirmation or --yes")
        expected_gb = len(tiles) * APPROX_TILE_MB / 1000
        confirmation = input(
            f"This will download {len(tiles)} tile(s), approximately {expected_gb:.2f} GB. "
            "Type DOWNLOAD to continue: "
        )
        if confirmation.strip() != "DOWNLOAD":
            print("Cancelled.")
            return 0

    try:
        return asyncio.run(download_tiles(args, tiles))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

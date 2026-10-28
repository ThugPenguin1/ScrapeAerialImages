# ScrapeAerialImages

## Download official TDOP tiles by sheet number

`scripts/download_tdop.py` reads the **Table of File Name and Tile Extent** in the LandsD TDOP specification PDF, builds the HKMS OpenData `productView` URL for each sheet (the PDF's `1-SE-D` becomes the URL's `T1-SE-D`), opens the page in Chromium, and clicks its exact **Download** control.

The script is deliberately **dry-run by default**. It downloads serially, waits between tiles, records results in `manifest.csv`, and stores files outside the repository by default. The 192-tile specification represents roughly 100 GB at about 520 MB per tile, so select only the sheets you need for a pilot first.

### Install

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Preview the sheet list / URLs (no download)

```bash
python scripts/download_tdop.py \
  --pdf "/path/to/Technical Specifications of TDOP (Dec 2024 - Jan 2025).pdf" \
  --list-sheets

python scripts/download_tdop.py \
  --pdf "/path/to/Technical Specifications of TDOP (Dec 2024 - Jan 2025).pdf" \
  --sheet 1-SE-D
```

The second command prints the URL and remains a dry run. To download just the example tile:

```bash
python scripts/download_tdop.py \
  --pdf "/path/to/Technical Specifications of TDOP (Dec 2024 - Jan 2025).pdf" \
  --sheet 1-SE-D \
  --download
```

A real download asks you to type `DOWNLOAD`. The file is saved under `~/Downloads/HKMS_TDOP` unless `--out-dir` is provided. Re-running the script skips tiles already recorded as downloaded and still present at the expected size.

To download all sheets in the PDF, omit `--sheet` and use `--download`; review the selected sheet list and disk space before confirming. `--limit N` can cap a pilot run. `--yes` skips the interactive confirmation and should be used only when the full scope and storage are intentional.

### Verification and limits

- The script only visits the official OpenData `productView` pages and clicks **Download**; it does not reverse-engineer a private endpoint.
- It does **not** solve or bypass CAPTCHA. If a human-verification challenge appears, it pauses for manual completion in the visible browser; if blocked or challenged in headless mode, it stops.
- It saves a CSV manifest and does not put the imagery in Git.
- The PDF parser expects the TDOP tile/file-name table. If LandsD changes the PDF layout, check `--list-sheets` before downloading.

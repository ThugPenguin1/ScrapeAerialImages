# ScrapeAerialImages

## Download official TDOP tiles by sheet number

`scripts/download_tdop.py` builds the HKMS OpenData `productView` URL for each sheet (for example, PDF sheet `1-SE-D` becomes URL parameter `T1-SE-D`), opens the official page in Chromium, and clicks its **Download** control.

The script contains an editable `TDOP_SHEETS` list near the top. By default, it uses this list when run without `--pdf` or `--sheet`. The list contains the 192 sheet IDs from the supplied December 2024–January 2025 TDOP specification. You can edit the array directly to choose the default set. Alternatively, pass a PDF to read its tile table, or use one or more `--sheet` arguments for a custom selection.

The script is deliberately **dry-run by default**. It downloads serially, waits between tiles, records results in `manifest.csv`, and stores files outside the repository by default. The full 192-tile set is roughly 100 GB at about 520 MB per tile, so select only the sheets you need for a pilot first.

### Install

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Preview the built-in array (no download)

```bash
python scripts/download_tdop.py --list-sheets
```

The default run uses `TDOP_SHEETS` from the script. To customize it, edit that list in `scripts/download_tdop.py`. You can also select specific sheets directly; repeat `--sheet` for each one:

```bash
python scripts/download_tdop.py \
  --sheet 1-SE-D \
  --sheet 2-NE-C \
  --dry-run
```

To read the list from a TDOP specification PDF instead, pass its path. With `--pdf` and no `--sheet`, all sheets in that PDF are selected; `--sheet` can limit that selection:

```bash
python scripts/download_tdop.py \
  --pdf "/path/to/Technical Specifications of TDOP (Dec 2024 - Jan 2025).pdf" \
  --list-sheets
```

### Download

A real download asks you to type `DOWNLOAD`. For example, to download just the example tile using the built-in list:

```bash
python scripts/download_tdop.py --sheet 1-SE-D --download
```

To download the default array, use `--download` without `--pdf` or `--sheet`. Review the selected sheets and disk-space estimate before confirming. `--limit N` can cap a pilot run. The file is saved under `~/Downloads/HKMS_TDOP` unless `--out-dir` is provided. Re-running the script skips tiles already recorded as downloaded and still present at the expected size. `--yes` skips the interactive confirmation and should only be used when the scope and storage are intentional.

### Verification and limits

- The script only visits the official OpenData `productView` pages and clicks **Download**; it does not reverse-engineer a private endpoint.
- It does **not** solve or bypass CAPTCHA. If a human-verification challenge appears, it pauses for manual completion in the visible browser; if blocked or challenged in headless mode, it stops.
- It saves a CSV manifest and does not put the imagery in Git.
- The PDF parser expects the TDOP tile/file-name table. If LandsD changes the PDF layout, check `--list-sheets` before downloading.

# Authorized HKMS aerial-imagery acquisition plan

**Status:** planning only — no downloads or automated requests have been run.

## Recommendation

Do not begin with a crawler that walks every page or harvests every map tile. First define what “all images” means, then use Lands Department (LandsD) catalogues and an approved data-delivery route to build a complete inventory and download manifest. A manifest-driven downloader is easier to resume, audit, and prove complete than a browser-clicking scraper.

Keep three different goals separate:

1. **Original aerial photographs** — DAP, DAP-UE, or DAP-L0 product files. This is the right path for an image archive.
2. **A georeferenced, near-seamless map layer** — orthophoto products such as DOP/TDOP. Prefer these over stitching raw aerial photographs.
3. **A lookalike web map** — use LandsD’s documented imagery map-tile API under its terms. Tiles are rendered map tiles, not a bulk replacement for original photo files.

If “all images” literally means the website’s banners, logos, and sample pictures, that is a separate, much smaller static-asset crawl and should not be mixed with geospatial product downloads.

## 1. Lock the scope and permission before downloading

Record the approval in a project file that does **not** contain the queue key. Confirm with the granting party:

- Which products are covered: DAP-L0, full-resolution DAP, DAP-UE products (RGBI/RGB/CIR), orthophotos, map tiles, or a specified subset.
- Covered years, territory/area of interest, flight/photo IDs, and whether “all” means all available records or only records in the approved queue.
- Permitted purpose, storage location, transformations (for example, making Cloud-Optimized GeoTIFF derivatives), display, sharing, and redistribution.
- The approved download endpoint or bulk-transfer method, authentication procedure, request/concurrency limits, and whether automated retrieval is explicitly permitted.

Do not assume permission for one product or queue also applies to every product, tile service, or onward redistribution. Retain the approval and applicable licence/terms with the dataset.

## 2. Build an authoritative inventory

Use the **Aerial Photo Flight Index** as the starting catalogue. LandsD publishes it in spreadsheet and KML/KMZ forms; the georeferenced KML/KMZ includes photo and flight information such as photo number, coverage, flight date, and flying height. Normalize the records into a manifest and deduplicate on the LandsD photo/product identifier, not on filename alone.

Recommended manifest fields:

- product and product version; LandsD photo/sheet ID; flight date/year;
- footprint/coverage and coordinate reference system;
- image variant/bands, format, expected size, and any sidecar files;
- official catalogue/download reference and authorization scope;
- state (`discovered`, `queued`, `downloading`, `verified`, `failed`), attempts, and error;
- actual byte size, SHA-256, download time, and validation notes.

Use product-specific expectations. DAP-L0 is a compressed JPEG product (about 2–3 MB per image) and is listed by HKMS among its open digital maps. Full-resolution DAP/DAP-UE files are substantially larger; the product information describes TIFF products around 760 MB to 2 GB for DAP-UE variants. A low-resolution DAP-L0 archive is therefore not interchangeable with the full-resolution source archive.

## 3. Use the right official access route

- For open products, start from LandsD’s HKMS / data.gov.hk / CSDI catalogue entry and its documented download or dataset API. The data.gov.hk DAP-L0 entry exposes a CSDI resource; confirm the resource’s current API/download mechanism before implementing against it.
- For products or records covered by the approved request queue, use that queue or ask LandsD for a supported bulk manifest/export. If the queue offers only browser downloads, get explicit confirmation before automating those UI actions.
- For a web-map display, use the documented Imagery Map API. Its documentation describes an XYZ PNG tile service, requires attribution, and warns against large bursts of requests. Do not enumerate every possible tile as a substitute for product downloads.
- Do not reverse-engineer undocumented endpoints, replay browser session cookies, automate or bypass reCAPTCHA, or evade throttling. HKMS documents reCAPTCHA on open-map downloads. If the approved path is blocked, pause and request an authorized bulk/API route or rate-limit exemption.

The supplied queue URL was not inspectable from this environment: it redirected to an internal hostname and returned a target-server error. I therefore cannot verify the queue’s product list, dates, or authorization scope. Also treat the `queueKey` in the URL as sensitive: do not put it in source control, screenshots, logs, or this project’s manifest. If it grants access and its exposure is a concern, ask LandsD whether it should be rotated.

## 4. Solar-panel detection: free imagery selection and quality ranking

For the stated task, start with the current **True Digital Orthophoto (TDOP)** open-data product rather than building a training set from arbitrary photo numbers. LandsD describes TDOP as a 0.25 m ground-sample-distance GeoTIFF product covering Hong Kong in 192 tiles, orthorectified using a digital surface model, including building features. That consistent map grid and building geometry make it the strongest free starting point for rooftop-panel detection. Check the product metadata for the actual image acquisition/update date before treating it as current. A panel-sized object may occupy only a handful of pixels at this resolution, so run a labelled pilot to establish whether it is adequate for the target panels.

Use **DOP5000** as a comparison dataset if its 0.20 m GSD is helpful, but note that LandsD distinguishes it from TDOP: conventional orthophoto correction does not rectify buildings in the same way. Include both only if you record product/version explicitly and keep their labels/splits separate. The current LandsD price list marks both DOP5000 and TDOP as free; download them via their open-data/CSDI listings rather than paid ordering routes. Plan storage accordingly: a full set is 192 tiles, with published approximate tile sizes of 810 MB for DOP5000 and 520 MB for TDOP (roughly 155 GB and 100 GB, respectively, before derived files). DAP-L0 is also listed as open data, but it is a 300-dpi compressed JPEG product and may be generated from different source types; it is not the best first choice for uniform roof geometry. The public “free aerial photographs” gallery is a small set of sample/portion images, not a complete, consistent training archive; it also carries a notice restricting onward dissemination.

Do not rank on `E267701C` (or any photo number) alone. The public flight index describes identifiers and flight metadata, not a numeric image-quality score. I could not verify `E267701C` as a record from public search; confirm the exact ID spelling and find its matching index row before selecting it. For a candidate set, rank/filter using:

1. **Product and date:** same product series, acquisition campaign, and recent enough for the intended roof stock; exclude historical orthophotos if the target is current solar panels.
2. **Ground sampling distance and geometry:** use product metadata; prefer the same GSD, coordinate system, orthorectification, and tile grid throughout a model run.
3. **Image conditions:** screen for blur, haze, saturation/underexposure, deep shadows, cloud/occlusion, stitching seams, and true-orthophoto artifacts around tall buildings.
4. **Task suitability:** manually inspect a labelled sample of positive and negative roofs. Record whether typical panel arrays are visually separable at the native resolution before processing all tiles.

Use image-quality metrics only as a screening aid (e.g. sharpness, clipping, and shadow fraction); they do not substitute for checking solar-panel visibility. Keep the raw GeoTIFFs and source metadata; make chips/normalizations as versioned derivatives. Label panel polygons or boxes, then split training/validation/test by spatial tile or district (not random neighboring chips) to avoid geographic leakage. If the model will detect changes, group and evaluate by acquisition date as well.

The official HKMS/CSDI free-data catalogues are the route to use. Do not bypass CAPTCHA or other access controls. If the sanctioned free download path presents a challenge during bulk access, request an approved bulk/API method or written automation/rate-limit arrangement from LandsD.

## 5. Pilot before scaling

1. Select a small, representative pilot (for example, 10–20 records across years and image variants), within the approved scope.
2. Download through the official route and record actual average size, transfer speed, metadata availability, and failure modes.
3. Confirm image readability and georeferencing; inspect TIFF/JPEG metadata and any world files, camera reports, or other sidecars.
4. Estimate storage and run time from the pilot, with headroom for retries and derived products. Obtain the necessary storage before the full run.
5. Have the data owner review the manifest and one or two sample outputs before scaling up.

Raw aerial photos are not necessarily a seamless, orthorectified mosaic. If the goal is an accurate map-like layer, use a suitable DOP/TDOP product or a separately approved photogrammetric workflow rather than simply stitching DAP images. HKMS also cautions that displayed photo footprints are for identification and may differ from actual coverage.

## 6. Implement a polite, restartable downloader

A small Python service/CLI is sufficient for a first version:

```text
official catalogue / flight index
              ↓
       normalized manifest (SQLite + CSV export)
              ↓
  approved downloader (low concurrency, restartable)
              ↓
 immutable raw files + checksums + validation report
              ↓
 optional approved derivatives / map viewer
```

Implementation requirements:

- Read only records in the approved manifest; make each item idempotent.
- Keep credentials and queue keys in a secret store or environment variable, never in Git. Redact signed URLs and tokens from logs.
- Use timeouts, bounded retries with exponential backoff/jitter, and honor `Retry-After`. Start with one or two concurrent downloads at most; increase only within the written service limits.
- Resume partial transfers only if the official server supports HTTP range requests. Write to a temporary `.part` file and atomically rename after verification.
- Verify HTTP status, expected content type, byte count where available, and SHA-256. Reject HTML/login/error pages saved as `.jpg`/`.tif`.
- Keep a clear failure queue and a dry-run mode. Stop automatically on repeated 401/403/429/5xx responses rather than hammering the service.

Suggested stack: Python `httpx`/`requests`, SQLite for job state, GDAL/`rasterio` for raster inspection, and a KML/KMZ parser or GDAL for the flight index. Add Playwright only if LandsD explicitly approves UI automation; do not use it to bypass human verification.

## 7. Store originals and derived products separately

Keep the original response bytes unchanged and outside Git (for example, on approved local/object storage). Use a stable layout such as:

```text
<storage-root>/raw/<product>/<year>/<photo-id>/<original-filename>
<storage-root>/metadata/manifest.sqlite
<storage-root>/metadata/manifest.csv
<storage-root>/reports/sha256sums.txt
<storage-root>/derived/<product>/<version>/...
```

Preserve original filenames where practical and use manifest IDs for stable lookup. Store any thumbnails, mosaics, reprojected files, or Cloud-Optimized GeoTIFFs in `derived/`; never silently replace the originals. Include LandsD attribution and the applicable licence text with any permitted display or distribution.

## 8. Completeness and quality checks

At the end of every batch, reconcile the manifest against the source catalogue/approved queue:

- every expected ID is either verified or has a recorded, actionable failure;
- no duplicate IDs or unexpected product/date/area are present;
- every verified file has a checksum and plausible size/type;
- raster files open successfully; dimensions, bands, CRS/georeferencing, and sidecars are consistent with the product;
- inspect a sample of images/footprints on a map and document coverage gaps;
- publish a summary of counts, bytes, failed items, and last successful sync time.

## 9. Suggested milestones

1. **Scope and authorization:** obtain written product/AOI/date scope, reuse rights, and approved transfer/rate limits.
2. **Inventory:** download the flight index and generate a deduplicated manifest; estimate total volume.
3. **Proof of concept:** retrieve and validate a small representative sample through the approved route.
4. **Pilot batch:** complete one bounded date/area/product batch; confirm storage, checksums, and GIS readability.
5. **Full acquisition:** run manifest-driven batches with monitoring and a pause/resume capability.
6. **Close-out:** reconcile expected vs. verified records, document gaps, and optionally build a separate viewer or derivatives if the licence allows.

### Official references

- [HKMS aerial-photo products](https://www.hkmapservice.gov.hk/OneStopSystem/prodOssCatADetail)
- [HKMS FAQ: open digital maps](https://www.hkmapservice.gov.hk/OneStopSystem/faqDownloadOpenDigitalMaps)
- [HKMS FAQ: product selection and order methods](https://www.hkmapservice.gov.hk/OneStopSystem/faqMapProductOrdering)
- [LandsD Aerial Photo Flight Index on data.gov.hk](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-aerial-photo-flight-index)
- [LandsD Digital Aerial Photo dataset on data.gov.hk](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-development-hkms-digital-aerial-photo)
- [LandsD True Digital Orthophoto (TDOP) dataset on data.gov.hk](https://data.gov.hk/en-data/dataset/hk-landsd-openmap-true-digital-orthophoto)
- [LandsD Digital Orthophoto specifications and per-tile photography dates](https://www.landsd.gov.hk/en/survey-mapping/mapping/aerial-photo-photogrammetric-products/digital-orthophoto.html)
- [LandsD digital-map price list (DOP5000 and TDOP marked Free)](https://www.landsd.gov.hk/doc/en/mapping/digital-map/common/doc/pricelist.pdf)
- [LandsD free downloadable aerial-photo gallery and copyright notice](https://www.landsd.gov.hk/en/resources/mapping-information/downloadable-aerial-photographs.html)
- [LandsD Imagery Map API documentation](https://portal.csdi.gov.hk/csdi-webpage/apidoc/ImageryMapAPI)
- [Licence Agreement for Using Government Digital Map](https://www.hkmapservice.gov.hk/OneStopSystem/resources/doc/en/HKMS-LA_Revision4.0_eng.pdf)

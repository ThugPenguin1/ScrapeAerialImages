import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from download_tdop import Tile, build_product_url, normalize_sheet, select_tiles  # noqa: E402


class TDOPSheetTests(unittest.TestCase):
    def test_pdf_sheet_maps_to_product_view_name(self):
        self.assertEqual(build_product_url("1-SE-D"),
                         "https://open.hkmapservice.gov.hk/OpenData/productView?"
                         "productName=TDOP&sheetName=T1-SE-D&productFormat=TIFF&locale=en")

    def test_prefixed_sheet_is_accepted(self):
        self.assertEqual(normalize_sheet("T1-SE-D"), "1-SE-D")

    def test_invalid_sheet_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_sheet("1-SE-Z")

    def test_select_requested_sheet_from_pdf_tiles(self):
        tiles = [Tile("1-SE-D", "tdop1sed20250009"), Tile("2-NE-C", "tdop2nec20250009")]
        selected = select_tiles(tiles, ["T2-NE-C"], None)
        self.assertEqual([tile.sheet_no for tile in selected], ["2-NE-C"])
        self.assertEqual(selected[0].file_stem, "tdop2nec20250009")


if __name__ == "__main__":
    unittest.main()

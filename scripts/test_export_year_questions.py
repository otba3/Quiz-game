import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EXPORTER = Path(__file__).with_name("export_year_questions.py").resolve()


class YearExporterTests(unittest.TestCase):
    def test_bilingual_titles_preserve_internal_parentheses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "data").mkdir()
            (root / "output" / "images").mkdir(parents=True)
            (root / "output" / "images" / "art.jpg").touch()
            csv_path = root / "data" / "Baghdad Modern Art Group Exhibition-Checklist.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Questions", "Answer", "Option 1", "Option 2",
                    "Option 3", "Option 4", "Art Info Answer", "", "", "",
                    "File of Option", "Art Info Option", "", "", "",
                    "File of Option", "Type",
                ])
                writer.writerow([
                    "What year was this artwork made?", "1986",
                    "1986", "1991", "1983", "1987", "Picture",
                    "Artist (1900)\nالفنان (١٩٠٠)",
                    "Untitled (The Letter Ein)\n(الحرف ع)", "1986", "art.jpg",
                    "", "", "", "", "", "which_year",
                ])
            subprocess.run(
                [sys.executable, str(EXPORTER)], cwd=root, check=True,
                capture_output=True, text=True, encoding="utf-8",
            )
            bank = json.loads(
                (root / "output" / "questions_year.json").read_text(encoding="utf-8")
            )

        art = bank["questions"][0]["artworks"][0]
        self.assertEqual(art["title"], {
            "en": "Untitled (The Letter Ein)", "ar": "الحرف ع",
        })
        self.assertEqual(art["artist"], {
            "en": "Artist (1900)", "ar": "الفنان (١٩٠٠)",
        })
        self.assertEqual(art["date"], {"en": "1986", "ar": ""})


if __name__ == "__main__":
    unittest.main()

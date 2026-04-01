from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


from daozang_kb.validation import check_text_integrity, validate_pn_sequence


class ValidationTests(unittest.TestCase):
    def test_validate_pn_sequence_accepts_contiguous_numbers(self) -> None:
        lines = ["[1] 道可道。", "[2] 名可名。", "[3] 無名天地之始。"]
        ok, message = validate_pn_sequence(lines)
        self.assertTrue(ok)
        self.assertEqual(message, "")

    def test_validate_pn_sequence_rejects_gap(self) -> None:
        lines = ["[1] 道可道。", "[3] 名可名。"]
        ok, message = validate_pn_sequence(lines)
        self.assertFalse(ok)
        self.assertIn("期望 [2]", message)

    def test_check_text_integrity_compares_stripped_text(self) -> None:
        archive_text = "道可道，非常道。\n名可名，非常名。"
        tagged_lines = ["# 第一章", "", "[1] 〖~道〗可道，非常〖~道〗。", "[2] 名可名，非常名。"]
        ok, details = check_text_integrity(tagged_lines, archive_text)
        self.assertTrue(ok)
        self.assertEqual(details, "")


if __name__ == "__main__":
    unittest.main()

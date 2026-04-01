from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


from daozang_kb.builders import build_nanhua_chapters


class BuilderTests(unittest.TestCase):
    def test_build_nanhua_chapters_marks_all_inputs_as_annotated(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for chapter_id, title in [("08_駢拇", "駢拇"), ("23_庚桑楚", "庚桑楚")]:
                (root / f"{chapter_id}.tagged.md").write_text(
                    f"# {title}\n\n[1] 測試段落。\n",
                    encoding="utf-8",
                )

            payload = build_nanhua_chapters(sorted(root.glob("*.tagged.md")))

        self.assertEqual(payload["metadata"]["total_chapters"], 2)
        self.assertEqual(payload["metadata"]["annotated_chapters"], 2)
        self.assertTrue(all(chapter["annotated"] for chapter in payload["chapters"]))


if __name__ == "__main__":
    unittest.main()

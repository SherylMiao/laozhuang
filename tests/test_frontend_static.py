from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrontendStaticTests(unittest.TestCase):
    def test_homepage_has_dual_reader_entries_and_no_old_pitch_copy(self) -> None:
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn('reader/?book=daodejing&chapter=001', html)
        self.assertIn('reader/?book=nanhua&chapter=01_逍遙遊', html)
        self.assertNotIn("這不是把古文做成普通資料表", html)

    def test_reader_has_book_switch_and_scrollable_chapter_list(self) -> None:
        html = (ROOT / "docs" / "reader" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "docs" / "css" / "daozang.css").read_text(encoding="utf-8")
        self.assertIn('id="book-switch"', html)
        self.assertRegex(css, r"\.chapter-list\s*\{[^}]*max-height:")
        self.assertRegex(css, r"\.chapter-list\s*\{[^}]*overflow-y:\s*auto")

    def test_reader_uses_single_book_viz_link_and_wide_catalog_layout(self) -> None:
        html = (ROOT / "docs" / "reader" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "docs" / "reader" / "reader.js").read_text(encoding="utf-8")
        css = (ROOT / "docs" / "css" / "daozang.css").read_text(encoding="utf-8")
        self.assertIn('id="book-viz-link"', html)
        self.assertNotIn('../concept-map/"', html)
        self.assertNotIn('../fable-atlas/"', html)
        self.assertIn("vizHref", js)
        self.assertRegex(css, r"\.reader-layout\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)")
        self.assertRegex(css, r"\.chapter-list\s*\{[^}]*grid-template-columns:")

    def test_site_uses_unified_serif_font_stack(self) -> None:
        css = (ROOT / "docs" / "css" / "daozang.css").read_text(encoding="utf-8")
        self.assertNotIn("ZCOOL XiaoWei", css)
        self.assertNotIn("#f3ead8", css)


if __name__ == "__main__":
    unittest.main()

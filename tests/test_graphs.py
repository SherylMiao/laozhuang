from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


from daozang_kb.graphs import build_cooccurrence_links, extract_fable_blocks


class GraphTests(unittest.TestCase):
    def test_build_cooccurrence_links_counts_chapter_pairs(self) -> None:
        chapters = [
            {"chapter": "001", "concepts": ["道", "無", "有"]},
            {"chapter": "002", "concepts": ["有", "無"]},
        ]
        links = build_cooccurrence_links(chapters)
        link_map = {(link["source"], link["target"]): link for link in links}
        self.assertEqual(link_map[("有", "無")]["weight"], 2)
        self.assertEqual(sorted(link_map[("有", "無")]["co_chapters"]), ["001", "002"])

    def test_extract_fable_blocks(self) -> None:
        lines = [
            "# 逍遙遊（內篇）",
            "",
            "::: fable 鯤鵬之變",
            "[1] 北冥有魚，其名為鯤。",
            "[2] 化而為鳥，其名為鵬。",
            ":::",
        ]
        blocks = extract_fable_blocks(lines, "01_逍遙遊", "內篇")
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["name"], "鯤鵬之變")
        self.assertEqual(blocks[0]["para_range"], "1-2")


if __name__ == "__main__":
    unittest.main()

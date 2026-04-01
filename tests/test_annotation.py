from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


from daozang_kb.annotation import annotate_text, inject_fable_markers, strip_annotations, text_to_paragraphs


class AnnotationTests(unittest.TestCase):
    def test_strip_annotations_restores_original_text(self) -> None:
        tagged = "〖~道〗可道，非常〖~道〗。〖#聖人〗不爭。"
        self.assertEqual(strip_annotations(tagged), "道可道，非常道。聖人不爭。")

    def test_annotate_text_prefers_longest_match(self) -> None:
        text = "聖人之道為而不爭。"
        lexicon = [
            {"term": "聖人之道", "type": "concept"},
            {"term": "聖人", "type": "identity"},
        ]
        self.assertEqual(
            annotate_text(text, lexicon),
            "〖~聖人之道〗為而不爭。",
        )

    def test_text_to_paragraphs_builds_pn_lines(self) -> None:
        text = "道可道，非常道。名可名，非常名。無名天地之始；有名萬物之母。"
        paragraphs = text_to_paragraphs(text, strategy="sentence")
        self.assertEqual(
            paragraphs,
            [
                "[1] 道可道，非常道。",
                "[2] 名可名，非常名。",
                "[3] 無名天地之始；有名萬物之母。",
            ],
        )

    def test_inject_fable_markers_matches_variant_seed(self) -> None:
        lines = [
            "[1] 南郭子綦隱几而坐，仰天而噓。",
            "[2] 荅焉似喪其耦。",
        ]
        rendered = inject_fable_markers(
            lines,
            [{"name": "南郭子綦隱几", "start": "南郭子綦隱机而坐"}],
        )
        self.assertEqual(
            rendered,
            [
                "::: fable 南郭子綦隱几",
                "[1] 南郭子綦隱几而坐，仰天而噓。",
                "[2] 荅焉似喪其耦。",
                ":::",
            ],
        )

    def test_inject_fable_markers_wraps_whole_chapter_as_fallback(self) -> None:
        lines = [
            "[1] 天下有至樂無有哉？",
            "[2] 有可以活身者無有哉？",
        ]
        rendered = inject_fable_markers(lines, [], fallback_name="至樂")
        self.assertEqual(
            rendered,
            [
                "::: fable 至樂",
                "[1] 天下有至樂無有哉？",
                "[2] 有可以活身者無有哉？",
                ":::",
            ],
        )


if __name__ == "__main__":
    unittest.main()

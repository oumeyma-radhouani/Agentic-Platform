import unittest

from src.backend.aggregator import (
    aggregate_results,
    calculate_summary_metrics,
    classify_nps,
)


class AggregatorTests(unittest.TestCase):
    def test_nps_boundaries(self):
        expected = {
            0: "detractor",
            6: "detractor",
            7: "passive",
            8: "passive",
            9: "promoter",
            10: "promoter",
        }
        for score, category in expected.items():
            with self.subTest(score=score):
                self.assertEqual(classify_nps(score), category)

    def test_summary_matches_supplied_nps_formula(self):
        records = []
        records.extend({"original_score": 10} for _ in range(120))
        records.extend({"original_score": 8} for _ in range(30))
        records.extend({"original_score": 2} for _ in range(50))

        self.assertEqual(
            calculate_summary_metrics(records),
            {
                "total_processed": 200,
                "nps_score": 35,
                "total_promoters": 120,
                "total_passives": 30,
                "total_detractors": 50,
            },
        )

    def test_aggregate_results_orders_themes(self):
        records = [
            {"original_score": 2, "assigned_theme": "Problème technique"},
            {"original_score": 8, "assigned_theme": "Retard de traitement"},
            {"original_score": 9, "assigned_theme": "Retard de traitement"},
        ]

        result = aggregate_results(records)

        self.assertEqual(
            result["top_themes"],
            [
                {"theme": "Retard de traitement", "count": 2},
                {"theme": "Problème technique", "count": 1},
            ],
        )
        self.assertEqual(result["processed_records"], records)

    def test_empty_batch_is_valid(self):
        self.assertEqual(calculate_summary_metrics([])["nps_score"], 0)


if __name__ == "__main__":
    unittest.main()

import unittest

from backend.app.graph.routing import should_use_kg_query


class GraphRoutingTests(unittest.TestCase):
    def test_normal_support_question_skips_kg(self):
        self.assertFalse(should_use_kg_query("How do I reset my password?"))

    def test_relationship_question_uses_kg(self):
        self.assertTrue(should_use_kg_query("Which customers are connected to the billing issue?"))


if __name__ == "__main__":
    unittest.main()

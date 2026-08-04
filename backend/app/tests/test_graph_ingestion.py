import unittest
from unittest.mock import Mock, patch

from backend.app.db import knowladge_graph


class GraphIngestionTests(unittest.TestCase):
    def test_ingest_pdf_to_graph_force_refresh_clears_existing_graph(self):
        graph_db = Mock()
        graph_db.query.return_value = [{"count": 1}]

        with patch.object(knowladge_graph, "load_document", return_value=[object()]), \
             patch.object(knowladge_graph, "split_documents", return_value=["chunk"]), \
             patch.object(knowladge_graph, "get_llm", return_value=object()), \
             patch.object(knowladge_graph, "LLMGraphTransformer") as transformer_cls:
            transformer_cls.return_value.convert_to_graph_documents.return_value = ["graph-doc"]

            knowladge_graph.ingest_pdf_to_graph("dummy.pdf", graph_db=graph_db, force_refresh=True)

        self.assertTrue(any(call.args == ("MATCH (n) DETACH DELETE n",) for call in graph_db.query.call_args_list))
        graph_db.add_graph_documents.assert_called_once_with(["graph-doc"], baseEntityLabel=True, include_source=True)


if __name__ == "__main__":
    unittest.main()

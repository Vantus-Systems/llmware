import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add repo root to path
sys.path.append(os.getcwd())

from llmware.agents import RecursiveAgent

class TestRecursiveAgent(unittest.TestCase):

    def setUp(self):
        # Mock Prompt and Query classes
        self.mock_prompt_patcher = patch('llmware.agents.Prompt')
        self.mock_query_patcher = patch('llmware.agents.Query')

        self.mock_prompt_cls = self.mock_prompt_patcher.start()
        self.mock_query_cls = self.mock_query_patcher.start()

        # Setup mock instances
        self.mock_query_engine = MagicMock()

        # Prompt().load_model(...) returns 'self'.
        self.mock_prompt_instance = MagicMock()
        self.mock_prompt_cls.return_value = self.mock_prompt_instance
        self.mock_prompt_instance.load_model.return_value = self.mock_prompt_instance

        self.mock_query_cls.return_value = self.mock_query_engine

    def tearDown(self):
        self.mock_prompt_patcher.stop()
        self.mock_query_patcher.stop()

    def test_instantiation(self):
        agent = RecursiveAgent(library="test_lib", controller_model="controller", reader_model="reader")
        self.assertEqual(agent.library, "test_lib")
        self.assertEqual(agent.controller_model, "controller")
        self.assertEqual(agent.reader_model, "reader")

        # Verify Prompt loading called twice (controller and reader)
        self.assertEqual(self.mock_prompt_instance.load_model.call_count, 2)

    def test_neural_peek(self):
        agent = RecursiveAgent(library="test_lib", controller_model="controller")

        # Mock query result
        self.mock_query_engine.semantic_query.return_value = [
            {"text": "chunk1"}, {"text": "chunk2"}
        ]

        results = agent.neural_peek("test query")
        self.assertEqual(results, ["chunk1", "chunk2"])
        self.mock_query_engine.semantic_query.assert_called_with("test query", result_count=5)

    def test_map_reduce(self):
        agent = RecursiveAgent(library="test_lib", controller_model="controller")

        # Mock reader response
        # Since we instantiate a NEW Prompt inside map_reduce, we need to make sure the mocked Prompt class
        # returns a new mock instance (or the same one, but allowing multiple calls).
        # Our setUp uses: self.mock_prompt_cls.return_value = self.mock_prompt_instance
        # So every Prompt() call returns the SAME instance. This is fine for verifying method calls.

        # side_effect needs to handle the sequence.
        # Chunks are processed in threads.
        # Then synthesis.

        self.mock_prompt_instance.prompt_main.side_effect = [
            {"llm_response": "summary1"}, # Chunk 1
            {"llm_response": "summary2"}, # Chunk 2
            {"llm_response": "final_summary"} # Synthesis
        ]

        chunks = ["text1", "text2"]
        result = agent.map_reduce("summarize", chunks)

        self.assertEqual(result, "final_summary")
        # Ensure prompt_main called 3 times
        self.assertEqual(self.mock_prompt_instance.prompt_main.call_count, 3)

    def test_update_context_granular(self):
        agent = RecursiveAgent(library="test_lib", controller_model="controller")
        agent.context = {"key1": "val1"}

        agent.update_context_granular("key2", "val2", "set")
        self.assertEqual(agent.context["key2"], "val2")

        agent.update_context_granular("key1", None, "delete")
        self.assertTrue("key1" not in agent.context)

    def test_parse_args_robust(self):
        agent = RecursiveAgent(library="test_lib", controller_model="controller")

        # Test 1: Simple args
        args = agent._parse_args_robust('arg1, "arg 2"')
        self.assertEqual(args, ['arg1', 'arg 2'])

        # Test 2: Comma inside quotes
        args = agent._parse_args_robust('"val, with, comma", val2')
        self.assertEqual(args, ['val, with, comma', 'val2'])

        # Test 3: Newlines and JSON-like with escaped quotes
        # Input simulates: key, "{\n \"json\": \"val\" \n}"
        args = agent._parse_args_robust('key, "{\n \\"json\\": \\"val\\" \n}"')
        self.assertEqual(args, ['key', '{\n "json": "val" \n}'])

    def test_run_flow_advanced(self):
        agent = RecursiveAgent(library="test_lib", controller_model="controller")

        # Sequence of controller responses:
        # 1. PEEK("what is X")
        # 2. SET("status", "found")
        # 3. ANSWER("It is Y")
        self.mock_prompt_instance.prompt_main.side_effect = [
            {"llm_response": 'PEEK("what is X")'},
            {"llm_response": 'SET("status", "found")'},
            {"llm_response": 'ANSWER("It is Y")'}
        ]

        # Mock peek result
        self.mock_query_engine.semantic_query.return_value = [{"text": "X is Y"}]

        response = agent.run("find X")

        self.assertEqual(response, "It is Y")

        # Verify context updated with peek result and status
        self.assertTrue("peek_step_1" in agent.context)
        self.assertEqual(agent.context["peek_step_1"], ["X is Y"])
        self.assertEqual(agent.context["status"], "found")

if __name__ == '__main__':
    unittest.main()

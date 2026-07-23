import importlib.util
from pathlib import Path
import sys
import unittest

SPEC = importlib.util.spec_from_file_location('pipeline', Path(__file__).with_name('run_preexperiment.py'))
pipeline = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pipeline
SPEC.loader.exec_module(pipeline)


class PipelineUnitTests(unittest.TestCase):
    def test_parse_dynamic_inbox_payload(self):
        inner = '0x' + '11' * 64
        data = '0x' + ('0' * 63 + '2') + ('0' * 62 + '40') + inner[2:]
        self.assertEqual(pipeline.inbox_event_payload({'data': data}), inner)

    def test_negative_values_are_retained(self):
        stats = pipeline.quantiles([-7.0, 1.0])
        self.assertEqual(stats['min'], -7.0)

    def test_word_rejects_short_abi(self):
        with self.assertRaises(ValueError):
            pipeline.word('0x00', 0)

    def test_batch_selection_requires_continuity(self):
        with self.assertRaises(RuntimeError):
            pipeline.choose_contiguous_batches([{'batch_sequence': 1}, {'batch_sequence': 3}], 2)


if __name__ == '__main__':
    unittest.main()

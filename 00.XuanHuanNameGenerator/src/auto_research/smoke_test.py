import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from auto_research import prepare
from auto_research.train import NameMLP


class AutoResearchSmokeTest(unittest.TestCase):
    def test_loads_training_tokens_and_vocab(self):
        bundle = prepare.load_data_bundle()

        self.assertEqual(len(bundle.raw_tokens), 12000)
        self.assertIn(".", bundle.stoi)
        self.assertIn("|", bundle.stoi)
        self.assertGreater(bundle.vocab_size, 10)

    def test_build_dataset_shapes(self):
        bundle = prepare.load_data_bundle()

        x, y = prepare.build_dataset(bundle.raw_tokens[:2], block_size=3, stoi=bundle.stoi)

        self.assertEqual(x.ndim, 2)
        self.assertEqual(y.ndim, 1)
        self.assertEqual(x.shape[1], 3)
        self.assertEqual(x.shape[0], y.shape[0])

    def test_model_forward_shape(self):
        bundle = prepare.load_data_bundle()
        model = NameMLP(
            vocab_size=bundle.vocab_size,
            block_size=3,
            embedding_dim=4,
            hidden_dim=100,
        )

        x, _ = prepare.build_dataset(bundle.raw_tokens[:2], block_size=3, stoi=bundle.stoi)
        logits = model(x[:5])

        self.assertEqual(tuple(logits.shape), (5, bundle.vocab_size))

    def test_sample_validation(self):
        self.assertTrue(prepare.is_valid_sample(["h", "an", "|", "l", "i"]))
        self.assertFalse(prepare.is_valid_sample(["h", "an", "l", "i"]))
        self.assertFalse(prepare.is_valid_sample(["h", "bad", "|", "l", "i"]))


if __name__ == "__main__":
    unittest.main()

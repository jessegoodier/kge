import unittest
from unittest.mock import patch
from kge.cli.main import parse_args

class TestCLI(unittest.TestCase):
    def test_parse_args_all_flag(self):
        with patch('sys.argv', ['kge', '-A']):
            args = parse_args()
            self.assertTrue(args.all)
            self.assertFalse(args.complete)
            self.assertIsNone(args.completion)
            self.assertIsNone(args.pod_name)

        with patch('sys.argv', ['kge', '--all']):
            args = parse_args()
            self.assertTrue(args.all)
            self.assertFalse(args.complete)
            self.assertIsNone(args.completion)
            self.assertIsNone(args.pod_name)

    def test_parse_args_complete_flag(self):
        with patch('sys.argv', ['kge', '--complete']):
            args = parse_args()
            self.assertFalse(args.all)
            self.assertTrue(args.complete)
            self.assertIsNone(args.completion)
            self.assertIsNone(args.pod_name)

    def test_parse_args_completion_zsh(self):
        with patch('sys.argv', ['kge', '--completion=zsh']):
            args = parse_args()
            self.assertFalse(args.all)
            self.assertFalse(args.complete)
            self.assertEqual(args.completion, 'zsh')
            self.assertIsNone(args.pod_name)

    def test_parse_args_pod_name(self):
        with patch('sys.argv', ['kge', 'my-pod']):
            args = parse_args()
            self.assertFalse(args.all)
            self.assertFalse(args.complete)
            self.assertIsNone(args.completion)
            self.assertEqual(args.pod_name, 'my-pod')

    def test_parse_args_no_args(self):
        with patch('sys.argv', ['kge']):
            args = parse_args()
            self.assertFalse(args.all)
            self.assertFalse(args.complete)
            self.assertIsNone(args.completion)
            self.assertIsNone(args.pod_name)

    def test_parse_args_mutually_exclusive(self):
        # Test that mutually exclusive arguments raise an error
        with patch('sys.argv', ['kge', '-A', '--complete']):
            with self.assertRaises(SystemExit):
                parse_args()

        with patch('sys.argv', ['kge', '-A', '--completion=zsh']):
            with self.assertRaises(SystemExit):
                parse_args()

        with patch('sys.argv', ['kge', '--complete', '--completion=zsh']):
            with self.assertRaises(SystemExit):
                parse_args()

if __name__ == '__main__':
    unittest.main() 
import tempfile
import unittest
from pathlib import Path

from src.core.file_utils import FileUtils


class FileUtilsTests(unittest.TestCase):
    def test_merge_files_accepts_mixed_path_types(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            part0 = tmp / "data_part000.txt"
            part1 = tmp / "data_part001.txt"
            output = tmp / "output.txt"

            part0.write_text("hello ")
            part1.write_text("world")

            result = FileUtils.merge_files([str(part1), part0], output)

            self.assertEqual(result, output)
            self.assertEqual(output.read_text(), "hello world")


if __name__ == "__main__":
    unittest.main()

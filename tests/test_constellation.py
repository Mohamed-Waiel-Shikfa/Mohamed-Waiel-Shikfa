import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from orbital_activity import contribution_marks, satellite_sizes
from refresh_commit_counts import parse_count


class ConstellationTests(unittest.TestCase):
    def test_commit_ranges(self):
        self.assertEqual([contribution_marks(n) for n in (None, 0, 1, 4, 5, 19, 20, 93)],
                         [0, 0, 1, 1, 2, 2, 3, 3])

    def test_commit_pagination(self):
        self.assertEqual(parse_count('HTTP/2 200\r\n\r\n0'), 0)
        self.assertEqual(parse_count('HTTP/2 200\r\n\r\n1'), 1)
        self.assertEqual(parse_count('HTTP/2 200\r\nLink: <https://api.github.com/x?page=93>; rel="last"\r\n\r\n1'), 93)

    def test_planet_area_tracks_source_volume(self):
        repos = [{'name': n, 'pushed_at': 'date'} for n in ('small', 'large')]
        metrics = {'metric': 'filtered_nonblank_noncomment_source_lines', 'repos': {
            n: {'source_lines': lines, 'pushed_at': 'date', 'head_sha': 'a' * 40}
            for n, lines in [('small', 100), ('large', 400)]}}
        small, large = satellite_sizes(repos, metrics)
        self.assertAlmostEqual((large / small) ** 2, 4)


if __name__ == '__main__':
    unittest.main()

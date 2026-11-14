import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_activity as updater


def repo(name="example", **changes):
    value = {"name": name, "private": False, "fork": False, "archived": False,
             "owner": {"login": updater.USER}, "language": "Python",
             "pushed_at": "2026-11-08T02:18:35Z"}
    value.update(changes)
    return value


class ActivityTests(unittest.TestCase):
    def test_only_original_public_owned_active_repositories_are_counted(self):
        values = [repo(), repo("private", private=True), repo("fork", fork=True),
                  repo("archived", archived=True), repo(updater.USER),
                  repo("other", owner={"login": "someone-else"}), repo("empty", pushed_at=None)]
        self.assertEqual(updater.summarize(values), [
            {"name": "example", "language": "Python", "pushed_at": "2026-11-08T02:18:35Z"}])

    def test_order_and_allowlisted_fields(self):
        old = repo("old", pushed_at="2024-01-01T00:00:00Z", language=None, secret="not published")
        result = updater.summarize([old, repo("new")])
        self.assertEqual([r["name"] for r in result], ["new", "old"])
        self.assertNotIn("secret", result[1])
        self.assertIsNone(result[1]["language"])

    def test_invalid_data_is_rejected(self):
        for changes in [{"name": "<script>"}, {"pushed_at": "not-a-date"}, {"language": 123}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                updater.summarize([repo(**changes)])

    def test_pagination_fetches_every_page(self):
        class Response:
            def __init__(self, data): self.data = json.dumps(data)
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return self.data
        with patch.object(updater, "urlopen", side_effect=[Response([repo()] * 100), Response([repo("last")])]) as fetch:
            self.assertEqual(len(updater.fetch_repos()), 101)
            self.assertIn("page=2", fetch.call_args.args[0].full_url)

    def test_unchanged_snapshot_keeps_date_and_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot.json"
            data = {"snapshot_at": "2026-11-01T00:00:00+00:00", "repos": updater.summarize([repo()])}
            snapshot.write_text(json.dumps(data))
            original = snapshot.read_bytes()
            with patch.object(updater, "SNAPSHOT", snapshot), patch.object(updater, "fetch_repos", return_value=[repo()]), patch.object(updater, "build") as build:
                updater.refresh()
                self.assertEqual(snapshot.read_bytes(), original)
                build.assert_called_once()

    def test_network_failure_preserves_snapshot_and_does_not_build(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot.json"
            snapshot.write_text('{"previous": "snapshot"}')
            original = snapshot.read_bytes()
            with patch.object(updater, "SNAPSHOT", snapshot), patch.object(updater, "fetch_repos", side_effect=OSError("offline")), patch.object(updater, "build") as build:
                with self.assertRaises(OSError): updater.refresh()
                self.assertEqual(snapshot.read_bytes(), original)
                build.assert_not_called()


if __name__ == "__main__":
    unittest.main()

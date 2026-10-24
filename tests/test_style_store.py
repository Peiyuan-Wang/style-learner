import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "style-learner/scripts/style_store.py"


class StyleStoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="style-test-", dir=Path(__file__).resolve().parent)
        self.root = Path(self.tmp.name)
        self.call("init")
        self.call("create", "academic", "--name", "中文论文")

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, *args, fail=False):
        result = subprocess.run([sys.executable, str(SCRIPT), "--home", str(self.root / "store"), *args],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1 if fail else 0, result.stderr)
        return json.loads(result.stderr if fail else result.stdout)

    def learn(self, sid="academic", key="sample-1", revision=0, text="审慎表述结论。", fail=False):
        profile = self.root / "profile.md"
        evidence = self.root / "evidence.json"
        profile.write_text(text, encoding="utf-8")
        evidence.write_text(json.dumps({"source_key": key, "kind": "work", "summary": "讨论段落采用限定措辞。"}), encoding="utf-8")
        return self.call("learn", sid, "--profile-file", str(profile), "--evidence-file", str(evidence),
                         "--expected-revision", str(revision), fail=fail)

    def test_independent_routing_and_persistence(self):
        self.call("settings", "--write-style", "academic")
        self.assertEqual(self.call("settings")["learn_style"], "daily")
        self.learn()
        self.assertEqual(self.call("show", "daily")["revision"], 0)
        self.assertEqual(self.call("show", "academic")["profile"], "审慎表述结论。")
        self.call("init")
        self.assertEqual(self.call("settings")["write_style"], "academic")

    def test_duplicate_and_stale_update_are_safe(self):
        self.learn()
        self.assertEqual(self.learn()["status"], "duplicate")
        self.learn(key="sample-2", fail=True)
        self.assertEqual(len(self.call("history", "academic")), 1)
        self.learn(key="sample-2", revision=1)
        self.assertEqual(self.call("show", "academic")["revision"], 2)

    def test_restore_and_export(self):
        self.learn()
        self.learn(key="sample-2", revision=1, text="增加明确的段落中心句。")
        self.call("restore", "academic", "--revision", "1", "--expected-revision", "2")
        self.assertEqual(self.call("show", "academic")["profile"], "审慎表述结论。")
        dest = self.root / "export"
        self.call("export", "academic", "--dest", str(dest))
        self.assertTrue((dest / "SKILL.md").exists())
        self.assertEqual((dest / "profile.md").read_text(encoding="utf-8"), "审慎表述结论。")
        self.call("export", "academic", "--dest", str(dest), fail=True)

    def test_delete_removes_history_and_resets_only_affected_default(self):
        self.learn()
        self.call("settings", "--write-style", "academic")
        self.call("delete", "academic")
        settings = self.call("settings")
        self.assertIsNone(settings["write_style"])
        self.assertEqual(settings["learn_style"], "daily")
        self.call("create", "academic", "--name", "新档案")
        self.assertEqual(self.call("history", "academic"), [])
        self.assertEqual(self.learn()["status"], "saved")

    def test_bad_id_unknown_default_empty_export(self):
        self.call("create", "../escape", "--name", "bad", fail=True)
        self.call("settings", "--learn-style", "missing", fail=True)
        self.assertEqual(self.call("settings")["learn_style"], "daily")
        self.call("export", "academic", "--dest", str(self.root / "empty"), fail=True)
        self.assertFalse((self.root / "empty").exists())


if __name__ == "__main__":
    unittest.main()

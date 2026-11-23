from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.compat.game_profile import (
    GameProfileError, plan_game_launch, launch_game, validate_game_profile,
)


def minimal_pe64() -> bytes:
    data = bytearray(0x400)
    data[0:2] = b"MZ"
    data[0x3C:0x40] = (0x80).to_bytes(4, "little")
    data[0x80:0x84] = b"PE\0\0"
    data[0x84:0x86] = (0x8664).to_bytes(2, "little")
    data[0x86:0x88] = (1).to_bytes(2, "little")
    data[0x94:0x96] = (0xF0).to_bytes(2, "little")
    data[0x98:0x9A] = (0x20B).to_bytes(2, "little")
    data[0x98 + 68:0x98 + 70] = (2).to_bytes(2, "little")
    data[0x98 + 108:0x98 + 112] = (16).to_bytes(4, "little")
    data[0x188:0x18C] = (0x1000).to_bytes(4, "little")
    data[0x18C:0x190] = (0x200).to_bytes(4, "little")
    return bytes(data)


def fixture(folder: Path) -> dict:
    (folder / "game.exe").write_bytes(minimal_pe64())
    (folder / "prefix").mkdir()
    return {
        "schema": "duckos.game-launch-profile.v1",
        "id": "sample-game",
        "name": "Sample Game",
        "executable": "game.exe",
        "working_directory": ".",
        "arguments": ["-window", "-language", "en"],
        "runtime": {"backend": "wine", "executable": "/usr/bin/wine", "prefix": "prefix"},
        "compatibility": {
            "windows_version": "windows-xp", "service_pack": 3,
            "graphics": ["direct3d9"], "audio": ["directsound", "winmm"],
            "input": ["directinput"], "network": ["tcp_ip"],
            "display": {"width": 1024, "height": 768, "color_depth": 16, "refresh_rate_hz": 75},
        },
        "environment": {"WINEDEBUG": "-all"},
    }


class GameLaunchProfileTests(unittest.TestCase):
    def test_validates_xp_sp3_profile_and_legacy_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = validate_game_profile(fixture(root), root)
            self.assertEqual(profile["compatibility"]["service_pack"], 3)
            self.assertEqual(profile["compatibility"]["display"]["color_depth"], 16)
            self.assertEqual(profile["arguments"], ["-window", "-language", "en"])

    def test_rejects_shell_injection_environment_and_unknown_backends(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = fixture(root)
            payload["environment"] = {"LD_PRELOAD": "/tmp/evil.so"}
            with self.assertRaises(GameProfileError):
                validate_game_profile(payload, root)
            payload = fixture(root)
            payload["runtime"]["backend"] = "native-win32"
            with self.assertRaises(GameProfileError):
                validate_game_profile(payload, root)

    def test_rejects_bad_arguments_and_unsupported_color_depth(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = fixture(root)
            payload["arguments"] = ["ok", "bad\x00arg"]
            with self.assertRaises(GameProfileError):
                validate_game_profile(payload, root)
            payload = fixture(root)
            payload["compatibility"]["display"]["color_depth"] = 12
            with self.assertRaises(GameProfileError):
                validate_game_profile(payload, root)

    def test_plan_is_non_executing_and_reports_missing_wine(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = validate_game_profile(fixture(root), root)
            plan = plan_game_launch(profile, wine_binary="/missing/wine")
            self.assertEqual(plan["status"], "blocked")
            self.assertFalse(plan["execution_performed"])
            self.assertFalse(plan["shell_used"])
            self.assertIn("Wine runtime", plan["blockers"][0])

    def test_launch_uses_argument_vector_and_explicit_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = validate_game_profile(fixture(root), root)
            class Process:
                pid = 321
            calls = []
            def fake_popen(argv, **kwargs):
                calls.append((argv, kwargs))
                return Process()
            with patch("duckos.compat.game_profile.shutil.which", return_value="/usr/bin/wine"):
                result = launch_game(profile, popen=fake_popen)
            argv, kwargs = calls[0]
            self.assertTrue(result["started"])
            self.assertEqual(result["pid"], 321)
            self.assertEqual(argv[1], str(root / "game.exe"))
            self.assertEqual(kwargs["cwd"], str(root))
            self.assertFalse(kwargs["shell"])
            self.assertEqual(kwargs["env"]["WINEPREFIX"], str(root / "prefix"))


if __name__ == "__main__":
    unittest.main()

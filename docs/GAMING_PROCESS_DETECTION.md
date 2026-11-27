# DAKOS process-based game detection

**Project author/developer:** Ivan-VHS

DAKOS adds a read-only process catalog for Windows, Linux and macOS. It compares executable basenames with an explicit local profile catalog using exact, case-insensitive matches.

## Profile format

```json
{
  "schema": "dakos.game-profile-catalog.v1",
  "profiles": [
    {
      "id": "sample-game",
      "name": "Sample Game",
      "engine": "directx12",
      "executables": ["SampleGame.exe"]
    }
  ]
}
```

## Detection semantics

A name match is a candidate, not proof that the foreground window belongs to the game. The detector deliberately does not collect process command-line arguments. It marks window state and graphics context as unchecked; DAKOS must confirm those signals before changing a gaming session state.

The process catalog is bounded, read-only and safe to run without elevated permissions. It does not suspend, reprioritize, terminate or launch processes.

## CLI

```sh
python -m dakos gaming-detect --profiles game-profiles.json
```

## Verification

```sh
python -m unittest tests.test_gaming_detection -v
```

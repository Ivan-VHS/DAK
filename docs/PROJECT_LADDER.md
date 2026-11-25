# DAK project maturity

**Current stage:** 03 — Evolution  
**Assessment:** provisional  
**Next stage:** 04 — Ascension  
**Canonical ladder:** [DAK Engineering Maturity Ladder](PROJECT_EVOLUTION_LADDER.md)  
**Machine record:** [`.github/project-ladder.v1.json`](../.github/project-ladder.v1.json)

The current stage records a bounded, experimental x86-64 Stage 1 boot path. It does **not** mean DAK has a usable process/service operating-system session.

## Promotion focus — Ascension

- Implement and test additional native kernel/runtime primitives beyond the Stage 1 boot slice.
- Define and exercise a versioned native boundary between Reaper and the DAK kernel.
- Add contract and integration tests that exercise the connected path in CI.
- Keep host-native Mora, Reaper reference policies and kernel-enforced behavior as separate evidence classes.

## Assessment limits

This is a provisional repository-evidence assessment. The target boot workflow and regression suite were not re-run in this adoption. The kernel still lacks a complete process model, syscall layer, filesystem, service supervisor and compositor. Those boundaries remain explicit and are not counted as implemented.

## Promotion procedure

Update the stage record in the same pull request as the implementation. A stage can be marked `met` only when its required evidence categories point to real repository artifacts. `verified` additionally requires a pinned commit, workflow, environment and CI run URL, plus test and CI evidence.

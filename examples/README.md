# Examples

Six models for the tasks in `experiments/`, five of them delivered by LLM
agents in the study, each with the reading a client made of it and the
output of the acceptance. Together they show each layer finding what the
others miss.

| Example | Task | Delivered by | What it shows |
|---|---|---|---|
| `task1-solved` | 1 | Opus 5, Claude Code | a delivery that passes every layer and check |
| `task1-black-box` | 1 | identified by us from the fitting experiments | a linear state-space model passes the behaviour layer and the test experiments; only the reading of conformance rejects it |
| `task1-start-values` | 1 | Hy4 preview, OpenCode | the report lists the fitted values, the file still carries its start values: 750 times the noise, and report and file inconsistent |
| `task2-static-friction` | 2 | gpt-5.6-luna, Codex | a sled with a static friction peak that the device does not have: it passes the behaviour layer and fails on a test experiment and on the heavier variant |
| `task4-energy` | 4 | Qwen3.8 (27.8 B), OpenCode | a drive train that passes the behaviour layer and the test experiments while its rebuilt converter creates energy, 29 kJ on the first fitting experiment; the invariant catches it |
| `task5-magnet` | 5 | Opus 5, Claude Code | a magnet that meets all nine features; the report names the moving mass in grams, which the automatic part of the report check cannot match, so the reading decides |

Each directory holds

- `model.mo`, the delivered model, and `report.md`, the report delivered
  with it; the agent's scripts, figures and build files are left out, and
  the task numbers are those of `experiments/`,
- `reading.toml`, the client's reading (`acceptance/README.md`),
- `expected.txt`, the output of the acceptance.

## Running an example

```
python -m acceptance.grade experiments/task1 examples/task1-solved/model.mo \
    --reading examples/task1-solved/reading.toml --report examples/task1-solved/report.md
```

prints the verdict layer by layer, as in `expected.txt`; the black box has
no report. Without `--reading` the layers that rest on a reading stay pending, which
is what a fresh delivery looks like before the client has read it.

The expected outputs were produced with the versions listed in the main
README; another version of OpenModelica can change the last digits of a
ratio.

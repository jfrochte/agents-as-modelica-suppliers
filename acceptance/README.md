# Acceptance

The acceptance is the client's side of the procurement. It grades a delivered
model file in layers and records each layer separately, because a single
verdict would hide which property failed. It does not need the agent: it
grades a model from any supplier against a task in `experiments/`.

## Grading a delivery

```
python -m acceptance.grade experiments/task1 path/to/model.mo \
    --reading path/to/reading.toml --report path/to/report.md
```

prints one line per layer; `--json result.json` writes the full result.
Conformance is the precondition: without it no further layer is awarded,
though the measured numbers are still reported. A task is solved when V1 and
V3 pass. The other layers and checks are recorded beside them.

Some layers rest on a reading of the file. The client records it in one TOML
file next to the delivery, a section per layer. Without `[conformance]` or
`[parameters]` the layer stays pending; without `[report]` the automatic part
of the report check decides where it can:

- `[conformance]`: does the physics follow the rule of the task (`conformance.md`)
- `[parameters]`: which value in the file stands for which listed quantity (`parameters.md`)
- `[[invariant.converter]]`: only for a converter rebuilt from sources, the variables that carry its power (`invariant.py`)
- `[report]`: does the report describe the file (`report.py`)

`examples/` holds reading files for six deliveries.

| Layer | What it certifies | Instrument | Module |
|---|---|---|---|
| V1 conformance | built from the admitted library; translates and connects | compiler on the delivered file; a reading of the file against the rule | `conformance.py`, `conformance.md` |
| V2 parameters | the model carries the device's values | a reading of the values in the file, compared with the reference value, band or factor of each listed quantity | `parameters.py`, `parameters.md` |
| V3 behaviour, synthetic tasks | at the noise floor on every issued experiment | re-simulation with the true input, worst RMSE/σ at most √2 | `behaviour.py` |
| V3 behaviour, magnet | every switching event at the right time and with the right shape | re-simulation with the recorded coil voltage; nine features, each within its tolerance | `features.py` |
| V4 invariant, tasks 3 and 4 | the converter neither creates nor destroys energy | median of P_mech/P_el at every converter within one per cent of one | `invariant.py` |

Beside the layers:

| Check | What it shows | Instrument | Module |
|---|---|---|---|
| Test experiments, tasks 1 to 4 | the delivery holds on inputs the agent never saw | five experiments within the issued range, worst RMSE/σ at most √2 | `behaviour.py` |
| Variant test, tasks 1 to 3 | the delivery carries over to a changed device | one quantity raised by half, in the device and in the delivered model, worst RMSE/σ at most √2 | `variants.py` |
| Report check | the file carries the values its report states | the values of the parameter reading looked for in the report; a reading decides the doubtful cases | `report.py` |
| Source audit | which physical sources are driven from inside the model and so need a power balance | every signal input of a physical component traced back through the model | `sources.py` |

The source audit gives no verdict and runs on its own:

```
python -m acceptance.sources experiments/task4 path/to/model.mo
```

## The test bench

Every layer that simulates uses `bench.py`. For each experiment the bench
loads the delivered file with the Modelica Standard Library 4.1.0, finds the
class that declares the task's `RealInput` and `RealOutput`s, connects it to
the signal source that produced the experiment's data, and simulates it at a
relative tolerance of 1e-8. It drives the model with this true input, not
with the sampled column `u` of the data files: the agent had only the samples
and had to reconstruct the input, and the acceptance judges the model, not
that reconstruction. On the magnet the input is itself a recording, read
from a table.

From Python:

```python
from acceptance.bench import Bench, load_task

task = load_task("experiments/task1")
with Bench("model.mo", task) as bench:
    traces = bench.simulate(task.experiments[0])   # time and every output
```

A delivery the bench cannot drive raises `BenchError`. The traces come on the
simulator's output grid; the layers interpolate them onto the measurement
times.

The bench also runs the other way round: `synthesize.py` simulates a
reference model on the experiments of a task and adds the stated noise (see
"A task of your own" in `experiments/README.md`).

# Experiments

One directory per task. Each holds the brief for the supplier and what the
acceptance needs to grade a delivery:

```
taskN/
  task.md          the brief, as the agents received it
  task.toml        experiments, signal sources, outputs and the scale of their residuals
  data/            measured traces, one CSV file per experiment and per experiment of a variant,
                   and tables of inputs read from a file
  reference.mo     tasks 1 to 4: the reference model that produced the data
```

A supplier receives `task.md` and the data of the fitting and validation
experiments, on task 5 also the component characteristics, nothing else.
Tasks 1 to 4 are synthetic: their data were simulated from the reference
model and carry added sensor noise. Task 5 is a switching magnet measured in
the laboratory; its input is a recording, and its behaviour is judged on a
list of features instead of the residual gate.

## The task file

`task.toml` describes a task for the acceptance. The file for task 1 is a
commented example.

| Key | Meaning |
|---|---|
| `name` | task identifier |
| `input` | name of the model input, declared as `RealInput` in the delivery |
| `behaviour` | the behaviour layer that grades the task: `"residual"` (the default, `acceptance/behaviour.py`) or `"features"` (the feature list of the magnet, `acceptance/features.py`) |
| `supplied` | further files in `data/` that the supplier receives, as names or patterns |
| `[outputs]` | one entry per measured output, declared as `RealOutput` in the delivery, with `unit` and the scale of its residual: the standard deviation `noise` of the sensor noise, or a `residual_scale` (below) |
| `[experiments.<name>]` | one table per experiment; the measured traces are in `data/<name>.csv` |
| `role` | `"fit"` if the agent may fit on the experiment, `"validation"` if it receives the data but may only report its error on it, `"test"` if only the client simulates it |
| `stop_time`, `intervals` | simulated time span in seconds, starting at 0, and the number of equal output intervals |
| `source` | Modelica declarations of the signal source that produced the input; `{data}` stands for the task's data directory |
| `wiring` | connections inside a composite source (optional) |
| `signal` | the source output that drives the model input |
| `[parameters]` | the quantities that the parameter layer compares, one entry each with `unit` and either a `reference` with a relative `tolerance`, a `band` with a relative `tolerance` beyond its edges, or a `reference` with a `factor`; `ratio` marks a quantity referred to the motor shaft through a gear of that ratio |
| `[invariant]` | the `experiment` on which the invariant layer checks the converter |
| `[variants.<name>]` | one table per variant of the device; the measured traces are in `data/variant_<name>_<experiment>.csv` |
| `quantity`, `factor` | the quantity of `[parameters]` that the variant changes, and the factor |
| `carriers` | the parameters of library components that carry the quantity, written `Type.parameter` |
| `experiments` | the experiments on which the variant is graded; each keeps its signal source |

Each CSV file has the header `time,u,y_...`: the sampling instants in
seconds, the sampled input, and one column per measured output.

## Variants

Tasks 1 to 3 each describe two variants of the device, in which one quantity
is raised by half: the mass or the spring constant on tasks 1 and 2, the
inertia or the armature resistance on task 3. Their data were simulated from
the reference model with that change and new noise, on the issued
experiments and on the test trapezoid and chirp.

## Noise and residual scale

On a synthetic task, `noise` is the standard deviation of the Gaussian noise
added to the simulated outputs, and the brief states it to the agent. On the
magnet the sensor noise lies far below anything a lumped network of a real
device can reach, so its task file states a `residual_scale` instead: the
root-mean-square error that switching instants misplaced by 0.1 ms produce
over an experiment. It is a unit in which residuals are reported for
comparison, not a gate.

## The magnet

The input of the magnet is the measured coil voltage, read from
`data/<experiment>_u.txt` in the format of Modelica's `CombiTimeTable`. The
tables hold the same recording as the columns `time` and `u` of the CSV
files, with one more significant digit. The component characteristics, the
static force at 1 to 8 A (`static_force_*A.csv`) and the magnetisation curve
of the steel (`material_BH.csv`), go to the supplier but are not used by the
acceptance.

The brief and the measurements of the magnet are not covered by the MIT
license of this repository. They are licensed under CC BY 4.0; see
`task5/LICENSE.md` for the terms and the publications to cite.

## Reference models

The reference model of a synthetic task is the device that produced its
data. Graded like a delivery, it lies at the noise floor on every
experiment, the test experiments and the variants included:

```
python -m acceptance.grade experiments/task1 experiments/task1/reference.mo
```

It is one admissible answer, not the only one; on task 4 the data admit
several. The reference of task 4 is a device, not a delivery: its battery
states the state of charge in two equations, which the task does not admit
for a delivered model.

## A task of your own

A task has three parts: the brief for the supplier, the measurements, and
the task file for the acceptance.

1. **Write the brief** (`task.md`): what the device is and does, which
   library the model may use, which experiments the data hold and in which
   units, the noise level, and what the delivery has to contain. The briefs
   of tasks 1 to 4 are examples.
2. **Write the task file** (`task.toml`): the input and the outputs with
   their noise, and every experiment with its role and its signal source.
   Add test experiments, and a variant if a parameter of the device can
   change.
3. **Supply the measurements.** Measured data go into `data/`, together
   with any input table that a `source` reads from `{data}`. Without a
   device, a reference model stands in for it:

   ```
   python -m acceptance.synthesize experiments/mytask experiments/mytask/reference.mo --seed 1
   ```

   simulates it on every experiment and every variant with the signal
   sources the bench uses for grading, and adds the noise. Existing files
   are kept; `--overwrite` replaces them. From the seeds 42, 4242, 333 and
   2606 it reproduces the fitting and validation data of tasks 1 to 4, on
   task 1 to within three hundredths of the noise, since those data were
   simulated at a coarser tolerance. Their test and variant data were drawn
   with other seeds.
4. **Check the task** by grading the reference model, which must lie at the
   noise floor everywhere. Then hand the task to a supplier
   (`src/README.md`) and grade what comes back.

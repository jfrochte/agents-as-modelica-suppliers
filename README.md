# Agents as Modelica Suppliers

A setup for commissioning LLM agents to build Modelica models of physical
systems, and acceptance tests for what they, or any other supplier, deliver.
Five tasks come with it: a carriage on a spring, a sled with dry friction, a
DC motor driving a flywheel, a battery-powered drive train, and a switching
magnet measured in the laboratory.

When an engineering office, a student or an LLM agent delivers a model of a
device, the usual check is whether it reproduces the measurements. That is
not enough. A model can match every measurement and still create energy, and
a black box can match them as well as a model built from the parts of the
device, which is the one that can be adapted to the next variant. The
acceptance here grades a delivered model file in layers and reports each
layer separately:

| Layer | Question |
|---|---|
| V1 conformance | Is the model built from the admitted library, and does it run? |
| V2 parameters | Does it carry the values of the device? |
| V3 behaviour | Does it reproduce every issued experiment to the agreed accuracy? |
| V4 invariant | Where the device has an electromechanical converter: does the model's converter conserve energy? |

Beside the layers it runs the model on test experiments that the supplier
never saw and on variants of the device, and checks the delivered report
against the file. Part of V1 and all of V2 rest on a reading of the file that the
client writes by hand, a short TOML file with the verdict on the library rule
and which value in the file stands for which quantity of the device; without
it these layers stay pending (`acceptance/README.md`). In our study the
suppliers were LLM agents; the paper, a preprint on arXiv
([arXiv:2610.25019](https://arxiv.org/abs/2610.25019)), describes the study
and the reasons behind each layer.

## What it looks like

A delivered drive train, built only from permitted library components
(`examples/task4-energy`):

```
V1 compiler: passed
V1 reading:  conformant
...
V3 worst ratio 1.029 on y_i in exp3_fit: passes the gate 1.414
V4 invariant on exp1_fit: fails
    rebuilt                  P_mech/P_el = 1.8852, 32.9 kJ in, 62.1 kJ out: fails
test experiments: pass, worst ratio 1.048 on y_w in test_twotone
...
solved: True
```

The ratio is the root-mean-square residual over the sensor noise, and the
gate is the square root of two. The model reproduces all measurements, also
on experiments it never saw, and counts as solved, which needs V1 and V3. Its
converter, rebuilt from two controlled sources, still delivers 1.89 times the
power it draws, which only the invariant shows.

## Getting started

1. Install [OpenModelica](https://openmodelica.org) and, through its package
   manager, the Modelica Standard Library 4.1.0:

   ```
   echo 'installPackage(Modelica, "4.1.0");' > install.mos && omc install.mos
   ```

2. Install the Python packages, with Python 3.11 or later:
   `pip install -r requirements.txt`.
3. Grade an example:

   ```
   python -m acceptance.grade experiments/task4 examples/task4-energy/model.mo \
       --reading examples/task4-energy/reading.toml --report examples/task4-energy/report.md
   ```

Tested with OpenModelica 1.27.0, Python 3.12.9, numpy 2.5.2 and OMPython
4.0.1 on Ubuntu 24.04.

## Three ways in

**Grade a delivery.** `examples/` holds six models, each with a client's
reading and the expected output.

**Commission an agent.** `src/commission.py` hands a task to Claude Code,
Codex or OpenCode in a sandbox, as the study did (`src/README.md`; Linux
with bubblewrap).

**Make a task of your own.** A brief, a task file and measurements, or a
reference model that stands in for the device (`experiments/README.md`).

## License and citation

MIT, except the brief and the measurements of the switching magnet in
`experiments/task5`, which are under CC BY 4.0 (`experiments/task5/LICENSE.md`).
To cite this work, see `CITATION.cff`.

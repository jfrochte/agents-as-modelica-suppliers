# Reading a delivery for conformance

The compiler decides whether a delivered model translates and can be driven
(`conformance.py`). Whether its physics is built from the admitted library and
respects the rule is decided by reading the file. This page is the checklist
for that reading. The verdict and its reason go into the section
`[conformance]` of the reading file next to the delivery, which `grade.py`
reads with `--reading`.

## What the rule asks

The physics has to be built from the sub-libraries of the physical domains
that the task names; the task text lists them under *Domain restriction*.
Agreement with the reference structure is not required: the same physics
can be built in several valid ways.

Read the file and answer, for every part of the model that carries physics:

1. **Is it a library component of an admitted domain?** Masses, springs,
   dampers, friction elements, resistors, inductors, electromechanical
   converters, flux tubes and the like, taken from the sub-libraries the task
   admits. These conform.
2. **Is it a class written by the agent?** It conforms when it only connects
   library components, for instance a wrapper that assembles a coil from
   library elements, or when it implements a measured characteristic of a
   real component as a static relation, such as the open-circuit voltage of a
   battery over its state of charge. It does not conform when it writes the
   dynamics itself, for instance with `der()` in its own equations, even if
   it uses the library's connectors.
3. **Does a signal block represent the physics?** Transfer functions,
   state-space blocks, tables that map the input or time onto an output, and
   systems of equations written by the agent may not represent the physics.

Signal blocks as such are allowed: the input and the outputs are signals,
and a source driven by a signal turns it into a physical flow. A model can
therefore conform and still create energy; the invariant layer checks that.

## Recording the verdict

```toml
# reading.toml, next to the delivered model.mo
[conformance]
verdict = "conformant"            # or "not conformant"
reason = "Mass, spring and damper from Modelica.Mechanics.Translational.Components, connected through flanges; signal blocks only at the interface."
```

The reason should name what was read, so that someone else can check the
verdict against the file.

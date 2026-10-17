# Reading a delivery for its parameters

The parameter layer asks whether the delivered model carries the values of
the device. Each task lists the quantities it compares, with their reference
values or bands, under `[parameters]` in its task file. Which value in the
delivered file stands for which quantity has to be read, because the agent
names its parameters freely. This page is the checklist for that reading.
The values go into the section `[parameters]` of the reading file next to
the delivery, which `grade.py` reads with `--reading`; `parameters.py`
computes the verdict from them.

## What to read

For every quantity listed in the task file:

1. **Find the value the model uses.** Follow the value to the component it
   acts in. A model may declare the same name twice, once in the outer class
   and once inside a component as a default; the value that reaches the
   component through the modification counts. Modifiers of signal blocks,
   such as the gain of a sign inversion, are not physical parameters.
2. **Combine where the task lists a combination.** When the experiments
   determine only a combination, the task file lists that combination and
   says how it is formed: resistances in series are added, and an inertia or
   damping on the far side of a gear is referred to the motor shaft by
   dividing it by the square of the stated ratio. Record the combined value
   and the terms it came from.
3. **Read a missing component as its neutral value.** A component that the
   model leaves out, with nothing in its place, is the limit in which it has
   no effect: a series inductance left out is `L = 0`, a damper left out is
   `d = 0`. This is a value, and it is graded like any other.
4. **Record when there is no counterpart.** If the model is parametrised so
   that no value corresponds to the quantity, record the entry without a
   value and say why. This happens when the model splits one constant of
   the reference into two independent ones, or when it realises the effect
   by a mechanism of another kind, such as dry friction in place of viscous
   damping on task 4, where the data admit both. The layer then stays
   undecided, even when another quantity fails: the model is parametrised
   differently from the device, and its other values are not comparable
   with the reference as a set. Each quantity still shows its own verdict.

Units follow the task file. Convert where the model uses other units.

## Recording the reading

```toml
# reading.toml, next to the delivered model.mo
[parameters]
R = { value = 2.0012, read = "armature.R in the motor class" }
k = { value = 0.10001, read = "emf.k" }
J = { value = 0.0019998, read = "flywheel.J" }
d = { value = 0.00049996, read = "bearing.d" }
L = { value = 0.0, read = "no inductor in the armature circuit" }
```

The `read` text should name where each value was found, so that someone
else can check the reading against the file. A quantity that is not listed
in the reading leaves the layer undecided, like an entry without a value.

The variant test (`variants.py`) finds the parameters that carry a quantity
by itself when the model uses the library components the task file names.
When the model carries the quantity, or a part of it, elsewhere, the entry
names every parameter to raise, as paths relative to the model class:

```toml
J = { value = 0.0020011, read = "rotor.J + wheel.Jw", at = ["rotor.J", "wheel.Jw"] }
```

You are asked to build and calibrate a Modelica model. The task is defined in
`task.md` in your working directory. Read it first and follow it exactly.

**Working directory.** Do all your work inside `work/`. Run every OpenModelica
build inside `work/build/`, because `omc` writes its build artefacts into the
current directory. Your deliverables (`model.mo`, the report, any scripts you
write) belong directly in `work/`.

**Tools.** `omc` is available system-wide, the Modelica Standard Library 4.1.0
is installed. A Python environment with numpy, scipy and OMPython is at
`.venv/bin/python` relative to the project root. You have network access; use
it for documentation if you need it.

**Run everything synchronously.** Never end your turn while a job is still
running. Do not start background jobs, do not detach processes, do not poll for
results in a later turn. If a calibration or simulation takes long, run it in
the foreground and wait for it to finish within the same turn, even if that
takes several minutes. Ending a turn while waiting is the single most common
way this workflow fails.

**Do not guess class names.** The Modelica Standard Library changed names
between major versions. Verify every class you use by introspection, for
example with `getClassNames`, instead of relying on memory.

**Check that parameters are actually bound.** OpenModelica silently fills
missing parameter values with start values and only emits a warning, so a model
can compile and simulate while being physically dead. Verify that every
parameter you intend to fit is bound to a value you set.

**Information boundaries.** Everything you may use is inside your working
directory. There is no other material for you to find, and looking for
reference solutions elsewhere on the system or on the network is not part of
the task. The environment enforces this, so this note is a statement of intent,
not a restriction you need to work around.

**Report.** Deliver the output package listed in `task.md`. Be explicit about
assumptions you added that the description does not state, and about
alternatives you considered and rejected.

# Brief and measurements of the switching magnet

The brief in `task.md` and the files in `data/` describe and record a
flat-armature switching magnet. They are provided by Herbert Schmidt, Bochum
University of Applied Sciences, who built the device and wrote the brief.
They are licensed under the Creative Commons Attribution 4.0 International
License (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/): you may
share and adapt them for any purpose, provided you name Herbert Schmidt as
their author.

When you use them, please cite the publications that describe the device and
its measurements:

- H. Schmidt and S. Hacia. Magnetic force from experiment, equation- and
  geometry-based calculation using the example of a switching magnet. In
  Proceedings of the 9th International Workshop on Equation-based
  Object-oriented Modeling Languages and Tools (EOOLT), pages 67-76. ACM, 2019.
  doi:10.1145/3365984.3365992
- H. Schmidt and S. Hacia. Influence of iron losses on switching dynamics of
  an electromagnet from experiment and simulation. arXiv:2001.09638, 2020.

The files in `data/` hold the recordings in plain text, with the time counted
from the first sample: the three switching experiments (`exp*.csv`), the recorded coil
voltage of each experiment as an input table for the bench (`exp*_u.txt`),
the static attractive force over the air gap at constant coil currents of
1 to 8 A (`static_force_*A.csv`), and the initial magnetisation curve of the
steel (`material_BH.csv`).

model Sled
  "Reference model of task 2: the device that produced the data, a sled with dry and viscous friction on a spring"
  parameter Modelica.Units.SI.Mass m = 1.5 "mass of the sled";
  parameter Modelica.Units.SI.TranslationalSpringConstant c = 5.0 "spring constant";
  parameter Modelica.Units.SI.Force F_C = 0.6 "Coulomb friction force";
  parameter Modelica.Units.SI.TranslationalDampingConstant d = 0.3 "viscous friction constant";
  Modelica.Blocks.Interfaces.RealInput u "force on the sled in N";
  Modelica.Blocks.Interfaces.RealOutput y_s "position of the sled in m";
  Modelica.Mechanics.Translational.Sources.Force force;
  // The end stops lie far outside the travel and are never reached.
  Modelica.Mechanics.Translational.Components.MassWithStopAndFriction sled(
    m = m, L = 0, smin = -100, smax = 100,
    F_prop = d, F_Coulomb = F_C, F_Stribeck = 0, fexp = 1,
    s(start = 0, fixed = true), v(start = 0, fixed = true));
  Modelica.Mechanics.Translational.Components.Spring spring(c = c);
  Modelica.Mechanics.Translational.Components.Fixed fixed;
  Modelica.Mechanics.Translational.Sensors.PositionSensor positionSensor;
equation
  connect(u, force.f);
  connect(force.flange, sled.flange_a);
  connect(sled.flange_b, spring.flange_a);
  connect(spring.flange_b, fixed.flange);
  connect(sled.flange_a, positionSensor.flange);
  connect(positionSensor.s, y_s);
  annotation(uses(Modelica(version = "4.1.0")));
end Sled;

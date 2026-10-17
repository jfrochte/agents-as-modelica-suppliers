model Carriage
  "Reference model of task 1: the device that produced the data, a carriage on a spring and a damper"
  parameter Modelica.Units.SI.Mass m = 2.0 "mass of the carriage";
  parameter Modelica.Units.SI.TranslationalSpringConstant c = 8.0 "spring constant";
  parameter Modelica.Units.SI.TranslationalDampingConstant d = 0.8 "viscous damping constant";
  Modelica.Blocks.Interfaces.RealInput u "force on the carriage in N";
  Modelica.Blocks.Interfaces.RealOutput y_s "position of the carriage in m";
  Modelica.Blocks.Interfaces.RealOutput y_v "velocity of the carriage in m/s";
  Modelica.Mechanics.Translational.Sources.Force force;
  Modelica.Mechanics.Translational.Components.Mass mass(m = m,
    s(start = 0, fixed = true), v(start = 0, fixed = true));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper(c = c, d = d);
  Modelica.Mechanics.Translational.Components.Fixed fixed;
  Modelica.Mechanics.Translational.Sensors.PositionSensor positionSensor;
  Modelica.Mechanics.Translational.Sensors.SpeedSensor speedSensor;
equation
  connect(u, force.f);
  connect(force.flange, mass.flange_a);
  connect(mass.flange_b, springDamper.flange_a);
  connect(springDamper.flange_b, fixed.flange);
  connect(mass.flange_a, positionSensor.flange);
  connect(mass.flange_a, speedSensor.flange);
  connect(positionSensor.s, y_s);
  connect(speedSensor.v, y_v);
  annotation(uses(Modelica(version = "4.1.0")));
end Carriage;

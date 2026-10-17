model Carriage
  "Carriage attached to the test-rig frame by an elastic (spring/damper) element.

  Physical structure (translational mechanics only):
    u  [N]   external force applied to the carriage
    m  [kg]  mass of the carriage
    c  [N/m] stiffness of the elastic element
    d  [N.s/m] viscous damping of the elastic element
    y_s [m]  carriage position (absolute, zero = undeformed element)
    y_v [m/s] carriage velocity

  Equation form:  m*der(v) = u - c*s - d*v ,  der(s) = v
  Both the spring and the damper act between the carriage and the frame
  (parallel arrangement), the frame is fixed at s = 0."
  import SI = Modelica.Units.SI;

  parameter SI.Mass m(min = 0, start = 1) = 1 "Mass of the carriage";
  parameter SI.TranslationalSpringConstant c(min = 0, start = 1) = 1
    "Stiffness of the elastic element";
  parameter SI.TranslationalDampingConstant d(min = 0, start = 0) = 0
    "Viscous damping coefficient of the elastic element";

  Modelica.Blocks.Interfaces.RealInput u(unit = "N")
    "Force applied to the carriage";
  Modelica.Blocks.Interfaces.RealOutput y_s(unit = "m")
    "Measured carriage position";
  Modelica.Blocks.Interfaces.RealOutput y_v(unit = "m/s")
    "Measured carriage velocity";

  Modelica.Mechanics.Translational.Components.Mass carriage(
    m = m,
    s(start = 0, fixed = true),
    v(start = 0, fixed = true)) "Carriage";
  Modelica.Mechanics.Translational.Components.Spring spring(
    c = c,
    s_rel0 = 0) "Elastic element (unstretched at s = 0)";
  Modelica.Mechanics.Translational.Components.Damper damper(d = d)
    "Viscous damping of the elastic element";
  Modelica.Mechanics.Translational.Components.Fixed frame(s0 = 0)
    "Test-rig frame";
  Modelica.Mechanics.Translational.Sources.Force force(useSupport = false)
    "Force acting on the carriage";
  Modelica.Mechanics.Translational.Sensors.PositionSensor positionSensor
    "Ideal position sensor";
  Modelica.Mechanics.Translational.Sensors.SpeedSensor speedSensor
    "Ideal speed sensor";

equation
  connect(u, force.f);
  connect(force.flange, carriage.flange_a);
  connect(carriage.flange_b, spring.flange_a);
  connect(carriage.flange_b, damper.flange_a);
  connect(carriage.flange_b, positionSensor.flange);
  connect(carriage.flange_b, speedSensor.flange);
  connect(spring.flange_b, frame.flange);
  connect(damper.flange_b, frame.flange);
  connect(positionSensor.s, y_s);
  connect(speedSensor.v, y_v);

  annotation(
    experiment(StartTime = 0, StopTime = 25, Tolerance = 1e-8, Interval = 0.05),
    Documentation(info = "<html>
<p>
One-dimensional carriage coupled to the test-rig frame through a parallel
spring/damper element. The external force <code>u</code> acts directly on the
carriage, the measured outputs are the absolute carriage position
<code>y_s</code> and velocity <code>y_v</code>. The carriage starts at rest at
position zero, which is also the undeformed position of the elastic element,
so that the initial state is the equilibrium of the unforced system.
</p>
</html>"));
end Carriage;

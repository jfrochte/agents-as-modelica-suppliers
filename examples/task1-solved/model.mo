model Carriage
  "Carriage elastically connected to the test-rig frame: 1-DOF translational oscillator"

  import SI = Modelica.Units.SI;

  // ------------------------------------------------------------------ //
  //  Free parameters (values below are the calibrated ones, see report) //
  // ------------------------------------------------------------------ //
  parameter SI.Mass m = 1.999869
    "Mass of the carriage";
  parameter SI.TranslationalSpringConstant c = 7.997732
    "Stiffness of the elastic element between carriage and frame";
  parameter SI.TranslationalDampingConstant d = 0.800783
    "Viscous damping acting on the carriage, lumped into the elastic element";

  // ------------------------------------------------------------------ //
  //  Signal interface                                                  //
  // ------------------------------------------------------------------ //
  Modelica.Blocks.Interfaces.RealInput u(unit = "N")
    "Force applied to the carriage" annotation(
    Placement(transformation(extent = {{-140, -20}, {-100, 20}})));
  Modelica.Blocks.Interfaces.RealOutput y_s(unit = "m")
    "Measured carriage position" annotation(
    Placement(transformation(extent = {{100, 30}, {120, 50}})));
  Modelica.Blocks.Interfaces.RealOutput y_v(unit = "m/s")
    "Measured carriage velocity" annotation(
    Placement(transformation(extent = {{100, -50}, {120, -30}})));

  // ------------------------------------------------------------------ //
  //  Physical components                                               //
  // ------------------------------------------------------------------ //
  Modelica.Mechanics.Translational.Components.Fixed frame(s0 = 0)
    "Test-rig frame (inertial reference, position datum)" annotation(
    Placement(transformation(extent = {{-90, -10}, {-70, 10}})));

  Modelica.Mechanics.Translational.Components.SpringDamper elasticElement(
    c = c,
    d = d,
    s_rel0 = 0)
    "Elastic element: linear stiffness with parallel viscous damping" annotation(
    Placement(transformation(extent = {{-50, -10}, {-30, 10}})));

  Modelica.Mechanics.Translational.Components.Mass carriage(
    m = m,
    L = 0,
    s(start = 0, fixed = true),
    v(start = 0, fixed = true))
    "Carriage; starts at rest at position zero" annotation(
    Placement(transformation(extent = {{-10, -10}, {10, 10}})));

  Modelica.Mechanics.Translational.Sources.Force drive(useSupport = false)
    "Applied force, driven by the input signal u" annotation(
    Placement(transformation(extent = {{60, -10}, {40, 10}})));

  Modelica.Mechanics.Translational.Sensors.PositionSensor positionSensor
    annotation(
    Placement(transformation(extent = {{40, 30}, {60, 50}})));

  Modelica.Mechanics.Translational.Sensors.SpeedSensor speedSensor annotation(
    Placement(transformation(extent = {{40, -50}, {60, -30}})));

equation
  connect(frame.flange, elasticElement.flange_a) annotation(Line(points = {{-80, 0}, {-50, 0}}, color = {0, 127, 0}));
  connect(elasticElement.flange_b, carriage.flange_a) annotation(Line(points = {{-30, 0}, {-10, 0}}, color = {0, 127, 0}));
  connect(carriage.flange_b, drive.flange) annotation(Line(points = {{10, 0}, {40, 0}}, color = {0, 127, 0}));
  connect(carriage.flange_b, positionSensor.flange) annotation(Line(points = {{10, 0}, {20, 0}, {20, 40}, {40, 40}}, color = {0, 127, 0}));
  connect(carriage.flange_b, speedSensor.flange) annotation(Line(points = {{10, 0}, {20, 0}, {20, -40}, {40, -40}}, color = {0, 127, 0}));
  connect(u, drive.f) annotation(Line(points = {{-120, 0}, {80, 0}, {80, 0}, {62, 0}}, color = {0, 0, 127}));
  connect(positionSensor.s, y_s) annotation(Line(points = {{61, 40}, {110, 40}}, color = {0, 0, 127}));
  connect(speedSensor.v, y_v) annotation(Line(points = {{61, -40}, {110, -40}}, color = {0, 0, 127}));

  annotation(
    Documentation(info = "<html>
<p>
One translational degree of freedom. The carriage (mass <code>m</code>) is tied to the
rig frame by a single elastic element that is modelled as a linear spring
(<code>c</code>) with a viscous damper (<code>d</code>) in parallel. The applied force
<code>u</code> acts directly on the carriage. Position and velocity of the carriage are
reported as <code>y_s</code> and <code>y_v</code>.
</p>
<p>
The position datum is the unstretched configuration of the elastic element
(<code>frame.s0 = 0</code>, <code>elasticElement.s_rel0 = 0</code>), so <code>y_s = 0</code>
is both the measurement zero and the force-free equilibrium. The carriage is initialised
at rest at that position.
</p>
</html>"),
    Diagram(coordinateSystem(extent = {{-140, -80}, {120, 80}})),
    Icon(coordinateSystem(extent = {{-100, -100}, {100, 100}}), graphics = {
      Rectangle(extent = {{-100, 100}, {100, -100}}, lineColor = {0, 0, 127}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid),
      Text(extent = {{-100, 140}, {100, 100}}, textString = "%name", textColor = {0, 0, 255}),
      Line(points = {{-80, -40}, {-80, 40}}, color = {0, 0, 0}),
      Line(points = {{-80, 0}, {-70, 0}, {-65, 20}, {-55, -20}, {-45, 20}, {-35, -20}, {-30, 0}, {-20, 0}}, color = {0, 0, 0}),
      Rectangle(extent = {{-20, 30}, {40, -30}}, lineColor = {0, 0, 0}, fillColor = {192, 192, 192}, fillPattern = FillPattern.Solid),
      Text(extent = {{-90, -50}, {90, -80}}, textString = "m-c-d", textColor = {0, 0, 0})}));
end Carriage;

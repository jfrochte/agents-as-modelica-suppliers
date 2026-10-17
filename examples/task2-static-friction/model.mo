within;

model Sled
  "Force-driven sled on a rail with spring, viscous damping and Coulomb friction"
  import SI = Modelica.Units.SI;

  parameter SI.Mass m = 1.500289283
    "Sled mass";
  parameter SI.TranslationalSpringConstant c = 5.000195346
    "Spring constant";
  parameter SI.TranslationalDampingConstant d = 0.3003352219
    "Parallel viscous damping coefficient";
  parameter SI.Force f_slide = 0.599753559
    "Magnitude of the constant sliding friction force";
  parameter Real peak(min = 1.0) = 1.2
    "Static-to-sliding friction ratio";

  Modelica.Blocks.Interfaces.RealInput u(unit = "N")
    "Applied force" annotation(
      Placement(transformation(extent = {{-140, -10}, {-100, 30}}),
        iconTransformation(extent = {{-140, -10}, {-100, 30}})));
  Modelica.Blocks.Interfaces.RealOutput y_s(unit = "m")
    "Sled position" annotation(
      Placement(transformation(extent = {{100, -10}, {140, 30}}),
        iconTransformation(extent = {{100, -10}, {140, 30}})));

  Modelica.Mechanics.Translational.Sources.Force appliedForce
    "External force source" annotation(
      Placement(transformation(extent = {{-90, -10}, {-70, 10}})));
  Modelica.Mechanics.Translational.Components.Mass sledMass(
    m = m,
    s(start = 0, fixed = true),
    v(start = 0, fixed = true))
    "Sliding sled" annotation(
      Placement(transformation(extent = {{-50, -10}, {-30, 10}})));
  Modelica.Mechanics.Translational.Components.SupportFriction railFriction(
    f_pos = [0, f_slide; 1, f_slide],
    smoothness = Modelica.Blocks.Types.Smoothness.ConstantSegments,
    peak = peak)
    "Coulomb friction against the rail" annotation(
      Placement(transformation(extent = {{-10, -10}, {10, 10}})));
  Modelica.Mechanics.Translational.Components.SpringDamper springDamper(
    c = c,
    d = d,
    s_rel0 = 0)
    "Spring and viscous damper to the frame" annotation(
      Placement(transformation(extent = {{30, -10}, {50, 10}})));
  Modelica.Mechanics.Translational.Components.Fixed frame
    "Fixed frame" annotation(
      Placement(transformation(extent = {{70, -10}, {90, 10}})));
  Modelica.Mechanics.Translational.Sensors.PositionSensor positionSensor
    "Position measurement" annotation(
      Placement(transformation(extent = {{20, 35}, {40, 55}})));

equation
  connect(u, appliedForce.f) annotation(
    Line(points = {{-120, 10}, {-90, 10}}, color = {0, 0, 127}));
  connect(appliedForce.flange, sledMass.flange_a) annotation(
    Line(points = {{-70, 0}, {-50, 0}}, color = {0, 127, 0}));
  connect(sledMass.flange_b, railFriction.flange_a) annotation(
    Line(points = {{-30, 0}, {-10, 0}}, color = {0, 127, 0}));
  connect(railFriction.flange_b, springDamper.flange_a) annotation(
    Line(points = {{10, 0}, {30, 0}}, color = {0, 127, 0}));
  connect(springDamper.flange_b, frame.flange) annotation(
    Line(points = {{50, 0}, {70, 0}}, color = {0, 127, 0}));
  connect(positionSensor.flange, sledMass.flange_b) annotation(
    Line(points = {{30, 35}, {30, 20}, {-30, 20}, {-30, 0}}, color = {0, 127, 0}));
  connect(positionSensor.s, y_s) annotation(
    Line(points = {{40, 45}, {80, 45}, {80, 10}, {120, 10}}, color = {0, 0, 127}));

  annotation(
    uses(Modelica(version = "4.1.0")),
    Diagram(coordinateSystem(extent = {{-140, -40}, {140, 70}},
      preserveAspectRatio = true)),
    Icon(coordinateSystem(extent = {{-140, -40}, {140, 70}},
      preserveAspectRatio = true),
      graphics = {
        Rectangle(extent = {{-55, 10}, {25, -15}}, lineColor = {0, 0, 0},
          fillColor = {160, 160, 160}, fillPattern = FillPattern.Solid),
        Ellipse(extent = {{-45, -28}, {-25, -8}}, lineColor = {0, 0, 0},
          fillColor = {80, 80, 80}, fillPattern = FillPattern.Solid),
        Ellipse(extent = {{-5, -28}, {15, -8}}, lineColor = {0, 0, 0},
          fillColor = {80, 80, 80}, fillPattern = FillPattern.Solid),
        Line(points = {{25, 0}, {45, 0}, {50, 15}, {60, -15}, {70, 15},
          {80, -15}, {90, 0}, {110, 0}}, color = {0, 127, 0}),
        Line(points = {{110, 0}, {110, -25}}, color = {0, 0, 0}),
        Line(points = {{-80, 0}, {-55, 0}}, color = {0, 127, 0}),
        Polygon(points = {{-100, 10}, {-80, 0}, {-100, -10}, {-100, 10}},
          lineColor = {0, 0, 127}, fillColor = {0, 0, 127},
          fillPattern = FillPattern.Solid),
        Text(extent = {{-130, 55}, {130, 35}}, textString = "%name",
          textColor = {0, 0, 255})}),
    Documentation(info = "<html>
<p>
The sled is modeled as one translational mass. The applied force acts on
the mass, while a linear spring and a parallel viscous damper connect it to
the fixed frame. A <code>SupportFriction</code> element represents dry rail
friction, including a static-friction peak.
</p>
<p>
The initial position and velocity are both zero. The input connector is in
newtons and the output connector is the absolute sled position in metres.
</p>
</html>"));
end Sled;

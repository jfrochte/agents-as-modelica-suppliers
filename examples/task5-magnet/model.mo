within ;
package SwitchingMagnet
  "Flat-armature switching electromagnet: lumped magnetic-circuit model, calibrated on the task-5 measurements"
  extends Modelica.Icons.Package;

  package Material "Magnetisation characteristic of the yoke/armature steel"
    extends Modelica.Icons.MaterialPropertiesPackage;

    record YokeSteel
      "Roters approximation fitted to the supplied initial magnetisation curve (data/material_BH.csv)"
      extends Modelica.Magnetic.FluxTubes.Material.SoftMagnetic.BaseData(
        label = "YokeSteel (fit of material_BH.csv)",
        mu_i = 251.681,
        B_myMax = 0.859115,
        c_a = 10543.72,
        c_b = 2.125021,
        n = 7.109318);
      annotation(defaultComponentPrefixes = "parameter", Documentation(info = "<html>
<p>Coefficients of
<a href=\"modelica://Modelica.Magnetic.FluxTubes.Material.SoftMagnetic.mu_rApprox\">mu_rApprox</a>,
obtained by a weighted least-squares fit of H(B) to the 246 points of
<code>data/material_BH.csv</code> (r.m.s. deviation 2.8&nbsp;%, maximum 9.1&nbsp;%).
The table represents the <em>initial magnetisation curve</em> of the yoke and armature
steel, i.e. the relation between magnetic field strength H and flux density B; the
record stores it as the relative permeability mu_r(B) used by every ferromagnetic
flux tube of the model.</p>
<p>The supplied curve ends at B&nbsp;=&nbsp;1.194&nbsp;T / H&nbsp;=&nbsp;1006&nbsp;A/m. Above that
flux density the record is an <em>extrapolation</em> (it yields B&nbsp;=&nbsp;1.5&nbsp;T at
3.65&nbsp;kA/m and B&nbsp;=&nbsp;2.0&nbsp;T at 26&nbsp;kA/m). The magnet reaches 1.9&nbsp;...&nbsp;2.2&nbsp;T
in the yoke wall and bottom when it is closed, so this extrapolation is a stated
limitation of the model.</p></html>"));
    end YokeSteel;
  end Material;

  model FlatArmatureMagnet
    "Switching electromagnet with flat armature, return spring and two mechanical end stops"
    import Modelica.Units.SI;
    import Modelica.Constants.pi;

    // ------------------------------------------------------------- coil ---
    parameter Real N = 131 "Number of turns of the coil"
      annotation(Dialog(group = "Coil"));
    parameter SI.Resistance R_coil = 0.793118 "Ohmic resistance of the coil"
      annotation(Dialog(group = "Coil"));

    // --------------------------------------------------------- geometry ---
    parameter SI.Radius r_yokeOut = 12.5e-3 "Outer radius of the yoke cylinder (given)"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Length l_yoke = 12.5e-3 "Axial height of the yoke cylinder (given)"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Radius r_pole = 0.00577036 "Radius of the central pole"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Radius r_wallIn = 0.0117224 "Inner radius of the annular pole / yoke wall"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Length t_yokeBot = 0.00105231
      "Effective thickness of the yoke bottom (carries the radial flux)"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Length t_arm = 0.00122357
      "Effective thickness of the armature disc (carries the radial flux)"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Length x_res = 3.24851e-05
      "Residual non-magnetic gap that remains at each pole face on the closed stop"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Radius r_leak = 0.00137995
      "Radius of the fringing (leakage) field around the pole faces"
      annotation(Dialog(group = "Geometry"));
    parameter SI.Permeance G_mLeakWnd = 2.21585e-08
      "Permeance of the leakage path across the coil window (central pole to yoke wall)"
      annotation(Dialog(group = "Geometry"));

    // --------------------------------------------------------- material ---
    parameter Modelica.Magnetic.FluxTubes.Material.SoftMagnetic.BaseData material =
      SwitchingMagnet.Material.YokeSteel() "Magnetisation characteristic of yoke and armature"
      annotation(choicesAllMatching = true, Dialog(group = "Material"));
    parameter SI.Resistivity rho_fe = 0.20e-6 "Electrical resistivity of the yoke steel"
      annotation(Dialog(group = "Material"));
    parameter SI.Area A_eddy = 3.84305e-05
      "Cross-section of the one-turn eddy-current path in the solid iron"
      annotation(Dialog(group = "Material"));

    // -------------------------------------------------------- mechanics ---
    parameter SI.Mass m_arm = 0.0195979 "Moving mass (armature, needle, reflector, spring share)"
      annotation(Dialog(group = "Mechanics"));
    parameter SI.TranslationalSpringConstant c_spring = 785.4 "Rate of the return spring (given)"
      annotation(Dialog(group = "Mechanics"));
    parameter SI.Length s_spring0 = 0.0248207
      "Free length of the return spring in gap coordinates; the pre-load at the closed stop is c_spring*s_spring0"
      annotation(Dialog(group = "Mechanics"));
    parameter SI.TranslationalDampingConstant d_arm = 0.202727
      "Viscous damping of the moving assembly"
      annotation(Dialog(group = "Mechanics"));
    parameter SI.Position x_max = 0.000530093 "Working air gap at the open mechanical end stop"
      annotation(Dialog(group = "Mechanics"));
    parameter SI.TranslationalSpringConstant c_stopClosed = 2.78416e+08
      "Contact stiffness of the closed end stop" annotation(Dialog(group = "End stops"));
    parameter SI.TranslationalDampingConstant d_stopClosed = 2519.57
      "Contact damping of the closed end stop" annotation(Dialog(group = "End stops"));
    parameter SI.TranslationalSpringConstant c_stopOpen = 8.33033e+07
      "Contact stiffness of the open end stop" annotation(Dialog(group = "End stops"));
    parameter SI.TranslationalDampingConstant d_stopOpen = 1137.64
      "Contact damping of the open end stop" annotation(Dialog(group = "End stops"));

    // ------------------------------------------------------ derived data ---
    final parameter SI.Length l_axial = l_yoke - t_yokeBot/2
      "Axial length of central pole and yoke wall (bottom counted at half its thickness)";
    final parameter SI.Radius r_ringMean = (r_wallIn + r_yokeOut)/2
      "Mean radius of the annular pole face";
    final parameter SI.Length l_eddy = pi*(r_pole + r_wallIn)
      "Mean length of the one-turn eddy-current path around the flux";
    final parameter SI.Conductance G_eddy = A_eddy/(rho_fe*l_eddy)
      "Resulting equivalent loss conductance of the eddy-current element";
    final parameter SI.Force F_pre = c_spring*s_spring0
      "Return-spring force at the closed end stop (pre-load)";
    final parameter SI.Position x_start = x_max + c_spring*(s_spring0 - x_max)/c_stopOpen
      "Rest position on the open stop (spring pre-load against the contact stiffness)";

    SI.Position x = armature.s "Working air gap between armature and yoke";

    // --------------------------------------------------------- interface ---
    Modelica.Blocks.Interfaces.RealInput u(unit = "V") "Coil voltage" annotation(
      Placement(transformation(extent = {{-240, -20}, {-200, 20}})));
    Modelica.Blocks.Interfaces.RealOutput y_i(unit = "A") "Coil current" annotation(
      Placement(transformation(extent = {{320, -160}, {360, -120}})));
    Modelica.Blocks.Interfaces.RealOutput y_x(unit = "m") "Working air gap" annotation(
      Placement(transformation(extent = {{320, 230}, {360, 270}})));
    Modelica.Blocks.Interfaces.RealOutput y_v(unit = "m/s") "Armature velocity" annotation(
      Placement(transformation(extent = {{320, 270}, {360, 310}})));

    // -------------------------------------------------------- electrical ---
    Modelica.Electrical.Analog.Sources.SignalVoltage src "Measured coil voltage" annotation(
      Placement(transformation(origin = {-180, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
    Modelica.Electrical.Analog.Basic.Resistor r_c(final R = R_coil, final T_ref = 293.15)
      "Ohmic resistance of the coil" annotation(
      Placement(transformation(origin = {-180, -60}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
    Modelica.Electrical.Analog.Sensors.CurrentSensor iSense "Coil current" annotation(
      Placement(transformation(extent = {{-150, -110}, {-130, -90}})));
    Modelica.Electrical.Analog.Basic.Ground gndE annotation(
      Placement(transformation(extent = {{-150, -30}, {-130, -10}})));

    // ---------------------------------------------------------- magnetic ---
    Modelica.Magnetic.FluxTubes.Basic.ElectroMagneticConverter coil(final N = N, i(start = 0))
      "Lumped magneto-motive force of the 131-turn coil" annotation(
      Placement(transformation(extent = {{-90, 50}, {-70, 70}})));
    Modelica.Magnetic.FluxTubes.Shapes.FixedShape.HollowCylinderAxialFlux g_mFeCore(
      final nonLinearPermeability = true, final material = material,
      final l = l_axial, final r_i = 0, final r_o = r_pole) "Central pole of the yoke" annotation(
      Placement(transformation(extent = {{-30, 60}, {-10, 80}})));
    Modelica.Magnetic.FluxTubes.Shapes.Force.HollowCylinderAxialFlux g_mGapCore(
      final mu_r = 1, final dlBydx = 1, final useSupport = false,
      final r_i = 0, final r_o = r_pole, final l = x_res + x)
      "Working air gap at the central pole face" annotation(
      Placement(transformation(extent = {{50, 100}, {70, 120}})));
    Modelica.Magnetic.FluxTubes.Shapes.Force.LeakageAroundPoles g_mLeakCore(
      final mu_r = 1, final dlBydx = 1, final useSupport = false,
      final w = 2*pi*r_pole, final r = r_leak, final l = x_res + x)
      "Fringing flux around the central pole face" annotation(
      Placement(transformation(extent = {{50, 150}, {70, 170}})));
    Modelica.Magnetic.FluxTubes.Shapes.FixedShape.HollowCylinderRadialFlux g_mFeArm(
      final nonLinearPermeability = true, final material = material,
      final l = t_arm, final r_i = r_pole, final r_o = r_ringMean, final alpha = 2*pi)
      "Armature disc, radial flux from the central to the annular pole" annotation(
      Placement(transformation(extent = {{120, 100}, {140, 120}})));
    Modelica.Magnetic.FluxTubes.Shapes.Force.HollowCylinderAxialFlux g_mGapRing(
      final mu_r = 1, final dlBydx = 1, final useSupport = false,
      final r_i = r_wallIn, final r_o = r_yokeOut, final l = x_res + x)
      "Working air gap at the annular pole face" annotation(
      Placement(transformation(extent = {{190, 100}, {210, 120}})));
    Modelica.Magnetic.FluxTubes.Shapes.Force.LeakageAroundPoles g_mLeakRing(
      final mu_r = 1, final dlBydx = 1, final useSupport = false,
      final w = 2*pi*(r_wallIn + r_yokeOut), final r = r_leak, final l = x_res + x)
      "Fringing flux around the annular pole face" annotation(
      Placement(transformation(extent = {{190, 150}, {210, 170}})));
    Modelica.Magnetic.FluxTubes.Basic.ConstantPermeance g_mLeakWindow(final G_m = G_mLeakWnd)
      "Leakage across the coil window; bypasses armature and working gaps" annotation(
      Placement(transformation(extent = {{110, 20}, {130, 40}})));
    Modelica.Magnetic.FluxTubes.Shapes.FixedShape.HollowCylinderAxialFlux g_mFeWall(
      final nonLinearPermeability = true, final material = material,
      final l = l_axial, final r_i = r_wallIn, final r_o = r_yokeOut) "Outer wall of the yoke"
      annotation(Placement(transformation(origin = {240, 70}, extent = {{-10, -10}, {10, 10}},
      rotation = 270)));
    Modelica.Magnetic.FluxTubes.Shapes.FixedShape.HollowCylinderRadialFlux g_mFeBot(
      final nonLinearPermeability = true, final material = material,
      final l = t_yokeBot, final r_i = r_pole, final r_o = r_wallIn, final alpha = 2*pi)
      "Bottom of the yoke, radial flux" annotation(
      Placement(transformation(extent = {{110, -70}, {130, -50}})));
    Modelica.Magnetic.FluxTubes.Basic.EddyCurrent eddy(
      final useConductance = false, final rho = rho_fe, final l = l_eddy, final A = A_eddy,
      Phi(start = 0, fixed = true))
      "One-turn short circuit formed by the solid iron; delays the flux build-up" annotation(
      Placement(transformation(extent = {{30, -70}, {50, -50}})));
    Modelica.Magnetic.FluxTubes.Basic.Ground gndM annotation(
      Placement(transformation(extent = {{-80, -120}, {-60, -100}})));

    // --------------------------------------------------------- mechanics ---
    Modelica.Mechanics.Translational.Components.Mass armature(
      final m = m_arm, final L = 0, s(start = x_start, fixed = true), v(start = 0, fixed = true))
      "Armature with needle and reflector; its position is the working air gap" annotation(
      Placement(transformation(extent = {{120, 200}, {140, 220}})));
    Modelica.Mechanics.Translational.Components.Spring spring(
      final c = c_spring, final s_rel0 = s_spring0) "Pre-loaded return spring" annotation(
      Placement(transformation(extent = {{-10, 230}, {10, 250}})));
    Modelica.Mechanics.Translational.Components.Damper damper(final d = d_arm)
      "Viscous damping of the moving assembly" annotation(
      Placement(transformation(extent = {{-10, 260}, {10, 280}})));
    Modelica.Mechanics.Translational.Components.ElastoGap stopClosed(
      final c = c_stopClosed, final d = d_stopClosed, final s_rel0 = 0, final n = 1)
      "Mechanical end stop in the closed position (x = 0)" annotation(
      Placement(transformation(extent = {{-10, 200}, {10, 220}})));
    Modelica.Mechanics.Translational.Components.ElastoGap stopOpen(
      final c = c_stopOpen, final d = d_stopOpen, final s_rel0 = -x_max, final n = 1)
      "Mechanical end stop in the open position (x = x_max)" annotation(
      Placement(transformation(extent = {{240, 200}, {260, 220}})));
    Modelica.Mechanics.Translational.Components.Fixed fixedYoke(final s0 = 0)
      "Yoke; reference for x = 0" annotation(
      Placement(transformation(extent = {{-70, 200}, {-50, 220}})));
    Modelica.Mechanics.Translational.Components.Fixed fixedStop(final s0 = 0)
      "Housing of the open end stop" annotation(
      Placement(transformation(extent = {{280, 200}, {300, 220}})));
    Modelica.Mechanics.Translational.Sensors.PositionSensor posSense annotation(
      Placement(transformation(extent = {{160, 240}, {180, 260}})));
    Modelica.Mechanics.Translational.Sensors.SpeedSensor vSense annotation(
      Placement(transformation(extent = {{160, 270}, {180, 290}})));
  equation
    // ---- electrical -----------------------------------------------------
    connect(u, src.v) annotation(Line(points = {{-220, 0}, {-192, 0}}, color = {0, 0, 127}));
    connect(src.p, r_c.n) annotation(Line(points = {{-180, -10}, {-180, -50}}, color = {0, 0, 255}));
    connect(r_c.p, iSense.p) annotation(Line(points = {{-180, -70}, {-180, -100}, {-150, -100}}, color = {0, 0, 255}));
    connect(iSense.n, coil.p) annotation(Line(points = {{-130, -100}, {-110, -100}, {-110, 70}, {-90, 70}}, color = {0, 0, 255}));
    connect(coil.n, src.n) annotation(Line(points = {{-90, 50}, {-140, 50}, {-140, 10}, {-180, 10}}, color = {0, 0, 255}));
    connect(gndE.p, src.n) annotation(Line(points = {{-140, -10}, {-140, 10}}, color = {0, 0, 255}));
    connect(iSense.i, y_i) annotation(Line(points = {{-140, -111}, {-140, -140}, {340, -140}}, color = {0, 0, 127}));
    // ---- magnetic: central pole and working gaps ------------------------
    connect(coil.port_p, g_mFeCore.port_p) annotation(Line(points = {{-70, 70}, {-30, 70}}, color = {255, 127, 0}));
    connect(g_mFeCore.port_n, g_mGapCore.port_p) annotation(Line(points = {{-10, 70}, {30, 70}, {30, 110}, {50, 110}}, color = {255, 127, 0}));
    connect(g_mGapCore.port_p, g_mLeakCore.port_p) annotation(Line(points = {{50, 110}, {30, 110}, {30, 160}, {50, 160}}, color = {255, 127, 0}));
    connect(g_mGapCore.port_n, g_mLeakCore.port_n) annotation(Line(points = {{70, 110}, {90, 110}, {90, 160}, {70, 160}}, color = {255, 127, 0}));
    connect(g_mGapCore.port_n, g_mFeArm.port_p) annotation(Line(points = {{70, 110}, {120, 110}}, color = {255, 127, 0}));
    connect(g_mFeArm.port_n, g_mGapRing.port_p) annotation(Line(points = {{140, 110}, {190, 110}}, color = {255, 127, 0}));
    connect(g_mGapRing.port_p, g_mLeakRing.port_p) annotation(Line(points = {{190, 110}, {170, 110}, {170, 160}, {190, 160}}, color = {255, 127, 0}));
    connect(g_mGapRing.port_n, g_mLeakRing.port_n) annotation(Line(points = {{210, 110}, {220, 110}, {220, 160}, {210, 160}}, color = {255, 127, 0}));
    // ---- magnetic: leakage across the coil window -----------------------
    connect(g_mLeakWindow.port_p, g_mFeCore.port_n) annotation(Line(points = {{110, 30}, {30, 30}, {30, 70}, {-10, 70}}, color = {255, 127, 0}));
    connect(g_mLeakWindow.port_n, g_mGapRing.port_n) annotation(Line(points = {{130, 30}, {230, 30}, {230, 110}, {210, 110}}, color = {255, 127, 0}));
    // ---- magnetic: yoke wall, yoke bottom, eddy currents ----------------
    connect(g_mGapRing.port_n, g_mFeWall.port_p) annotation(Line(points = {{210, 110}, {240, 110}, {240, 80}}, color = {255, 127, 0}));
    connect(g_mFeWall.port_n, g_mFeBot.port_n) annotation(Line(points = {{240, 60}, {240, -60}, {130, -60}}, color = {255, 127, 0}));
    connect(g_mFeBot.port_p, eddy.port_n) annotation(Line(points = {{110, -60}, {50, -60}}, color = {255, 127, 0}));
    connect(eddy.port_p, coil.port_n) annotation(Line(points = {{30, -60}, {-70, -60}, {-70, 50}}, color = {255, 127, 0}));
    connect(gndM.port, eddy.port_p) annotation(Line(points = {{-70, -100}, {-70, -60}}, color = {255, 127, 0}));
    // ---- mechanics ------------------------------------------------------
    connect(g_mGapCore.flange, g_mLeakCore.flange) annotation(Line(points = {{60, 120}, {10, 120}, {10, 190}, {60, 190}, {60, 170}}, color = {0, 127, 0}));
    connect(g_mLeakCore.flange, armature.flange_a) annotation(Line(points = {{60, 170}, {60, 190}, {120, 190}, {120, 210}}, color = {0, 127, 0}));
    connect(g_mGapRing.flange, g_mLeakRing.flange) annotation(Line(points = {{200, 120}, {260, 120}, {260, 190}, {200, 190}, {200, 170}}, color = {0, 127, 0}));
    connect(g_mLeakRing.flange, armature.flange_b) annotation(Line(points = {{200, 170}, {200, 190}, {140, 190}, {140, 210}}, color = {0, 127, 0}));
    connect(fixedYoke.flange, stopClosed.flange_a) annotation(Line(points = {{-60, 210}, {-10, 210}}, color = {0, 127, 0}));
    connect(fixedYoke.flange, spring.flange_a) annotation(Line(points = {{-60, 210}, {-60, 240}, {-10, 240}}, color = {0, 127, 0}));
    connect(fixedYoke.flange, damper.flange_a) annotation(Line(points = {{-60, 210}, {-60, 270}, {-10, 270}}, color = {0, 127, 0}));
    connect(stopClosed.flange_b, armature.flange_a) annotation(Line(points = {{10, 210}, {120, 210}}, color = {0, 127, 0}));
    connect(spring.flange_b, armature.flange_a) annotation(Line(points = {{10, 240}, {100, 240}, {100, 210}, {120, 210}}, color = {0, 127, 0}));
    connect(damper.flange_b, armature.flange_a) annotation(Line(points = {{10, 270}, {80, 270}, {80, 210}, {120, 210}}, color = {0, 127, 0}));
    connect(armature.flange_b, stopOpen.flange_a) annotation(Line(points = {{140, 210}, {240, 210}}, color = {0, 127, 0}));
    connect(stopOpen.flange_b, fixedStop.flange) annotation(Line(points = {{260, 210}, {290, 210}}, color = {0, 127, 0}));
    connect(armature.flange_b, posSense.flange) annotation(Line(points = {{140, 210}, {150, 210}, {150, 250}, {160, 250}}, color = {0, 127, 0}));
    connect(armature.flange_b, vSense.flange) annotation(Line(points = {{140, 210}, {150, 210}, {150, 280}, {160, 280}}, color = {0, 127, 0}));
    connect(posSense.s, y_x) annotation(Line(points = {{181, 250}, {340, 250}}, color = {0, 0, 127}));
    connect(vSense.v, y_v) annotation(Line(points = {{181, 280}, {280, 280}, {280, 290}, {340, 290}}, color = {0, 0, 127}));
    annotation(
      Diagram(coordinateSystem(preserveAspectRatio = false, extent = {{-240, -170}, {360, 320}}, grid = {2, 2})),
      Icon(coordinateSystem(preserveAspectRatio = false, extent = {{-100, -100}, {100, 100}}), graphics = {
        Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {0, 0, 255}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{-80, -70}, {80, -50}}, lineColor = {255, 128, 0}, fillColor = {255, 128, 0}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{-80, -50}, {-50, 40}}, lineColor = {255, 128, 0}, fillColor = {255, 128, 0}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{50, -50}, {80, 40}}, lineColor = {255, 128, 0}, fillColor = {255, 128, 0}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{-16, -50}, {16, 40}}, lineColor = {255, 128, 0}, fillColor = {255, 128, 0}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{-80, 56}, {80, 76}}, lineColor = {95, 95, 95}, fillColor = {160, 160, 164}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{-48, -40}, {-18, 30}}, lineColor = {255, 213, 170}, fillColor = {255, 213, 170}, fillPattern = FillPattern.Solid),
        Rectangle(extent = {{18, -40}, {48, 30}}, lineColor = {255, 213, 170}, fillColor = {255, 213, 170}, fillPattern = FillPattern.Solid),
        Line(points = {{-80, 46}, {80, 46}}, color = {0, 0, 0}, pattern = LinePattern.Dash),
        Text(extent = {{-150, 150}, {150, 110}}, textColor = {0, 0, 255}, textString = "%name"),
        Text(extent = {{-60, 100}, {60, 84}}, textColor = {0, 0, 0}, textString = "x")}),
      Documentation(info = "<html>
<p>Lumped magnetic-network model of a switching electromagnet of the flat-armature
(pot-magnet) type: a cylindrical yoke of 25&nbsp;mm diameter and 12.5&nbsp;mm height
carrying a 131-turn coil in an annular window, closed by a flat armature disc and
opened by a pre-loaded return spring.</p>
<p><strong>Magnetic circuit.</strong> One loop
<em>central pole &rarr; working gap &rarr; armature disc &rarr; working gap &rarr;
yoke wall &rarr; yoke bottom</em>. Each of the two working gaps carries a
<code>LeakageAroundPoles</code> element in parallel that represents the fringing flux
around the pole edge and contributes to the force; a constant permeance across the
coil window shunts the armature branch and carries no force. One
<code>EddyCurrent</code> element in the loop represents the one-turn short circuit
formed by the solid (non-laminated) steel and reproduces the measured delayed flux
build-up.
A residual non-magnetic gap <code>x_res</code> remains at each pole face when the
armature sits on the closed stop.</p>
<p><strong>Mechanics.</strong> Armature mass with a pre-loaded return spring, viscous
damping and two unilateral end stops, <code>x&nbsp;=&nbsp;0</code> (closed) and
<code>x&nbsp;=&nbsp;x_max</code> (open).</p>
<p><code>u</code> is the voltage across the coil, <code>y_i</code> the coil current,
<code>y_x</code> the working air gap and <code>y_v</code> its time derivative
(negative while the magnet closes).</p>
</html>"));
  end FlatArmatureMagnet;

  model TestRig
    "Plays a measured coil-voltage trace into FlatArmatureMagnet (used for calibration and validation)"
    parameter String fileName = "u.txt" "File with the measured coil voltage (time, u)";
    parameter String tableName = "u" "Name of the table on the file";
    Modelica.Blocks.Sources.CombiTimeTable uSource(
      final tableOnFile = true, final fileName = fileName, final tableName = tableName,
      final columns = {2}, final smoothness = Modelica.Blocks.Types.Smoothness.LinearSegments,
      final extrapolation = Modelica.Blocks.Types.Extrapolation.HoldLastPoint)
      "Measured coil voltage, replayed from file" annotation(
      Placement(transformation(extent = {{-80, -10}, {-60, 10}})));
    SwitchingMagnet.FlatArmatureMagnet magnet annotation(
      Placement(transformation(extent = {{-20, -20}, {20, 20}})));
    Modelica.Blocks.Interfaces.RealOutput y_i = magnet.y_i "Coil current" annotation(
      Placement(transformation(extent = {{60, 30}, {80, 50}})));
    Modelica.Blocks.Interfaces.RealOutput y_x = magnet.y_x "Working air gap" annotation(
      Placement(transformation(extent = {{60, -10}, {80, 10}})));
    Modelica.Blocks.Interfaces.RealOutput y_v = magnet.y_v "Armature velocity" annotation(
      Placement(transformation(extent = {{60, -50}, {80, -30}})));
  equation
    connect(uSource.y[1], magnet.u) annotation(Line(points = {{-59, 0}, {-20, 0}}, color = {0, 0, 127}));
    annotation(
      experiment(StopTime = 0.05, Tolerance = 1e-8, Interval = 2e-05),
      Diagram(coordinateSystem(preserveAspectRatio = false, extent = {{-100, -100}, {100, 100}})),
      Icon(coordinateSystem(preserveAspectRatio = false), graphics = {
        Rectangle(extent = {{-100, -100}, {100, 100}}, lineColor = {0, 0, 255}, fillColor = {255, 255, 255}, fillPattern = FillPattern.Solid),
        Text(extent = {{-150, 150}, {150, 110}}, textColor = {0, 0, 255}, textString = "%name")}));
  end TestRig;
  annotation(
    version = "1.0",
    uses(Modelica(version = "4.1.0")),
    Documentation(info = "<html>
<p>Deliverable of task 5. <code>FlatArmatureMagnet</code> is the calibrated model,
<code>TestRig</code> replays a measured coil-voltage trace into it.</p></html>"));
end SwitchingMagnet;

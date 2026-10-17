model BatteryPack
  "Battery pack: Thevenin model with state-of-charge dependent OCV

  The open-circuit voltage declines with the net charge delivered by the
  pack (state of charge). The pack internal resistance is modeled in
  series. The pack is assumed to be in its initial (serviced) state at
  the start of every run, i.e. Q = 0 at t = 0.
   "
   parameter Real V0(min=0, start=134.28)
    "Open-circuit voltage at start of run [V]"
    annotation (Dialog(group="Battery"));
  parameter Real dVdQ(min=0, start=1.0824e-4)
    "Open-circuit voltage drop per unit delivered charge [V/C]"
    annotation (Dialog(group="Battery"));
  parameter Real R_int(min=0, start=0.1)
    "Internal resistance [Ohm]"
    annotation (Dialog(group="Battery"));

  Modelica.Electrical.Analog.Interfaces.Pin p
    "Positive terminal"
    annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));
  Modelica.Electrical.Analog.Interfaces.Pin n
    "Negative terminal"
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));

  Modelica.Electrical.Analog.Basic.Resistor rInt(R=R_int)
    annotation (Placement(transformation(origin={-45, 0},
        extent={{-10,-10},{10,10}})));
  Modelica.Electrical.Analog.Sources.SignalVoltage ocv
    "Open-circuit voltage source"
    annotation (Placement(transformation(origin={45, 0},
        extent={{-10,-10},{10,10}})));

  Real Q(start=0, fixed=true) "Net charge delivered by the pack [C]"
    annotation (Dialog(group="Battery"));
equation
  connect(p, rInt.p)
    annotation (Line(points={{-100,0},{-55,0}}, color={0,0,255}));
  connect(rInt.n, ocv.p)
    annotation (Line(points={{-35,0},{35,0}}, color={0,0,255}));
  connect(ocv.n, n)
    annotation (Line(points={{55,0},{100,0}}, color={0,0,255}));
  ocv.v = V0 - dVdQ*Q;
  der(Q) = -p.i;
  annotation (
    Icon(coordinateSystem(extent={{-100,-100},{100,100}},
        preserveAspectRatio=true),
      graphics={
        Rectangle(extent={{-55,-30},{55,30}}, lineColor={0,0,0},
            fillColor={255,255,255}, fillPattern=FillPattern.Solid),
        Line(points={{-100,0},{-55,0}}, color={0,0,255}),
        Line(points={{55,0},{100,0}}, color={0,0,255}),
        Line(points={{-40,8},{-16,8}}, color={160,160,164}),
        Line(points={{-28,-4},{-28,20}}, color={160,160,164}),
        Line(points={{12,-4},{36,-4}}, color={160,160,164})}),
    Diagram(coordinateSystem(extent={{-100,-100},{100,100}},
        preserveAspectRatio=true)),
    Documentation(info="<html>
<p>Battery pack as a Thevenin model: open-circuit voltage source with a
voltage that declines linearly with the net charge delivered (state of
charge), in series with the internal resistance.</p>
<p>The pack starts every run in its initial (serviced) state, Q = 0.</p>
</html>"));
end BatteryPack;


model DCMachine
  "DC machine with armature resistance and inductance

  Lumped electrical-mechanical model of the DC machine. The armature
  circuit consists of the resistance R and the inductance L. The
  back-emf is proportional to the rotor speed with the constant ke and
  the electromagnetic torque is proportional to the armature current
  with the constant kt.
  "
  parameter Real R(min=0, start=0.168464) "Armature resistance [Ohm]"
    annotation (Dialog(group="Armature"));
   parameter Real L(min=Modelica.Constants.eps, start=0.0224326)
    "Armature inductance [H]"
    annotation (Dialog(group="Armature"));
   parameter Real ke(start=0.614163)
    "Back-emf constant [V.s/rad]"
    annotation (Dialog(group="Machine"));
   parameter Real kt(start=1.15782)
    "Torque constant [N.m/A]"
    annotation (Dialog(group="Machine"));
   parameter Real J(min=0, start=0.191812)
    "Total moment of inertia referred to the motor shaft [kg.m2]"
    annotation (Dialog(group="Machine"));

  Modelica.Electrical.Analog.Interfaces.Pin p
    "Positive armature terminal"
    annotation (Placement(transformation(extent={{-100,10},{-80,30}})));
  Modelica.Electrical.Analog.Interfaces.Pin n
    "Negative armature terminal"
    annotation (Placement(transformation(extent={{-100,-30},{-80,-10}})));
  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange
    "Motor shaft"
    annotation (Placement(transformation(extent={{80,-10},{100,10}})));

  Modelica.Electrical.Analog.Sensors.CurrentSensor iSens
    annotation (Placement(transformation(origin={-60, 20},
        extent={{-10,-10},{10,10}})));
  Modelica.Electrical.Analog.Basic.Resistor rArm(R=R)
    annotation (Placement(transformation(origin={-35, 20},
        extent={{-10,-10},{10,10}})));
  Modelica.Electrical.Analog.Basic.Inductor lArm(L=L, i(start=0))
    annotation (Placement(transformation(origin={-10, 20},
        extent={{-10,-10},{10,10}})));
  Modelica.Electrical.Analog.Sources.SignalVoltage emf
    "Back-emf, v = ke * w"
    annotation (Placement(transformation(origin={15, 20},
        extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Components.Inertia rotor(
      J=J, phi(fixed=true, start=0), w(fixed=true, start=0))
    annotation (Placement(transformation(origin={90, -40},
        extent={{-10,-10},{10,10}}, rotation=270)));
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor wSens
    annotation (Placement(transformation(origin={40, -30},
        extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Sources.Torque motorTorque
    "Electromagnetic torque, tau = kt * i"
    annotation (Placement(transformation(origin={60, -60},
        extent={{-10,-10},{10,10}})));
  Modelica.Blocks.Math.Gain keGain(k=ke)
    annotation (Placement(transformation(origin={-70, 50},
        extent={{-10,-10},{10,10}})));
  Modelica.Blocks.Math.Gain ktGain(k=kt)
    annotation (Placement(transformation(origin={-30, -50},
        extent={{-10,-10},{10,10}})));
equation
  connect(p, iSens.p)
    annotation (Line(points={{-90,20},{-70,20}}, color={0,0,255}));
  connect(iSens.n, rArm.p)
    annotation (Line(points={{-50,20},{-45,20}}, color={0,0,255}));
  connect(rArm.n, lArm.p)
    annotation (Line(points={{-25,20},{-20,20}}, color={0,0,255}));
  connect(lArm.n, emf.p)
    annotation (Line(points={{0,20},{5,20}}, color={0,0,255}));
  connect(emf.n, n)
    annotation (Line(points={{25,20},{25,-20},{-90,-20}}, color={0,0,255}));
  connect(flange, rotor.flange_a)
    annotation (Line(points={{90,0},{90,-30}}));
  connect(rotor.flange_a, wSens.flange)
    annotation (Line(points={{90,-30},{30,-30}}));
  connect(rotor.flange_a, motorTorque.flange)
    annotation (Line(points={{90,-30},{90,-60},{70,-60}}));
  connect(wSens.w, keGain.u)
    annotation (Line(points={{51,-30},{51,50},{-80,50}}, color={0,0,127}));
  connect(keGain.y, emf.v)
    annotation (Line(points={{-60,50},{15,50},{15,32}}, color={0,0,127}));
  connect(iSens.i, ktGain.u)
    annotation (Line(points={{-60,9},{-60,-50},{-40,-50}}, color={0,0,127}));
  connect(ktGain.y, motorTorque.tau)
    annotation (Line(points={{-20,-50},{-20,-60},{48,-60}}, color={0,0,127}));
  annotation (
    Icon(coordinateSystem(extent={{-100,-100},{100,100}},
        preserveAspectRatio=true),
      graphics={
        Ellipse(extent={{-60,60},{60,-60}}, lineColor={0,0,255},
            fillColor={255,255,255}, fillPattern=FillPattern.Solid),
        Text(extent={{-30,30},{30,-30}}, textString="M",
            textColor={0,0,255}),
        Line(points={{-100,20},{-85,20}}, color={0,0,255}),
        Line(points={{-100,-20},{-85,-20}}, color={0,0,255}),
        Polygon(points={{85,-12},{100,0},{85,12},{85,-12}},
            lineColor={0,0,0}, fillColor={0,0,0},
            fillPattern=FillPattern.Solid)}),
    Diagram(coordinateSystem(extent={{-120,-90},{110,70}},
        preserveAspectRatio=true)),
    Documentation(info="<html>
<p>DC machine. Armature circuit: resistance R and inductance L in
series with the back-emf v = ke*w (w = rotor speed). The
electromagnetic torque is tau = kt*i (i = armature current). The total
rotor inertia referred to the motor shaft is J.</p>
</html>"));
end DCMachine;


model DriveTrainRig
  "Battery powered drive train test rig

  Battery pack feeds a DC machine; the machine drives the output shaft
  through a fixed reduction stage (ratio 5.2, motor side to output
  side). The load is a brake applying the commanded torque u at the
  output shaft. The rig starts from standstill with the circuit closed.

   Measured: battery current y_i [A] and output shaft speed y_w [rad/s].
   "
   Modelica.Blocks.Interfaces.RealInput u(unit="N.m")
    "Commanded brake torque at the output shaft"
    annotation (Placement(transformation(extent={{155,-110},{175,-90}})));
  Modelica.Blocks.Interfaces.RealOutput y_i(unit="A")
    "Battery current"
    annotation (Placement(transformation(extent={{-55,70},{-35,90}})));
  Modelica.Blocks.Interfaces.RealOutput y_w(unit="rad/s")
    "Output shaft speed"
    annotation (Placement(transformation(extent={{170,70},{190,90}})));

  parameter Real V0(min=0) = 133.731
    "Battery open-circuit voltage at start of run [V]"
    annotation (Dialog(group="Battery"));
  parameter Real dVdQ(min=0) = 0.000107941
    "Battery OCV drop per unit delivered charge [V/C]"
    annotation (Dialog(group="Battery"));
  parameter Real R_int(min=0) = 0.10
    "Battery internal resistance [Ohm] (only R_int + R identifiable)"
    annotation (Dialog(group="Battery"));
  parameter Real R(min=0) = 0.168464
    "Machine armature resistance [Ohm] (only R_int + R identifiable)"
    annotation (Dialog(group="Machine"));
  parameter Real L(min=Modelica.Constants.eps) = 0.0224326
    "Machine armature inductance [H]"
    annotation (Dialog(group="Machine"));
  parameter Real ke = 0.614163
    "Machine back-emf constant [V.s/rad]"
    annotation (Dialog(group="Machine"));
  parameter Real kt = 1.15782
    "Machine torque constant [N.m/A]"
    annotation (Dialog(group="Machine"));
  parameter Real J(min=0) = 0.191812
    "Total inertia referred to the motor shaft [kg.m2]"
    annotation (Dialog(group="Machine"));
  parameter Real ratio(fixed=true) = 5.2
    "Reduction ratio (motor side to output side) [-]"
    annotation (Dialog(group="Reduction", enable=false));
  parameter Real F0(min=0) = 3.32679
    "Coulomb friction torque at the motor shaft [N.m]"
    annotation (Dialog(group="Drivetrain"));

  BatteryPack battery(V0=V0, dVdQ=dVdQ, R_int=R_int)
    annotation (Placement(transformation(origin={-70, 30},
        extent={{-30,-15},{30,15}})));
  DCMachine machine(R=R, L=L, ke=ke, kt=kt, J=J)
    annotation (Placement(transformation(origin={20, 30},
        extent={{-40,-20},{40,20}})));
  Modelica.Electrical.Analog.Sensors.CurrentSensor battCurrent
    "Battery current sensor"
    annotation (Placement(transformation(origin={-35, 30},
        extent={{-10,-10},{10,10}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(origin={-16, 5},
        extent={{-8,-8},{8,8}})));
  Modelica.Mechanics.Rotational.Sources.SignTorque friction(
      tau_nominal=-F0,
      reg=Modelica.Blocks.Types.Regularization.Exp,
      w0=0.1)
    "Coulomb friction at the motor shaft"
    annotation (Placement(transformation(origin={80, -70},
        extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Components.IdealGear reduction(
      ratio=ratio)
    "Fixed reduction stage"
    annotation (Placement(transformation(origin={125, -30},
        extent={{-15,-15},{15,15}})));
  Modelica.Mechanics.Rotational.Sources.Torque brake
    "Brake applying the commanded torque at the output shaft"
    annotation (Placement(transformation(origin={165, -30},
        extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor wSensor
    "Output shaft speed sensor"
    annotation (Placement(transformation(origin={140, -70},
        extent={{-10,-10},{10,10}})));
  Modelica.Blocks.Math.Gain brakeSign(k=-1)
    annotation (Placement(transformation(origin={120, -100},
        extent={{-10,-10},{10,10}})));
equation
  connect(battery.p, battCurrent.p)
    annotation (Line(points={{-100,30},{-45,30}}, color={0,0,255}));
  connect(battCurrent.n, machine.p)
    annotation (Line(points={{-25,30},{-16,30},{-16,34}}, color={0,0,255}));
  connect(battery.n, ground.p)
    annotation (Line(points={{-40,30},{-40,13},{-16,13}}, color={0,0,255}));
  connect(machine.n, ground.p)
    annotation (Line(points={{-16,26},{-16,13}}, color={0,0,255}));
  connect(machine.flange, reduction.flange_a)
    annotation (Line(points={{56,30},{56,-30},{110,-30}}));
  connect(machine.flange, friction.flange)
    annotation (Line(points={{56,30},{56,-30},{56,-70},{90,-70}}));
  connect(reduction.flange_b, brake.flange)
    annotation (Line(points={{140,-30},{175,-30}}));
  connect(reduction.flange_b, wSensor.flange)
    annotation (Line(points={{140,-30},{140,-70},{130,-70}}));
  connect(u, brakeSign.u)
    annotation (Line(points={{165,-100},{130,-100}}, color={0,0,127}));
  connect(brakeSign.y, brake.tau)
    annotation (Line(points={{130,-100},{130,-30},{153,-30}},
        color={0,0,127}));
  connect(battCurrent.i, y_i)
    annotation (Line(points={{-35,19},{-35,80},{-45,80}}, color={0,0,127}));
  connect(wSensor.w, y_w)
    annotation (Line(points={{151,-70},{151,80},{180,80}},
        color={0,0,127}));
  annotation (
    Icon(coordinateSystem(extent={{-120,-120},{200,100}},
        preserveAspectRatio=true),
      graphics={
        Rectangle(extent={{-110,40},{-50,10}}, lineColor={0,0,255}),
        Text(extent={{-108,38},{-52,12}}, textString="battery",
            textColor={0,0,255}),
        Ellipse(extent={{-20,40},{20,0}}, lineColor={0,0,255}),
        Text(extent={{-10,35},{10,5}}, textString="M",
            textColor={0,0,255}),
        Line(points={{20,20},{60,20}}, color={0,0,255}),
        Line(points={{-50,25},{-20,20}}, color={0,0,255}),
        Ellipse(extent={{60,30},{100,-10}}, lineColor={0,0,255}),
        Text(extent={{68,25},{92,5}}, textString="i",
            textColor={0,0,255}),
        Ellipse(extent={{110,30},{150,-10}}, lineColor={0,0,255}),
        Text(extent={{118,25},{142,5}}, textString="r",
            textColor={0,0,255}),
        Line(points={{150,10},{180,10}}, color={0,0,255}),
        Rectangle(extent={{180,30},{210,-10}}, lineColor={0,0,255}),
        Text(extent={{182,28},{208,-8}}, textString="brake",
            textColor={0,0,255})}),
    Diagram(coordinateSystem(extent={{-120,-120},{200,100}},
        preserveAspectRatio=true)),
    Documentation(info="<html>
<p>Battery powered drive train test rig. A battery pack feeds a DC
machine; the machine drives the output shaft through a fixed reduction
stage with ratio 5.2 (motor side to output side). The load is a brake
applying the commanded torque u at the output shaft. Every run starts
from standstill with the circuit closed.</p>
<p>Inputs/outputs: u = commanded brake torque [N.m]; y_i = battery
current [A]; y_w = output shaft speed [rad/s].</p>
</html>"));
end DriveTrainRig;

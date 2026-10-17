model DriveTrainRig
  "Reference model of task 4: the device that produced the data, a test rig for a battery-powered drive train"
  // Architecture and orders of magnitude after Wallén (2004), chapter 4; the
  // composition and the values are our own. This is the device, not a
  // delivery: its battery states the state of charge in two equations, which
  // the task does not admit for a delivered model.
  parameter Modelica.Units.SI.Resistance R_i = 0.14 "internal resistance of the battery";
  parameter Modelica.Units.SI.Resistance R_a = 0.36 "armature resistance";
  parameter Modelica.Units.SI.Inductance L_a = 0.042 "armature inductance";
  parameter Modelica.Units.SI.ElectricalTorqueConstant k = 1.15 "torque constant";
  parameter Modelica.Units.SI.Inertia J_rot = 0.014 "inertia of the rotor";
  parameter Modelica.Units.SI.RotationalDampingConstant d_rot = 0.0025 "viscous friction on the motor side";
  parameter Real ratio = 5.2 "reduction ratio, motor side to output side";
  parameter Modelica.Units.SI.Inertia J_load = 4.8 "inertia of the load";
  parameter Modelica.Units.SI.RotationalDampingConstant d_load = 0.35 "viscous friction on the output side";
  parameter Modelica.Units.SI.ElectricCharge Q_max = 200000.0 "capacity of the battery (55.6 Ah)";
  parameter Real SOC0 = 0.85 "state of charge at the start of every experiment";
  Real SOC(start = SOC0, fixed = true) "state of charge, not measured";
  Modelica.Blocks.Interfaces.RealInput u "commanded brake torque at the output shaft in N.m";
  Modelica.Blocks.Interfaces.RealOutput y_i "battery current in A";
  Modelica.Blocks.Interfaces.RealOutput y_w "speed of the output shaft in rad/s";
  Modelica.Electrical.Analog.Sources.SignalVoltage battery;
  Modelica.Electrical.Analog.Basic.Resistor r_i(R = R_i);
  Modelica.Electrical.Analog.Basic.Resistor r_a(R = R_a);
  Modelica.Electrical.Analog.Basic.Inductor l_a(L = L_a, i(start = 0, fixed = true));
  Modelica.Electrical.Analog.Basic.RotationalEMF emf(k = k);
  Modelica.Electrical.Analog.Basic.Ground ground;
  Modelica.Electrical.Analog.Sensors.CurrentSensor currentSensor;
  // Open-circuit voltage over the state of charge: flat in the middle, steeper at the ends.
  Modelica.Blocks.Tables.CombiTable1Ds ocv(
    table = [0.0000, 198.0; 0.1000, 216.0; 0.2500, 226.0; 0.5000, 236.0;
             0.7500, 246.0; 0.9000, 253.0; 1.0000, 260.0],
    smoothness = Modelica.Blocks.Types.Smoothness.ContinuousDerivative);
  Modelica.Mechanics.Rotational.Components.Inertia rotor(J = J_rot,
    phi(start = 0, fixed = true), w(start = 0, fixed = true));
  Modelica.Mechanics.Rotational.Components.Damper frictionRotor(d = d_rot);
  Modelica.Mechanics.Rotational.Components.IdealGear gear(ratio = ratio);
  Modelica.Mechanics.Rotational.Components.Inertia load(J = J_load);
  Modelica.Mechanics.Rotational.Components.Damper frictionLoad(d = d_load);
  Modelica.Mechanics.Rotational.Components.Fixed housing;
  Modelica.Mechanics.Rotational.Sources.Torque brake;
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor speedSensor;
  Modelica.Blocks.Math.Gain sign(k = -1) "the brake torque opposes the rotation";
equation
  der(SOC) = -currentSensor.i / Q_max;
  ocv.u = SOC;
  battery.v = ocv.y[1];
  connect(battery.p, r_i.p);
  connect(r_i.n, r_a.p);
  connect(r_a.n, l_a.p);
  connect(l_a.n, emf.p);
  connect(emf.n, currentSensor.p);
  connect(currentSensor.n, battery.n);
  connect(ground.p, battery.n);
  connect(emf.flange, rotor.flange_a);
  connect(rotor.flange_b, frictionRotor.flange_a);
  connect(frictionRotor.flange_b, housing.flange);
  connect(rotor.flange_b, gear.flange_a);
  connect(gear.flange_b, load.flange_a);
  connect(load.flange_b, frictionLoad.flange_a);
  connect(frictionLoad.flange_b, housing.flange);
  connect(load.flange_b, brake.flange);
  connect(load.flange_b, speedSensor.flange);
  connect(u, sign.u);
  connect(sign.y, brake.tau);
  y_i = currentSensor.i;
  y_w = speedSensor.w;
  annotation(uses(Modelica(version = "4.1.0")));
end DriveTrainRig;

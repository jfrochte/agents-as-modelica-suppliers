model FlywheelDrive
  "Reference model of task 3: the device that produced the data, a permanent-magnet DC motor driving a flywheel"
  parameter Modelica.Units.SI.Resistance R = 2.0 "armature resistance";
  parameter Modelica.Units.SI.Inductance L = 1e-3 "armature inductance";
  parameter Modelica.Units.SI.ElectricalTorqueConstant k = 0.1 "torque constant";
  parameter Modelica.Units.SI.Inertia J = 2e-3 "inertia of rotor and wheel";
  parameter Modelica.Units.SI.RotationalDampingConstant d = 5e-4 "viscous bearing friction";
  Modelica.Blocks.Interfaces.RealInput u "supply voltage in V";
  Modelica.Blocks.Interfaces.RealOutput y_i "motor current in A";
  Modelica.Blocks.Interfaces.RealOutput y_w "speed of the wheel in rad/s";
  Modelica.Electrical.Analog.Sources.SignalVoltage supply;
  Modelica.Electrical.Analog.Basic.Resistor resistor(R = R);
  Modelica.Electrical.Analog.Basic.Inductor inductor(L = L, i(start = 0, fixed = true));
  Modelica.Electrical.Analog.Sensors.CurrentSensor currentSensor;
  Modelica.Electrical.Analog.Basic.RotationalEMF emf(k = k);
  Modelica.Electrical.Analog.Basic.Ground ground;
  Modelica.Mechanics.Rotational.Components.Inertia inertia(J = J,
    phi(start = 0, fixed = true), w(start = 0, fixed = true));
  Modelica.Mechanics.Rotational.Components.Damper damper(d = d);
  Modelica.Mechanics.Rotational.Components.Fixed fixed;
  Modelica.Mechanics.Rotational.Sensors.SpeedSensor speedSensor;
equation
  connect(u, supply.v);
  connect(supply.p, resistor.p);
  connect(resistor.n, inductor.p);
  connect(inductor.n, currentSensor.p);
  connect(currentSensor.n, emf.p);
  connect(emf.n, supply.n);
  connect(emf.n, ground.p);
  connect(emf.flange, inertia.flange_a);
  connect(inertia.flange_b, damper.flange_a);
  connect(damper.flange_b, fixed.flange);
  connect(inertia.flange_b, speedSensor.flange);
  connect(currentSensor.i, y_i);
  connect(speedSensor.w, y_w);
  annotation(uses(Modelica(version = "4.1.0")));
end FlywheelDrive;

model LinearBlackBox "Linear black box: output-error state-space model of order 2, identified from the two fitting experiments"
  Modelica.Blocks.Interfaces.RealInput u;
  Modelica.Blocks.Interfaces.RealOutput y_s;
  Modelica.Blocks.Interfaces.RealOutput y_v;
  Modelica.Blocks.Continuous.StateSpace ss(A=[0, 1; -3.9977193111190505, -0.40042864136446388], B=[0; 1], C=[0.49983305265243344, 0.00031607602050722687; -0.0029632234311281697, 0.50050851802531793], D=[0; 0],
    initType=Modelica.Blocks.Types.Init.InitialState, x_start=zeros(2));
equation
  connect(u, ss.u[1]);
  connect(ss.y[1], y_s);
  connect(ss.y[2], y_v);
end LinearBlackBox;

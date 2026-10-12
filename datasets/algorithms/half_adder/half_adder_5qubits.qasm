OPENQASM 2.0;
include "qelib1.inc";
gate gate_HalfAdder q0,q1,q2,q3,q4 { cx q1,q3; cx q1,q4; ccx q0,q2,q1; ccx q1,q3,q4; cx q1,q3; x q3; ccx q0,q2,q1; x q3; cx q0,q2; cx q1,q3; }
qreg q[5];
creg meas[5];
gate_HalfAdder q[0],q[1],q[2],q[3],q[4];
barrier q[0],q[1],q[2],q[3],q[4];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];
measure q[4] -> meas[4];

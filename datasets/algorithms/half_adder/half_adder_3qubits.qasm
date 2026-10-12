OPENQASM 2.0;
include "qelib1.inc";
gate gate_HalfAdder q0,q1,q2 { ccx q0,q1,q2; cx q0,q1; }
qreg q[3];
creg meas[3];
gate_HalfAdder q[0],q[1],q[2];
barrier q[0],q[1],q[2];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];

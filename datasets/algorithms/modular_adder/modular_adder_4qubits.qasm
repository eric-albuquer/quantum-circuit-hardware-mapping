OPENQASM 2.0;
include "qelib1.inc";
gate mcmt q0,q1,q2,q3 { cx q0,q1; cx q0,q2; cx q0,q3; }
gate gate_ModularAdder q0,q1,q2,q3 { mcmt q1,q0,q2,q3; cx q1,q2; cx q0,q1; rccx q2,q1,q0; cx q0,q1; cx q1,q3; cx q0,q1; rccx q2,q1,q0; cx q0,q1; cx q0,q2; mcmt q1,q0,q2,q3; }
qreg q[4];
creg meas[4];
gate_ModularAdder q[0],q[1],q[2],q[3];
barrier q[0],q[1],q[2],q[3];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];

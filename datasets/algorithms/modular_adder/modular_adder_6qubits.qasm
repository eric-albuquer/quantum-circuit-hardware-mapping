OPENQASM 2.0;
include "qelib1.inc";
gate mcmt q0,q1,q2,q3,q4,q5 { cx q0,q1; cx q0,q2; cx q0,q3; cx q0,q4; cx q0,q5; }
gate gate_ModularAdder q0,q1,q2,q3,q4,q5 { mcmt q2,q0,q1,q3,q4,q5; cx q2,q3; cx q0,q2; rccx q3,q2,q0; cx q0,q2; cx q2,q4; cx q1,q2; rccx q4,q2,q1; cx q1,q2; cx q2,q5; cx q1,q2; rccx q4,q2,q1; cx q1,q2; cx q1,q4; cx q0,q2; rccx q3,q2,q0; cx q0,q2; cx q0,q3; mcmt q2,q0,q1,q3,q4,q5; }
qreg q[6];
creg meas[6];
gate_ModularAdder q[0],q[1],q[2],q[3],q[4],q[5];
barrier q[0],q[1],q[2],q[3],q[4],q[5];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];
measure q[4] -> meas[4];
measure q[5] -> meas[5];

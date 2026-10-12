OPENQASM 2.0;
include "qelib1.inc";
gate mcmt q0,q1,q2,q3,q4,q5,q6,q7,q8,q9 { cx q0,q1; cx q0,q2; cx q0,q3; cx q0,q4; cx q0,q5; cx q0,q6; cx q0,q7; cx q0,q8; cx q0,q9; }
gate gate_ModularAdder q0,q1,q2,q3,q4,q5,q6,q7,q8,q9 { mcmt q4,q0,q1,q2,q3,q5,q6,q7,q8,q9; cx q4,q5; cx q0,q4; rccx q5,q4,q0; cx q0,q4; cx q4,q6; cx q1,q4; rccx q6,q4,q1; cx q1,q4; cx q4,q7; cx q2,q4; rccx q7,q4,q2; cx q2,q4; cx q4,q8; cx q3,q4; rccx q8,q4,q3; cx q3,q4; cx q4,q9; cx q3,q4; rccx q8,q4,q3; cx q3,q4; cx q3,q8; cx q2,q4; rccx q7,q4,q2; cx q2,q4; cx q2,q7; cx q1,q4; rccx q6,q4,q1; cx q1,q4; cx q1,q6; cx q0,q4; rccx q5,q4,q0; cx q0,q4; cx q0,q5; mcmt q4,q0,q1,q2,q3,q5,q6,q7,q8,q9; }
qreg q[10];
creg meas[10];
gate_ModularAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];
measure q[4] -> meas[4];
measure q[5] -> meas[5];
measure q[6] -> meas[6];
measure q[7] -> meas[7];
measure q[8] -> meas[8];
measure q[9] -> meas[9];

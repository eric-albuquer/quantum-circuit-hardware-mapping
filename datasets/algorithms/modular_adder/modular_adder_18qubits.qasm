OPENQASM 2.0;
include "qelib1.inc";
gate mcmt q0,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17 { cx q0,q1; cx q0,q2; cx q0,q3; cx q0,q4; cx q0,q5; cx q0,q6; cx q0,q7; cx q0,q8; cx q0,q9; cx q0,q10; cx q0,q11; cx q0,q12; cx q0,q13; cx q0,q14; cx q0,q15; cx q0,q16; cx q0,q17; }
gate gate_ModularAdder q0,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17 { mcmt q8,q0,q1,q2,q3,q4,q5,q6,q7,q9,q10,q11,q12,q13,q14,q15,q16,q17; cx q8,q9; cx q0,q8; rccx q9,q8,q0; cx q0,q8; cx q8,q10; cx q1,q8; rccx q10,q8,q1; cx q1,q8; cx q8,q11; cx q2,q8; rccx q11,q8,q2; cx q2,q8; cx q8,q12; cx q3,q8; rccx q12,q8,q3; cx q3,q8; cx q8,q13; cx q4,q8; rccx q13,q8,q4; cx q4,q8; cx q8,q14; cx q5,q8; rccx q14,q8,q5; cx q5,q8; cx q8,q15; cx q6,q8; rccx q15,q8,q6; cx q6,q8; cx q8,q16; cx q7,q8; rccx q16,q8,q7; cx q7,q8; cx q8,q17; cx q7,q8; rccx q16,q8,q7; cx q7,q8; cx q7,q16; cx q6,q8; rccx q15,q8,q6; cx q6,q8; cx q6,q15; cx q5,q8; rccx q14,q8,q5; cx q5,q8; cx q5,q14; cx q4,q8; rccx q13,q8,q4; cx q4,q8; cx q4,q13; cx q3,q8; rccx q12,q8,q3; cx q3,q8; cx q3,q12; cx q2,q8; rccx q11,q8,q2; cx q2,q8; cx q2,q11; cx q1,q8; rccx q10,q8,q1; cx q1,q8; cx q1,q10; cx q0,q8; rccx q9,q8,q0; cx q0,q8; cx q0,q9; mcmt q8,q0,q1,q2,q3,q4,q5,q6,q7,q9,q10,q11,q12,q13,q14,q15,q16,q17; }
qreg q[18];
creg meas[18];
gate_ModularAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16],q[17];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16],q[17];
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
measure q[10] -> meas[10];
measure q[11] -> meas[11];
measure q[12] -> meas[12];
measure q[13] -> meas[13];
measure q[14] -> meas[14];
measure q[15] -> meas[15];
measure q[16] -> meas[16];
measure q[17] -> meas[17];

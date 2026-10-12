OPENQASM 2.0;
include "qelib1.inc";
gate mcx q0,q1,q2,q3 { h q3; p(pi/8) q0; p(pi/8) q1; p(pi/8) q2; p(pi/8) q3; cx q0,q1; p(-pi/8) q1; cx q0,q1; cx q1,q2; p(-pi/8) q2; cx q0,q2; p(pi/8) q2; cx q1,q2; p(-pi/8) q2; cx q0,q2; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; h q3; }
gate gate_HalfAdder q0,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16 { cx q1,q9; cx q2,q10; cx q3,q11; cx q4,q12; cx q5,q13; cx q6,q14; cx q7,q15; cx q7,q16; cx q2,q3; cx q4,q5; cx q6,q7; cx q4,q6; cx q2,q4; cx q1,q2; cx q3,q4; cx q5,q6; ccx q6,q14,q7; ccx q4,q12,q5; ccx q2,q10,q3; ccx q0,q8,q1; mcx q1,q9,q10,q3; mcx q3,q11,q12,q5; mcx q5,q13,q14,q7; ccx q5,q13,q6; ccx q3,q11,q4; ccx q1,q9,q2; ccx q7,q15,q16; cx q1,q9; cx q2,q10; cx q3,q11; cx q4,q12; cx q5,q13; cx q6,q14; cx q7,q15; x q9; x q10; x q11; x q12; x q13; x q14; ccx q6,q14,q7; ccx q1,q9,q2; ccx q3,q11,q4; ccx q5,q13,q6; mcx q3,q11,q12,q5; mcx q1,q9,q10,q3; ccx q0,q8,q1; ccx q2,q10,q3; ccx q4,q12,q5; x q9; x q10; x q11; x q12; x q13; x q14; cx q5,q6; cx q3,q4; cx q1,q2; cx q2,q4; cx q4,q6; cx q4,q5; cx q2,q3; cx q6,q7; cx q0,q8; cx q1,q9; cx q2,q10; cx q3,q11; cx q4,q12; cx q5,q13; cx q6,q14; cx q7,q15; }
qreg q[17];
creg meas[17];
gate_HalfAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16];
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

OPENQASM 2.0;
include "qelib1.inc";
gate mcx q0,q1,q2,q3 { h q3; p(pi/8) q0; p(pi/8) q1; p(pi/8) q2; p(pi/8) q3; cx q0,q1; p(-pi/8) q1; cx q0,q1; cx q1,q2; p(-pi/8) q2; cx q0,q2; p(pi/8) q2; cx q1,q2; p(-pi/8) q2; cx q0,q2; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; h q3; }
gate gate_HalfAdder q0,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10 { cx q1,q6; cx q2,q7; cx q3,q8; cx q4,q9; cx q4,q10; cx q2,q3; cx q2,q4; cx q1,q2; cx q3,q4; ccx q2,q7,q3; ccx q0,q5,q1; mcx q1,q6,q7,q3; ccx q3,q8,q4; ccx q1,q6,q2; ccx q4,q9,q10; cx q1,q6; cx q2,q7; cx q3,q8; cx q4,q9; x q6; x q7; x q8; ccx q3,q8,q4; ccx q1,q6,q2; mcx q1,q6,q7,q3; ccx q0,q5,q1; ccx q2,q7,q3; x q6; x q7; x q8; cx q1,q2; cx q2,q3; cx q3,q4; cx q0,q5; cx q1,q6; cx q2,q7; cx q3,q8; cx q4,q9; }
qreg q[11];
creg meas[11];
gate_HalfAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10];
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

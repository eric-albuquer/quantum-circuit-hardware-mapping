OPENQASM 2.0;
include "qelib1.inc";
gate mcx q0,q1,q2,q3 { h q3; p(pi/8) q0; p(pi/8) q1; p(pi/8) q2; p(pi/8) q3; cx q0,q1; p(-pi/8) q1; cx q0,q1; cx q1,q2; p(-pi/8) q2; cx q0,q2; p(pi/8) q2; cx q1,q2; p(-pi/8) q2; cx q0,q2; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q1,q3; p(pi/8) q3; cx q2,q3; p(-pi/8) q3; cx q0,q3; h q3; }
gate gate_HalfAdder q0,q1,q2,q3,q4,q5,q6,q7,q8 { cx q1,q5; cx q2,q6; cx q3,q7; cx q3,q8; cx q2,q3; cx q1,q2; ccx q2,q6,q3; ccx q0,q4,q1; mcx q1,q5,q6,q3; ccx q1,q5,q2; ccx q3,q7,q8; cx q1,q5; cx q2,q6; cx q3,q7; x q5; x q6; ccx q2,q6,q3; ccx q1,q5,q2; ccx q0,q4,q1; x q5; x q6; cx q1,q2; cx q2,q3; cx q0,q4; cx q1,q5; cx q2,q6; cx q3,q7; }
qreg q[9];
creg meas[9];
gate_HalfAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];
measure q[4] -> meas[4];
measure q[5] -> meas[5];
measure q[6] -> meas[6];
measure q[7] -> meas[7];
measure q[8] -> meas[8];

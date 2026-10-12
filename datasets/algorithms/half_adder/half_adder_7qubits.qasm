OPENQASM 2.0;
include "qelib1.inc";
gate gate_HalfAdder q0,q1,q2,q3,q4,q5,q6 { cx q1,q4; cx q2,q5; cx q2,q6; cx q1,q2; ccx q0,q3,q1; ccx q1,q4,q2; ccx q2,q5,q6; cx q1,q4; cx q2,q5; x q4; ccx q1,q4,q2; ccx q0,q3,q1; x q4; cx q1,q2; cx q0,q3; cx q1,q4; cx q2,q5; }
qreg q[7];
creg meas[7];
gate_HalfAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];
measure q[4] -> meas[4];
measure q[5] -> meas[5];
measure q[6] -> meas[6];

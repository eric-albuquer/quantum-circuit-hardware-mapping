OPENQASM 2.0;
include "qelib1.inc";
gate gate_MAJ q0,q1,q2 { cx q0,q1; cx q0,q2; ccx q2,q1,q0; }
gate gate_UMA q0,q1,q2 { ccx q2,q1,q0; cx q0,q2; cx q2,q1; }
gate gate_FullAdder q0,q1,q2,q3,q4,q5,q6,q7,q8,q9 { gate_MAJ q1,q5,q0; gate_MAJ q2,q6,q1; gate_MAJ q3,q7,q2; gate_MAJ q4,q8,q3; cx q4,q9; gate_UMA q4,q8,q3; gate_UMA q3,q7,q2; gate_UMA q2,q6,q1; gate_UMA q1,q5,q0; }
qreg q[10];
creg meas[10];
gate_FullAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9];
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

OPENQASM 2.0;
include "qelib1.inc";
gate gate_MAJ q0,q1,q2 { cx q0,q1; cx q0,q2; ccx q2,q1,q0; }
gate gate_UMA q0,q1,q2 { ccx q2,q1,q0; cx q0,q2; cx q2,q1; }
gate gate_FullAdder q0,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,q15,q16,q17 { gate_MAJ q1,q9,q0; gate_MAJ q2,q10,q1; gate_MAJ q3,q11,q2; gate_MAJ q4,q12,q3; gate_MAJ q5,q13,q4; gate_MAJ q6,q14,q5; gate_MAJ q7,q15,q6; gate_MAJ q8,q16,q7; cx q8,q17; gate_UMA q8,q16,q7; gate_UMA q7,q15,q6; gate_UMA q6,q14,q5; gate_UMA q5,q13,q4; gate_UMA q4,q12,q3; gate_UMA q3,q11,q2; gate_UMA q2,q10,q1; gate_UMA q1,q9,q0; }
qreg q[18];
creg meas[18];
gate_FullAdder q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13],q[14],q[15],q[16],q[17];
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

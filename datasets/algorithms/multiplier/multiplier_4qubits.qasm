OPENQASM 2.0;
include "qelib1.inc";
gate qft q0,q1 { h q1; cp(pi/2) q1,q0; h q0; swap q0,q1; }
gate mcphase(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629231744(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate qft_dg q0,q1 { swap q0,q1; h q0; cp(-pi/2) q1,q0; h q1; }
gate gate_Multiplier q0,q1,q2,q3 { qft q2,q3; mcphase(pi) q0,q1,q3; mcphase_1951629231744(pi/2) q0,q1,q2; qft_dg q2,q3; }
qreg q[4];
creg meas[4];
gate_Multiplier q[0],q[1],q[2],q[3];
barrier q[0],q[1],q[2],q[3];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];

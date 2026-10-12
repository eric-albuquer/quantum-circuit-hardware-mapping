OPENQASM 2.0;
include "qelib1.inc";
gate mcphase(param0) q0,q1 { cp(-pi/4) q0,q1; }
gate mcphase_1951629470384(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629470576(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629470672(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629470864(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471056(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471152(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471248(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471536(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471728(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471824(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629471920(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629472208(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629472400(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629472592(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629472688(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629472880(param0) q0,q1 { cp(pi/4) q0,q1; }
gate ccircuit_953 q0,q1,q2,q3,q4,q5,q6 { ccx q0,q1,q3; ccx q0,q2,q4; ccx q0,q1,q6; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q3,q1; mcphase(-pi/4) q0,q1; ccx q0,q6,q1; mcphase_1951629470384(pi/4) q0,q1; ccx q0,q3,q1; mcphase(-pi/4) q0,q1; mcphase_1951629470576(pi/4) q0,q3; ccx q0,q6,q1; mcphase_1951629470672(pi/4) q0,q1; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q2,q1; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; ccx q0,q4,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629470864(pi/4) q0,q2; ccx q0,q4,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629471056(pi/4) q0,q2; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; ccx q0,q2,q5; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; mcphase_1951629471152(pi/4) q0,q4; ccx q0,q1,q4; mcphase_1951629471248(pi/4) q0,q1; mcphase(-pi/4) q0,q4; ccx q0,q1,q4; ccx q0,q4,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629471536(pi/4) q0,q2; ccx q0,q4,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629471728(pi/4) q0,q2; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; mcphase_1951629471824(pi/4) q0,q4; ccx q0,q1,q4; mcphase_1951629471920(pi/4) q0,q1; mcphase(-pi/4) q0,q4; ccx q0,q1,q4; ccx q0,q2,q1; ccx q0,q1,q4; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q6,q3; mcphase(-pi/4) q0,q3; mcphase_1951629472208(pi/4) q0,q6; ccx q0,q6,q3; ccx q0,q3,q1; mcphase(-pi/4) q0,q1; ccx q0,q6,q1; mcphase_1951629472400(pi/4) q0,q1; ccx q0,q3,q1; mcphase(-pi/4) q0,q1; mcphase_1951629472592(pi/4) q0,q3; ccx q0,q6,q1; mcphase_1951629472688(pi/4) q0,q1; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q6,q3; mcphase(-pi/4) q0,q3; mcphase_1951629472880(pi/4) q0,q6; ccx q0,q6,q3; ccx q0,q1,q6; ccx q0,q6,q3; }
qreg a[2];
qreg b[2];
qreg out[4];
qreg helper[1];
creg meas[9];
ccircuit_953 a[0],b[0],b[1],out[0],out[1],out[2],helper[0];
ccircuit_953 a[1],b[0],b[1],out[1],out[2],out[3],helper[0];
barrier a[0],a[1],b[0],b[1],out[0],out[1],out[2],out[3],helper[0];
measure a[0] -> meas[0];
measure a[1] -> meas[1];
measure b[0] -> meas[2];
measure b[1] -> meas[3];
measure out[0] -> meas[4];
measure out[1] -> meas[5];
measure out[2] -> meas[6];
measure out[3] -> meas[7];
measure helper[0] -> meas[8];

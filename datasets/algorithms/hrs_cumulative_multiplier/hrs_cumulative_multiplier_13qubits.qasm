OPENQASM 2.0;
include "qelib1.inc";
gate mcphase(param0) q0,q1 { cp(-pi/4) q0,q1; }
gate mcphase_1951629807776(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629807968(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629808064(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629808256(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629808448(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629808544(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629808640(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629808928(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809120(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809216(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809312(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809600(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809792(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809888(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629809984(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629810272(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629810464(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629810560(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629810656(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629810944(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629811136(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629811328(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629811424(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629811616(param0) q0,q1 { cp(pi/4) q0,q1; }
gate ccircuit_990 q0,q1,q2,q3,q4,q5,q6,q7,q8 { ccx q0,q1,q4; ccx q0,q2,q5; ccx q0,q3,q6; ccx q0,q1,q8; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q4,q1; mcphase(-pi/4) q0,q1; ccx q0,q8,q1; mcphase_1951629807776(pi/4) q0,q1; ccx q0,q4,q1; mcphase(-pi/4) q0,q1; mcphase_1951629807968(pi/4) q0,q4; ccx q0,q8,q1; mcphase_1951629808064(pi/4) q0,q1; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q2,q1; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; ccx q0,q5,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629808256(pi/4) q0,q2; ccx q0,q5,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629808448(pi/4) q0,q2; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; ccx q0,q3,q2; s q3; h q3; t q3; cx q0,q3; tdg q3; h q3; sdg q3; mcphase_1951629808544(pi/4) q0,q5; ccx q0,q1,q5; mcphase_1951629808640(pi/4) q0,q1; mcphase(-pi/4) q0,q5; ccx q0,q1,q5; ccx q0,q6,q3; mcphase(-pi/4) q0,q3; ccx q0,q2,q3; mcphase_1951629808928(pi/4) q0,q3; ccx q0,q6,q3; mcphase(-pi/4) q0,q3; ccx q0,q2,q3; mcphase_1951629809120(pi/4) q0,q3; s q3; h q3; t q3; cx q0,q3; tdg q3; h q3; sdg q3; ccx q0,q3,q7; s q3; h q3; t q3; cx q0,q3; tdg q3; h q3; sdg q3; mcphase_1951629809216(pi/4) q0,q6; ccx q0,q2,q6; mcphase_1951629809312(pi/4) q0,q2; mcphase(-pi/4) q0,q6; ccx q0,q2,q6; ccx q0,q6,q3; mcphase(-pi/4) q0,q3; ccx q0,q2,q3; mcphase_1951629809600(pi/4) q0,q3; ccx q0,q6,q3; mcphase(-pi/4) q0,q3; ccx q0,q2,q3; mcphase_1951629809792(pi/4) q0,q3; s q3; h q3; t q3; cx q0,q3; tdg q3; h q3; sdg q3; mcphase_1951629809888(pi/4) q0,q6; ccx q0,q2,q6; mcphase_1951629809984(pi/4) q0,q2; mcphase(-pi/4) q0,q6; ccx q0,q2,q6; ccx q0,q3,q2; ccx q0,q2,q6; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; ccx q0,q5,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629810272(pi/4) q0,q2; ccx q0,q5,q2; mcphase(-pi/4) q0,q2; ccx q0,q1,q2; mcphase_1951629810464(pi/4) q0,q2; s q2; h q2; t q2; cx q0,q2; tdg q2; h q2; sdg q2; mcphase_1951629810560(pi/4) q0,q5; ccx q0,q1,q5; mcphase_1951629810656(pi/4) q0,q1; mcphase(-pi/4) q0,q5; ccx q0,q1,q5; ccx q0,q2,q1; ccx q0,q1,q5; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q8,q4; mcphase(-pi/4) q0,q4; mcphase_1951629810944(pi/4) q0,q8; ccx q0,q8,q4; ccx q0,q4,q1; mcphase(-pi/4) q0,q1; ccx q0,q8,q1; mcphase_1951629811136(pi/4) q0,q1; ccx q0,q4,q1; mcphase(-pi/4) q0,q1; mcphase_1951629811328(pi/4) q0,q4; ccx q0,q8,q1; mcphase_1951629811424(pi/4) q0,q1; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q8,q4; mcphase(-pi/4) q0,q4; mcphase_1951629811616(pi/4) q0,q8; ccx q0,q8,q4; ccx q0,q1,q8; ccx q0,q8,q4; }
qreg a[3];
qreg b[3];
qreg out[6];
qreg helper[1];
creg meas[13];
ccircuit_990 a[0],b[0],b[1],b[2],out[0],out[1],out[2],out[3],helper[0];
ccircuit_990 a[1],b[0],b[1],b[2],out[1],out[2],out[3],out[4],helper[0];
ccircuit_990 a[2],b[0],b[1],b[2],out[2],out[3],out[4],out[5],helper[0];
barrier a[0],a[1],a[2],b[0],b[1],b[2],out[0],out[1],out[2],out[3],out[4],out[5],helper[0];
measure a[0] -> meas[0];
measure a[1] -> meas[1];
measure a[2] -> meas[2];
measure b[0] -> meas[3];
measure b[1] -> meas[4];
measure b[2] -> meas[5];
measure out[0] -> meas[6];
measure out[1] -> meas[7];
measure out[2] -> meas[8];
measure out[3] -> meas[9];
measure out[4] -> meas[10];
measure out[5] -> meas[11];
measure helper[0] -> meas[12];

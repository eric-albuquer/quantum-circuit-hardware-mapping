OPENQASM 2.0;
include "qelib1.inc";
gate mcphase(param0) q0,q1 { cp(-pi/4) q0,q1; }
gate mcphase_1951629230448(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629230400(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629230304(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629232128(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629232320(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629233184(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629232944(param0) q0,q1 { cp(pi/4) q0,q1; }
gate mcphase_1951629231696(param0) q0,q1 { cp(pi/4) q0,q1; }
gate ccircuit_930 q0,q1,q2,q3,q4 { ccx q0,q1,q2; ccx q0,q1,q4; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q2,q1; mcphase(-pi/4) q0,q1; ccx q0,q4,q1; mcphase_1951629230448(pi/4) q0,q1; ccx q0,q2,q1; mcphase(-pi/4) q0,q1; mcphase_1951629230400(pi/4) q0,q2; ccx q0,q4,q1; mcphase_1951629230304(pi/4) q0,q1; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q1,q3; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q4,q2; mcphase(-pi/4) q0,q2; mcphase_1951629232128(pi/4) q0,q4; ccx q0,q4,q2; ccx q0,q2,q1; mcphase(-pi/4) q0,q1; ccx q0,q4,q1; mcphase_1951629232320(pi/4) q0,q1; ccx q0,q2,q1; mcphase(-pi/4) q0,q1; mcphase_1951629233184(pi/4) q0,q2; ccx q0,q4,q1; mcphase_1951629232944(pi/4) q0,q1; s q1; h q1; t q1; cx q0,q1; tdg q1; h q1; sdg q1; ccx q0,q4,q2; mcphase(-pi/4) q0,q2; mcphase_1951629231696(pi/4) q0,q4; ccx q0,q4,q2; ccx q0,q1,q4; ccx q0,q4,q2; }
qreg a[1];
qreg b[1];
qreg out[2];
qreg helper[1];
creg meas[5];
ccircuit_930 a[0],b[0],out[0],out[1],helper[0];
barrier a[0],b[0],out[0],out[1],helper[0];
measure a[0] -> meas[0];
measure b[0] -> meas[1];
measure out[0] -> meas[2];
measure out[1] -> meas[3];
measure helper[0] -> meas[4];

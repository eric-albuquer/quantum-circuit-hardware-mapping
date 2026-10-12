OPENQASM 2.0;
include "qelib1.inc";
gate qft q0,q1,q2,q3,q4,q5 { h q5; cp(pi/2) q5,q4; cp(pi/4) q5,q3; cp(pi/8) q5,q2; cp(pi/16) q5,q1; cp(pi/32) q5,q0; h q4; cp(pi/2) q4,q3; cp(pi/4) q4,q2; cp(pi/8) q4,q1; cp(pi/16) q4,q0; h q3; cp(pi/2) q3,q2; cp(pi/4) q3,q1; cp(pi/8) q3,q0; h q2; cp(pi/2) q2,q1; cp(pi/4) q2,q0; h q1; cp(pi/2) q1,q0; h q0; swap q0,q5; swap q1,q4; swap q2,q3; }
gate mcphase(param0) q0,q1,q2 { cx q0,q2; rz(-4*pi) q2; cx q1,q2; rz(4*pi) q2; cx q0,q2; rz(-4*pi) q2; cx q1,q2; rz(4*pi) q2; crz(8*pi) q0,q1; p(4*pi) q0; }
gate mcphase_1951629640576(param0) q0,q1,q2 { cx q0,q2; rz(-2*pi) q2; cx q1,q2; rz(2*pi) q2; cx q0,q2; rz(-2*pi) q2; cx q1,q2; rz(2*pi) q2; crz(4*pi) q0,q1; p(2*pi) q0; }
gate mcphase_1951629645904(param0) q0,q1,q2 { cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; crz(2*pi) q0,q1; p(pi) q0; }
gate mcphase_1951629646192(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629646240(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629646432(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629640384(param0) q0,q1,q2 { cx q0,q2; rz(-2*pi) q2; cx q1,q2; rz(2*pi) q2; cx q0,q2; rz(-2*pi) q2; cx q1,q2; rz(2*pi) q2; crz(4*pi) q0,q1; p(2*pi) q0; }
gate mcphase_1951629646864(param0) q0,q1,q2 { cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; crz(2*pi) q0,q1; p(pi) q0; }
gate mcphase_1951629647152(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629646336(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629646480(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629649168(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629646960(param0) q0,q1,q2 { cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; crz(2*pi) q0,q1; p(pi) q0; }
gate mcphase_1951629647104(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629645664(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629649648(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629640864(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629647680(param0) q0,q1,q2 { cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; crz(pi/16) q0,q1; p(pi/32) q0; }
gate mcphase_1951629647440(param0) q0,q1,q2 { cx q0,q2; rz(-2*pi) q2; cx q1,q2; rz(2*pi) q2; cx q0,q2; rz(-2*pi) q2; cx q1,q2; rz(2*pi) q2; crz(4*pi) q0,q1; p(2*pi) q0; }
gate mcphase_1951629647872(param0) q0,q1,q2 { cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; crz(2*pi) q0,q1; p(pi) q0; }
gate mcphase_1951629647200(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629648496(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629648016(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629649216(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629644320(param0) q0,q1,q2 { cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; crz(2*pi) q0,q1; p(pi) q0; }
gate mcphase_1951629648736(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629647968(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629649408(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629648976(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629649120(param0) q0,q1,q2 { cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; crz(pi/16) q0,q1; p(pi/32) q0; }
gate mcphase_1951629649600(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629646096(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629650416(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629641536(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629646912(param0) q0,q1,q2 { cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; crz(pi/16) q0,q1; p(pi/32) q0; }
gate mcphase_1951629648208(param0) q0,q1,q2 { cx q0,q2; rz(-pi/64) q2; cx q1,q2; rz(pi/64) q2; cx q0,q2; rz(-pi/64) q2; cx q1,q2; rz(pi/64) q2; crz(pi/32) q0,q1; p(pi/64) q0; }
gate mcphase_1951629645232(param0) q0,q1,q2 { cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; cx q0,q2; rz(-pi) q2; cx q1,q2; rz(pi) q2; crz(2*pi) q0,q1; p(pi) q0; }
gate mcphase_1951629645376(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629644752(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629645040(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629646384(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629646672(param0) q0,q1,q2 { cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; crz(pi/16) q0,q1; p(pi/32) q0; }
gate mcphase_1951629650656(param0) q0,q1,q2 { cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; cx q0,q2; rz(-pi/2) q2; cx q1,q2; rz(pi/2) q2; crz(pi) q0,q1; p(pi/2) q0; }
gate mcphase_1951629640480(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951629640768(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951629640048(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951629645136(param0) q0,q1,q2 { cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; crz(pi/16) q0,q1; p(pi/32) q0; }
gate mcphase_1951629642256(param0) q0,q1,q2 { cx q0,q2; rz(-pi/64) q2; cx q1,q2; rz(pi/64) q2; cx q0,q2; rz(-pi/64) q2; cx q1,q2; rz(pi/64) q2; crz(pi/32) q0,q1; p(pi/64) q0; }
gate mcphase_1951629644512(param0) q0,q1,q2 { cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; cx q0,q2; rz(-pi/4) q2; cx q1,q2; rz(pi/4) q2; crz(pi/2) q0,q1; p(pi/4) q0; }
gate mcphase_1951628482016(param0) q0,q1,q2 { cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; cx q0,q2; rz(-pi/8) q2; cx q1,q2; rz(pi/8) q2; crz(pi/4) q0,q1; p(pi/8) q0; }
gate mcphase_1951628492576(param0) q0,q1,q2 { cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; cx q0,q2; rz(-pi/16) q2; cx q1,q2; rz(pi/16) q2; crz(pi/8) q0,q1; p(pi/16) q0; }
gate mcphase_1951628492528(param0) q0,q1,q2 { cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; cx q0,q2; rz(-pi/32) q2; cx q1,q2; rz(pi/32) q2; crz(pi/16) q0,q1; p(pi/32) q0; }
gate mcphase_1951629463424(param0) q0,q1,q2 { cx q0,q2; rz(-pi/64) q2; cx q1,q2; rz(pi/64) q2; cx q0,q2; rz(-pi/64) q2; cx q1,q2; rz(pi/64) q2; crz(pi/32) q0,q1; p(pi/64) q0; }
gate mcphase_1951629462944(param0) q0,q1,q2 { cx q0,q2; rz(-0.02454369260617026) q2; cx q1,q2; rz(0.02454369260617026) q2; cx q0,q2; rz(-0.02454369260617026) q2; cx q1,q2; rz(0.02454369260617026) q2; crz(pi/64) q0,q1; p(0.02454369260617026) q0; }
gate qft_dg q0,q1,q2,q3,q4,q5 { swap q2,q3; swap q1,q4; swap q0,q5; h q0; cp(-pi/2) q1,q0; h q1; cp(-pi/4) q2,q0; cp(-pi/2) q2,q1; h q2; cp(-pi/8) q3,q0; cp(-pi/4) q3,q1; cp(-pi/2) q3,q2; h q3; cp(-pi/16) q4,q0; cp(-pi/8) q4,q1; cp(-pi/4) q4,q2; cp(-pi/2) q4,q3; h q4; cp(-pi/32) q5,q0; cp(-pi/16) q5,q1; cp(-pi/8) q5,q2; cp(-pi/4) q5,q3; cp(-pi/2) q5,q4; h q5; }
gate gate_Multiplier q0,q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11 { qft q6,q7,q8,q9,q10,q11; mcphase(16*pi) q2,q5,q11; mcphase_1951629640576(8*pi) q2,q5,q10; mcphase_1951629645904(4*pi) q2,q5,q9; mcphase_1951629646192(2*pi) q2,q5,q8; mcphase_1951629646240(pi) q2,q5,q7; mcphase_1951629646432(pi/2) q2,q5,q6; mcphase_1951629640384(8*pi) q2,q4,q11; mcphase_1951629646864(4*pi) q2,q4,q10; mcphase_1951629647152(2*pi) q2,q4,q9; mcphase_1951629646336(pi) q2,q4,q8; mcphase_1951629646480(pi/2) q2,q4,q7; mcphase_1951629649168(pi/4) q2,q4,q6; mcphase_1951629646960(4*pi) q2,q3,q11; mcphase_1951629647104(2*pi) q2,q3,q10; mcphase_1951629645664(pi) q2,q3,q9; mcphase_1951629649648(pi/2) q2,q3,q8; mcphase_1951629640864(pi/4) q2,q3,q7; mcphase_1951629647680(pi/8) q2,q3,q6; mcphase_1951629647440(8*pi) q1,q5,q11; mcphase_1951629647872(4*pi) q1,q5,q10; mcphase_1951629647200(2*pi) q1,q5,q9; mcphase_1951629648496(pi) q1,q5,q8; mcphase_1951629648016(pi/2) q1,q5,q7; mcphase_1951629649216(pi/4) q1,q5,q6; mcphase_1951629644320(4*pi) q1,q4,q11; mcphase_1951629648736(2*pi) q1,q4,q10; mcphase_1951629647968(pi) q1,q4,q9; mcphase_1951629649408(pi/2) q1,q4,q8; mcphase_1951629648976(pi/4) q1,q4,q7; mcphase_1951629649120(pi/8) q1,q4,q6; mcphase_1951629649600(2*pi) q1,q3,q11; mcphase_1951629646096(pi) q1,q3,q10; mcphase_1951629650416(pi/2) q1,q3,q9; mcphase_1951629641536(pi/4) q1,q3,q8; mcphase_1951629646912(pi/8) q1,q3,q7; mcphase_1951629648208(pi/16) q1,q3,q6; mcphase_1951629645232(4*pi) q0,q5,q11; mcphase_1951629645376(2*pi) q0,q5,q10; mcphase_1951629644752(pi) q0,q5,q9; mcphase_1951629645040(pi/2) q0,q5,q8; mcphase_1951629646384(pi/4) q0,q5,q7; mcphase_1951629646672(pi/8) q0,q5,q6; mcphase_1951629650656(2*pi) q0,q4,q11; mcphase_1951629640480(pi) q0,q4,q10; mcphase_1951629640768(pi/2) q0,q4,q9; mcphase_1951629640048(pi/4) q0,q4,q8; mcphase_1951629645136(pi/8) q0,q4,q7; mcphase_1951629642256(pi/16) q0,q4,q6; mcphase_1951629644512(pi) q0,q3,q11; mcphase_1951628482016(pi/2) q0,q3,q10; mcphase_1951628492576(pi/4) q0,q3,q9; mcphase_1951628492528(pi/8) q0,q3,q8; mcphase_1951629463424(pi/16) q0,q3,q7; mcphase_1951629462944(pi/32) q0,q3,q6; qft_dg q6,q7,q8,q9,q10,q11; }
qreg q[12];
creg meas[12];
gate_Multiplier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11];
barrier q[0],q[1],q[2],q[3],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11];
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

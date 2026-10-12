OPENQASM 3.0;
include "stdgates.inc";
gate rxx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_0;
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
  h _gate_q_0;
}
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate dcx _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
}
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
gate ryy(p0) _gate_q_0, _gate_q_1 {
  sxdg _gate_q_0;
  sxdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  sx _gate_q_0;
  sx _gate_q_1;
}
gate cu3(p0, p1, p2) _gate_q_0, _gate_q_1 {
  p(0.5*p2 + 0.5*p1) _gate_q_0;
  p(0.5*p2 - 0.5*p1) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U((-0.5)*p0, 0, (-0.5)*p1 - 0.5*p2) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U(0.5*p0, p1, 0) _gate_q_1;
}
gate ecr _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  sx _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  x _gate_q_0;
}
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
gate xx_minus_yy(p0, p1) _gate_q_0, _gate_q_1 {
  rz(-p1) _gate_q_1;
  sdg _gate_q_0;
  sx _gate_q_0;
  s _gate_q_0;
  s _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  ry(0.5*p0) _gate_q_0;
  ry((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  sdg _gate_q_1;
  sdg _gate_q_0;
  sxdg _gate_q_0;
  s _gate_q_0;
  rz(p1) _gate_q_1;
}
gate cu1(p0) _gate_q_0, _gate_q_1 {
  p(0.5*p0) _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  p((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  p(0.5*p0) _gate_q_1;
}
gate xx_plus_yy(p0, p1) _gate_q_0, _gate_q_1 {
  rz(p1) _gate_q_0;
  sdg _gate_q_1;
  sx _gate_q_1;
  s _gate_q_1;
  s _gate_q_0;
  cx _gate_q_1, _gate_q_0;
  ry((-0.5)*p0) _gate_q_1;
  ry((-0.5)*p0) _gate_q_0;
  cx _gate_q_1, _gate_q_0;
  sdg _gate_q_0;
  sdg _gate_q_1;
  sxdg _gate_q_1;
  s _gate_q_1;
  rz(-p1) _gate_q_0;
}
gate cs _gate_q_0, _gate_q_1 {
  t _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  tdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
}
gate csx _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cs _gate_q_0, _gate_q_1;
  h _gate_q_1;
}
gate rzx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
}
gate csdg _gate_q_0, _gate_q_1 {
  tdg _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  tdg _gate_q_1;
}
qubit[10] q;
rxx(1.155760440473277) q[6], q[1];
rx(6.092842448159141) q[4];
sxdg q[0];
dcx q[9], q[3];
ch q[2], q[7];
iswap q[8], q[5];
crx(0.2944718087631289) q[0], q[3];
ryy(4.049196782337862) q[5], q[6];
swap q[2], q[7];
crz(0.897007264085505) q[9], q[8];
crz(3.4178154130735043) q[4], q[1];
ch q[2], q[1];
crx(2.6431747666790955) q[3], q[6];
cx q[5], q[9];
rxx(4.729174648057121) q[8], q[0];
cu3(2.9920687806580286, 1.66101831664389, 1.4423271852698232) q[7], q[4];
sdg q[5];
ecr q[3], q[2];
iswap q[7], q[0];
crz(2.3498780549545013) q[9], q[8];
ryy(4.435109509427205) q[1], q[4];
dcx q[7], q[6];
cu(3.2351188988561663, 1.9185512216543277, 2.934187473581693, 3.747582418657624) q[9], q[5];
rxx(5.895854850295593) q[4], q[2];
rzz(3.823110479809863) q[1], q[8];
swap q[3], q[0];
cu3(2.6394660108554615, 3.663747333546797, 0.8184457221647153) q[1], q[8];
rzz(0.4125756807850398) q[3], q[2];
xx_minus_yy(4.568689708538684, 3.4072033520191405) q[5], q[7];
xx_minus_yy(1.4906066725184444, 1.1894650189274736) q[0], q[9];
iswap q[4], q[6];
cx q[7], q[1];
ch q[0], q[4];
crx(0.6507025381455112) q[9], q[8];
cry(5.287179191218293) q[6], q[2];
crz(3.6056015225582247) q[5], q[3];
cu1(3.2818608700795475) q[1], q[4];
cy q[8], q[9];
swap q[2], q[7];
ecr q[0], q[6];
cx q[3], q[5];
ch q[5], q[7];
xx_plus_yy(4.5673402557543685, 4.496576342583439) q[9], q[6];
ecr q[1], q[2];
dcx q[4], q[3];
csx q[0], q[8];
cy q[3], q[0];
ch q[4], q[5];
ryy(0.03917356416742331) q[7], q[8];
cx q[6], q[1];
iswap q[2], q[9];
ryy(1.2057412744220795) q[7], q[2];
rzz(3.013144033869881) q[3], q[4];
cu3(1.094649879314849, 1.0938386419498176, 3.766684236212858) q[5], q[6];
rzz(2.3929494664264794) q[0], q[9];
swap q[8], q[1];
ryy(4.800616816012363) q[6], q[0];
swap q[3], q[9];
swap q[2], q[7];
swap q[4], q[5];
crx(4.927128448929951) q[1], q[8];
rxx(2.527654311012973) q[6], q[8];
rzz(4.426363719558188) q[4], q[1];
tdg q[9];
ch q[5], q[3];
crz(3.9719384122597607) q[7], q[0];
s q[2];
ecr q[4], q[0];
rzx(4.570755725085939) q[3], q[8];
iswap q[7], q[6];
csdg q[5], q[2];
ecr q[9], q[1];
cp(1.2592856537697026) q[9], q[8];
crx(3.7872581018445377) q[2], q[6];
cu(2.5169765603531418, 5.148799461287167, 3.5018365732191974, 0.7096812655151167) q[4], q[3];
sx q[5];
crz(0.3172021369741713) q[0], q[7];
z q[1];
rzz(2.0284677100803297) q[3], q[6];
ecr q[7], q[1];
dcx q[9], q[4];
crx(0.9707636575534692) q[8], q[5];
crz(4.792359032387942) q[0], q[2];
cx q[3], q[8];
sxdg q[9];
rxx(3.4303879094454506) q[6], q[0];
iswap q[2], q[5];
cy q[1], q[4];
rzx(1.7182901157396462) q[4], q[6];
cy q[9], q[1];
x q[0];
cy q[8], q[7];
cu1(4.814761038118783) q[2], q[5];
ecr q[5], q[0];
rxx(0.09087046996995786) q[3], q[8];
cx q[1], q[4];
ryy(4.925104300780851) q[6], q[7];
swap q[2], q[9];
iswap q[9], q[5];
cry(6.181116230379153) q[2], q[4];
cu1(2.547097757445968) q[3], q[1];
csx q[0], q[8];
tdg q[6];

OPENQASM 3.0;
include "stdgates.inc";
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
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
gate ryy(p0) _gate_q_0, _gate_q_1 {
  sxdg _gate_q_0;
  sxdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  sx _gate_q_0;
  sx _gate_q_1;
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
gate csdg _gate_q_0, _gate_q_1 {
  tdg _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  tdg _gate_q_1;
}
gate rzx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
}
gate cu1(p0) _gate_q_0, _gate_q_1 {
  p(0.5*p0) _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  p((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  p(0.5*p0) _gate_q_1;
}
gate rxx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_0;
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
  h _gate_q_0;
}
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
gate r(p0, p1) _gate_q_0 {
  U(p0, -pi/2 + p1, pi/2 - p1) _gate_q_0;
}
gate dcx _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
}
gate ecr _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  sx _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  x _gate_q_0;
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
qubit[4] q;
xx_plus_yy(3.886830643665057, 1.1499206998965035) q[0], q[2];
s q[3];
ryy(2.137145164907456) q[0], q[2];
cz q[3], q[1];
csx q[2], q[0];
ryy(1.3600060020732931) q[1], q[3];
swap q[1], q[3];
csdg q[0], q[2];
z q[0];
rzx(5.447881885490129) q[1], q[2];
s q[3];
csx q[3], q[0];
rx(5.0333351285069545) q[1];
h q[2];
u3(6.189935665783626, 3.355539258280568, 3.98924219010153) q[0];
cy q[1], q[3];
s q[3];
cy q[2], q[1];
cx q[0], q[2];
t q[1];
s q[3];
tdg q[2];
sx q[0];
cu1(0.581713654811101) q[1], q[3];
z q[1];
cy q[0], q[2];
crz(4.423551278387946) q[1], q[3];
rxx(3.5590289053212025) q[2], q[0];
cry(3.9101936863363402) q[1], q[3];
rxx(0.22097502584582912) q[0], q[2];
iswap q[0], q[1];
r(6.257454176123224, 1.470659035624014) q[2];
cry(4.707049495105035) q[1], q[0];
rzx(3.529351957451415) q[3], q[2];
cy q[3], q[0];
cz q[1], q[2];
iswap q[2], q[3];
cu(2.6926786310355935, 4.843591485461748, 2.2983694731242648, 1.055979205451113) q[1], q[0];
z q[3];
crx(6.19732606700017) q[1], q[0];
csx q[0], q[3];
cp(4.934416875779568) q[1], q[2];
cy q[3], q[2];
dcx q[0], q[1];
rx(2.9965633399704377) q[2];
rz(3.7977728491704927) q[0];
sdg q[3];
id q[1];
crz(5.115217645643801) q[1], q[0];
ecr q[2], q[3];
t q[1];
cu(0.17715584019573305, 0.2852019800705348, 0.2945082342465872, 0.129681903950976) q[3], q[0];
swap q[0], q[1];
csdg q[3], q[2];
xx_plus_yy(1.3397909237831427, 1.3836869545894954) q[0], q[3];
ryy(0.07950779013440781) q[2], q[1];
ryy(1.7537959149545277) q[3], q[0];
cry(1.2158478953630112) q[1], q[2];
swap q[1], q[0];
p(1.8072614691892595) q[3];
xx_minus_yy(3.939291389703931, 2.9899448589646345) q[2], q[1];
dcx q[3], q[0];
swap q[3], q[0];
crz(6.283121977845731) q[1], q[2];
cry(4.3347931461659694) q[2], q[0];
sdg q[3];
r(4.891492665060487, 4.946436519821694) q[1];

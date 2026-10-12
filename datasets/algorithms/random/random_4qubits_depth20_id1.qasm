OPENQASM 3.0;
include "stdgates.inc";
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
gate cu3(p0, p1, p2) _gate_q_0, _gate_q_1 {
  p(0.5*p2 + 0.5*p1) _gate_q_0;
  p(0.5*p2 - 0.5*p1) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U((-0.5)*p0, 0, (-0.5)*p1 - 0.5*p2) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U(0.5*p0, p1, 0) _gate_q_1;
}
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
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
gate cu1(p0) _gate_q_0, _gate_q_1 {
  p(0.5*p0) _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  p((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  p(0.5*p0) _gate_q_1;
}
gate rzx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
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
gate dcx _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
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
gate ryy(p0) _gate_q_0, _gate_q_1 {
  sxdg _gate_q_0;
  sxdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  sx _gate_q_0;
  sx _gate_q_1;
}
qubit[4] q;
iswap q[2], q[1];
cu3(2.582757277516436, 2.516455616531766, 3.441997657582075) q[0], q[3];
rzz(3.5577447178497126) q[2], q[1];
sx q[3];
cu(0.3697277466618904, 0.9540096140216281, 3.891043268838168, 3.941627346653602) q[3], q[0];
cu(4.795585020487913, 1.335219760605533, 1.3877049089430507, 2.1244169899553205) q[1], q[2];
h q[0];
xx_plus_yy(5.063477490403308, 2.424371405672042) q[3], q[2];
cu3(4.996460174327156, 5.780806572690481, 5.920152092166318) q[0], q[3];
crz(0.1975929483625605) q[2], q[1];
cry(0.0648208325502816) q[1], q[2];
cu1(4.324554020172381) q[0], q[3];
swap q[1], q[3];
rzx(6.224786407971964) q[0], q[2];
rxx(1.3282296769673507) q[1], q[2];
cry(4.293168826750369) q[0], q[3];
cu(5.535444709172632, 5.9954480645891115, 1.5720430883374028, 5.326631407502128) q[2], q[1];
cp(3.743523382753939) q[0], q[3];
ry(1.5412587272401235) q[2];
z q[3];
dcx q[0], q[1];
rxx(0.5277843489551702) q[2], q[1];
dcx q[0], q[3];
rzx(0.9991153628575924) q[3], q[1];
t q[0];
p(4.8087138729132946) q[2];
csx q[1], q[2];
crz(3.5706381535315774) q[3], q[0];
rzx(1.5402261088407887) q[2], q[0];
crz(6.218396068410529) q[3], q[1];
cy q[3], q[1];
sxdg q[2];
rzz(4.671638337758642) q[2], q[3];
cp(3.837715958100113) q[0], q[1];
z q[1];
ryy(1.268593280209481) q[3], q[0];
rzx(2.500253806259011) q[2], q[0];
csx q[1], q[3];
cy q[2], q[1];
cy q[0], q[3];
cs q[0], q[2];
iswap q[3], q[1];

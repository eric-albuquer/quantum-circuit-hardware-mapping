OPENQASM 3.0;
include "stdgates.inc";
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
gate ecr _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  sx _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  x _gate_q_0;
}
gate cu1(p0) _gate_q_0, _gate_q_1 {
  p(0.5*p0) _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  p((-0.5)*p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  p(0.5*p0) _gate_q_1;
}
gate cu3(p0, p1, p2) _gate_q_0, _gate_q_1 {
  p(0.5*p2 + 0.5*p1) _gate_q_0;
  p(0.5*p2 - 0.5*p1) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U((-0.5)*p0, 0, (-0.5)*p1 - 0.5*p2) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U(0.5*p0, p1, 0) _gate_q_1;
}
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
qubit[8] q;
cx q[3], q[6];
csx q[1], q[7];
cry(3.873088635169376) q[5], q[0];
cp(3.510782114358784) q[4], q[2];
ch q[6], q[2];
tdg q[7];
rzx(2.254446263523136) q[0], q[3];
s q[5];
rxx(4.920495054203086) q[1], q[4];
cz q[0], q[3];
cs q[4], q[1];
ch q[5], q[7];
crx(5.870852474851286) q[2], q[6];
dcx q[1], q[3];
ecr q[7], q[5];
cu(5.3093259885030095, 2.2225585437801976, 2.209489365514018, 0.8469457836864686) q[2], q[0];
swap q[4], q[6];
cx q[5], q[7];
rxx(3.9470673311347917) q[6], q[0];
s q[3];
cz q[2], q[4];
crx(5.589941477877426) q[7], q[0];
cz q[1], q[5];
ch q[3], q[6];
cu1(2.298349057857334) q[4], q[2];
csx q[1], q[2];
cu3(1.0567258103423918, 5.522999367323524, 0.08813952958393605) q[3], q[5];
dcx q[0], q[4];
cs q[6], q[7];
cry(2.2644387595047246) q[4], q[0];
x q[2];
cy q[3], q[6];
cz q[5], q[1];
sxdg q[7];
cp(4.896698676330728) q[7], q[1];
sxdg q[3];
dcx q[0], q[6];
cu(3.391890211588792, 3.248821005169959, 3.3731463158984956, 4.81263022937319) q[5], q[2];
swap q[5], q[4];
cu(0.6681990133558239, 4.138857430879381, 4.038500775900727, 0.8037288956159282) q[0], q[1];
dcx q[6], q[2];
cp(1.61598636338379) q[7], q[3];

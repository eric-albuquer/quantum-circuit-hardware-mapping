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
gate ecr _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  sx _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  x _gate_q_0;
}
gate cu3(p0, p1, p2) _gate_q_0, _gate_q_1 {
  p(0.5*p2 + 0.5*p1) _gate_q_0;
  p(0.5*p2 - 0.5*p1) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U((-0.5)*p0, 0, (-0.5)*p1 - 0.5*p2) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U(0.5*p0, p1, 0) _gate_q_1;
}
gate r(p0, p1) _gate_q_0 {
  U(p0, -pi/2 + p1, pi/2 - p1) _gate_q_0;
}
gate csdg _gate_q_0, _gate_q_1 {
  tdg _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  tdg _gate_q_1;
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
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
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
gate rxx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_0;
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
  h _gate_q_0;
}
qubit[6] q;
u1(2.9437849860801952) q[3];
csx q[5], q[4];
u3(2.1028030111116074, 1.564962996271388, 1.3930782306599372) q[2];
id q[0];
h q[1];
sdg q[0];
h q[4];
x q[5];
tdg q[1];
csx q[2], q[3];
ecr q[3], q[2];
cu3(2.6303382039494347, 3.497094493570497, 0.971422904416596) q[0], q[1];
r(5.971254533226692, 2.7410291330049588) q[4];
u1(2.245381724988159) q[5];
u2(1.8580405468586345, 5.418017147509415) q[5];
ecr q[1], q[4];
csdg q[0], q[3];
sxdg q[2];
xx_plus_yy(4.944584920006568, 4.210604321514957) q[3], q[0];
t q[1];
z q[2];
cy q[4], q[5];
xx_plus_yy(3.2637707011258326, 5.988658181852975) q[1], q[4];
u2(4.528232994631595, 5.942528168375956) q[3];
p(4.109241547570321) q[2];
x q[5];
U(5.270296961652636, 2.1368972785536227, 4.7938744597722565) q[0];
r(3.7166491490506086, 6.175418383310401) q[5];
cu3(4.875201154854471, 4.814865076505934, 0.03890673469567613) q[3], q[0];
cs q[4], q[2];
id q[1];
rzz(1.4972173587301867) q[3], q[2];
dcx q[4], q[0];
u2(0.1889127759415749, 4.327162655170444) q[5];
u2(5.90757484747601, 3.600393685917996) q[1];
r(2.920982605232868, 5.65550355496538) q[4];
U(5.812830073523444, 5.719507997404958, 1.0310908681549784) q[1];
iswap q[0], q[2];
cu3(1.0540216810540455, 3.5813824158325476, 2.949950751452033) q[5], q[3];
rxx(4.1540672349476) q[5], q[4];
cu(2.6622557886722236, 2.459793093233866, 2.426854654222405, 2.7745147732964806) q[1], q[0];
rx(5.309486426983012) q[2];
ry(0.9081868385156834) q[3];

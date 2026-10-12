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
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
gate r(p0, p1) _gate_q_0 {
  U(p0, -pi/2 + p1, pi/2 - p1) _gate_q_0;
}
qubit[4] q;
y q[0];
u3(4.696185761198462, 4.532526182773045, 3.5172049573352444) q[2];
u3(0.9715283512578583, 4.183926218777358, 4.305995435584083) q[1];
h q[0];
t q[2];
id q[3];
U(5.921582057832755, 4.1292523296609085, 5.8446413605582945) q[1];
sxdg q[0];
s q[3];
xx_plus_yy(6.125522294959695, 2.9761883045652655) q[2], q[1];
t q[2];
sx q[1];
tdg q[3];
s q[0];
x q[2];
t q[3];
u3(5.634015780974852, 5.692637977488633, 2.8342643500123743) q[1];
sxdg q[0];
rzz(3.108851319485741) q[0], q[2];
s q[3];
u3(3.0524734507387112, 6.088934910450532, 1.2735385366903773) q[1];
ry(4.642599639119689) q[0];
h q[1];
rx(3.0450872295729883) q[2];
u1(3.1049175131142666) q[1];
r(0.5902669045907668, 4.475257916208899) q[2];
y q[0];
ry(0.5955683968092916) q[3];
cy q[0], q[3];
sx q[2];
sdg q[1];
cp(3.515083891695412) q[0], q[2];
cx q[3], q[1];

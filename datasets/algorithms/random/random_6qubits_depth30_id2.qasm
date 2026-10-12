OPENQASM 3.0;
include "stdgates.inc";
gate cs _gate_q_0, _gate_q_1 {
  t _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  tdg _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
}
gate ecr _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  sx _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  x _gate_q_0;
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
gate rzx(p0) _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  h _gate_q_1;
}
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate cu3(p0, p1, p2) _gate_q_0, _gate_q_1 {
  p(0.5*p2 + 0.5*p1) _gate_q_0;
  p(0.5*p2 - 0.5*p1) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U((-0.5)*p0, 0, (-0.5)*p1 - 0.5*p2) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  U(0.5*p0, p1, 0) _gate_q_1;
}
gate csdg _gate_q_0, _gate_q_1 {
  tdg _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  t _gate_q_1;
  cx _gate_q_0, _gate_q_1;
  tdg _gate_q_1;
}
gate csx _gate_q_0, _gate_q_1 {
  h _gate_q_1;
  cs _gate_q_0, _gate_q_1;
  h _gate_q_1;
}
gate r(p0, p1) _gate_q_0 {
  U(p0, -pi/2 + p1, pi/2 - p1) _gate_q_0;
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
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
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
gate dcx _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
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
gate rzz(p0) _gate_q_0, _gate_q_1 {
  cx _gate_q_0, _gate_q_1;
  rz(p0) _gate_q_1;
  cx _gate_q_0, _gate_q_1;
}
qubit[6] q;
ry(2.0927234246629665) q[2];
sx q[3];
cz q[4], q[0];
cs q[1], q[5];
ecr q[4], q[0];
ecr q[5], q[1];
rxx(2.6289112705137554) q[3], q[2];
ry(3.4734328706112674) q[4];
cry(5.453909696532618) q[3], q[1];
rzx(2.3824536922139483) q[0], q[2];
h q[5];
ch q[2], q[4];
rx(2.3800841468841947) q[3];
sxdg q[0];
x q[1];
id q[5];
rxx(4.826692164717731) q[0], q[4];
cu3(4.109874740557889, 1.3689119156194114, 3.907432254725398) q[5], q[2];
rx(4.901742624846744) q[1];
rx(3.4109452503334623) q[3];
U(3.072077270236812, 3.0666440348047996, 0.9295296136807774) q[3];
u3(0.8242972240049696, 0.6270491465727842, 3.079369541258527) q[5];
h q[2];
tdg q[0];
p(4.5910117918424085) q[4];
rxx(1.1033648827306877) q[2], q[3];
h q[1];
ch q[0], q[4];
p(3.7145317676496448) q[5];
csdg q[5], q[2];
csx q[1], q[4];
crz(3.743120725174662) q[3], q[0];
r(3.517055537904393, 3.168643309697776) q[1];
crx(3.781393289979749) q[0], q[3];
cp(5.705933566503005) q[5], q[4];
z q[2];
tdg q[5];
swap q[1], q[4];
sdg q[2];
ryy(0.6083255994847896) q[0], q[3];
u1(4.382734478787131) q[2];
cp(5.472311746602896) q[5], q[1];
crx(0.3313610753175542) q[0], q[4];
swap q[0], q[4];
tdg q[1];
iswap q[5], q[3];
xx_plus_yy(5.601499208142352, 4.75482865050124) q[4], q[5];
u1(1.8535813014466191) q[1];
ryy(2.502525288349997) q[2], q[0];
h q[3];
cx q[2], q[0];
cu1(6.115913481877058) q[4], q[3];
sxdg q[5];
z q[1];
ryy(4.513591075625816) q[3], q[5];
u3(2.2958949382387956, 1.6231199395146692, 4.852252404060653) q[0];
ry(0.6792638989402603) q[2];
u2(1.9802961323792532, 2.0682469507937338) q[4];
z q[2];
cu1(1.469614626913545) q[3], q[0];
ryy(0.5684464968192751) q[1], q[5];
sx q[4];
tdg q[1];
dcx q[0], q[2];
ryy(0.748940295178921) q[5], q[3];
t q[4];
cu3(3.081696854407921, 0.02167282845231154, 1.9311510033216086) q[2], q[3];
cu1(4.1220149672850654) q[0], q[5];
u3(3.9033287116421445, 6.014168829936147, 2.582848657619137) q[4];
sxdg q[0];
xx_plus_yy(2.7276290138538783, 2.985967297741784) q[3], q[2];
iswap q[5], q[4];
r(1.3665975735024594, 1.3312405524081306) q[5];
cs q[0], q[4];
xx_minus_yy(4.594799161044334, 3.6068444317000714) q[3], q[2];
s q[4];
U(0.5936021287519798, 1.9518568745107674, 5.871354840927889) q[0];
sxdg q[5];
iswap q[3], q[1];
p(4.882574187162309) q[2];
u2(6.125088162886414, 6.187022090948572) q[2];
ecr q[3], q[1];
x q[4];
h q[5];
id q[0];
u3(2.9200787762229448, 0.04420206130608043, 4.168773554720505) q[0];
xx_minus_yy(0.6668486618293397, 3.8337124356553947) q[5], q[4];
sxdg q[3];
sxdg q[2];
s q[1];
rz(3.6830796524390497) q[5];
ry(1.2395634310759365) q[1];
sxdg q[4];
U(0.9359316498187692, 2.4063390016695614, 5.5036163386327095) q[0];
cp(4.484257013008914) q[2], q[3];
tdg q[2];
rxx(1.314370645271568) q[3], q[1];
sxdg q[5];
h q[0];
h q[4];
sxdg q[3];
u2(4.7275035378331465, 0.4837314616059842) q[0];
z q[2];
x q[4];
rzz(4.078087040413921) q[5], q[1];
cry(2.975658325939061) q[4], q[5];
ecr q[3], q[2];
rxx(2.973365728488273) q[1], q[0];
u2(2.2569463686518514, 0.24385136996649237) q[5];
rxx(4.233856457873179) q[1], q[4];
xx_minus_yy(4.888866791120607, 2.051779742471556) q[2], q[0];
sxdg q[3];
ry(2.858607624593681) q[1];
sx q[5];
cry(1.6451413386822973) q[3], q[2];
s q[4];
csx q[0], q[2];
rz(4.361596779674958) q[1];
csx q[3], q[5];

const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('../scripts/pendulum_physics.cjs');
const evolve = (state, duration, dt=P.STEP) => { let s=state.slice(); for(let n=0;n<Math.round(duration/dt);n++)s=P.step(s,dt); return s; };
const norm = (a,b) => Math.hypot(...a.map((x,i)=>x-b[i]));

test('the downward equilibrium remains at rest',()=>{
  assert.deepEqual(evolve([0,0,0,0],2),[0,0,0,0]);
});
test('mirror releases produce mirror trajectories',()=>{
  const a=evolve([1.8,.2,2.1,-.4],3),b=evolve([-1.8,-.2,-2.1,.4],3);
  assert.ok(norm(a,b.map(x=>-x))<1e-11);
});
test('energy stays bounded over a chaotic 30-second trajectory',()=>{
  let s=[2*Math.PI/3,0,2*Math.PI/3,0],e0=P.energy(s),drift=0;
  for(let i=0;i<30/P.STEP;i++){s=P.step(s);drift=Math.max(drift,Math.abs(P.energy(s)-e0)/29.43);}
  assert.ok(drift<1e-5,`normalized energy drift ${drift}`);
});
test('halving the step substantially reduces trajectory error',()=>{
  const s=[1.3,.2,1.7,-.1],reference=evolve(s,1,1/3840);
  const coarse=norm(evolve(s,1,1/120),reference),fine=norm(evolve(s,1,1/240),reference);
  assert.ok(coarse/fine>10,`error improvement ${coarse/fine}`);
});
test('ensemble spread is a total range, not a random perturbation',()=>{
  const a=P.ensemble(128,120,1e-6),b=P.ensemble(128,120,1e-6);
  assert.deepEqual(a,b);assert.equal(a.length,128);
  assert.ok(Math.abs((a.at(-1)[2]-a[0][2])*180/Math.PI-1e-6)<1e-12);
  assert.ok(a.every(s=>s[1]===0&&s[3]===0));
});
test('the pendulum rod lengths are preserved by the angle coordinates',()=>{
  const p=P.positions(evolve([2.1,0,2.1,0],12),.7,1.3);
  assert.ok(Math.abs(Math.hypot(p[0],p[1])-.7)<1e-12);
  assert.ok(Math.abs(Math.hypot(p[2]-p[0],p[3]-p[1])-1.3)<1e-12);
});

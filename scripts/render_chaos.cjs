/* Render real sampled trajectories into script-free, reduced-motion-aware SVGs. */
const fs = require('node:fs');
const path = require('node:path');
const P = require('./pendulum_physics.cjs');
const assets = path.resolve(__dirname,'../assets');
const FRAMES=200,DURATION=24,START=8;
const point=(x,y)=>`${x.toFixed(3)},${y.toFixed(3)}`;
function smooth(points){
  let d='M'+point(...points[0]);
  for(let i=0;i<points.length-1;i++){
    const a=points[Math.max(0,i-1)],b=points[i],c=points[i+1],e=points[Math.min(points.length-1,i+2)];
    d+='C'+point(b[0]+(c[0]-a[0])/6,b[1]+(c[1]-a[1])/6)+' '+point(c[0]-(e[0]-b[0])/6,c[1]-(e[1]-b[1])/6)+' '+point(...c);
  }
  return d;
}
function model(degrees,count){
  let states=P.ensemble(count,degrees,1e-6),time=0;
  const samples=Array.from({length:count},()=>[]);
  for(let frame=0;frame<FRAMES;frame++){
    const target=START+frame/(FRAMES-1)*DURATION;
    while(time<target-P.STEP/2){states=states.map(s=>P.step(s));time+=P.STEP;}
    states.forEach((s,i)=>samples[i].push(P.positions(s)));
  }
  return samples;
}
function art(samples){
  let style='.chaos-loop{animation:chaos-loop 24s linear infinite}@keyframes chaos-loop{0%,100%{opacity:0}3%,96%{opacity:1}}';
  let drawing='<circle cx="0" cy="0" r="2.1" fill="none" stroke="#51627c" stroke-width=".007" stroke-dasharray=".02 .07" opacity=".45"/>';
  const tail=(sample,f)=>smooth(Array.from({length:9},(_,n)=>{const p=sample[Math.max(0,f-8+n)];return [p[2],p[3]];}));
  const arm=p=>'M0,0L'+point(p[0],p[1])+'L'+point(p[2],p[3]);
  samples.forEach((sample,i)=>{
    const color=`hsl(${165+i/Math.max(1,samples.length-1)*300} 85% 72%)`;
    style+=`.pendulum-${i}{animation:pendulum-${i} ${DURATION}s linear infinite}.tail-${i}{animation:tail-${i} ${DURATION}s linear infinite}`;
    style+=`@keyframes pendulum-${i}{`+sample.map((p,f)=>`${(100*f/(FRAMES-1)).toFixed(3)}%{d:path("${arm(p)}")}`).join('')+'}';
    style+=`@keyframes tail-${i}{`+sample.map((p,f)=>`${(100*f/(FRAMES-1)).toFixed(3)}%{d:path("${tail(sample,f)}")}`).join('')+'}';
    const representative=Math.floor(FRAMES*.65);
    drawing+=`<path d="${smooth(sample.map(p=>[p[2],p[3]]))}" fill="none" stroke="${color}" stroke-width=".006" opacity=".045"/>`;
    drawing+=`<path class="anim tail-${i}" d="${tail(sample,representative)}" fill="none" stroke="${color}" stroke-width=".055" stroke-linecap="round" opacity=".3" filter="url(#chaosGlow)"/>`;
    drawing+=`<path class="anim tail-${i}" d="${tail(sample,representative)}" fill="none" stroke="${color}" stroke-width=".024" stroke-linecap="round" stroke-linejoin="round" opacity=".65" style="mix-blend-mode:screen"/>`;
    drawing+=`<path class="anim pendulum-${i}" d="${arm(sample[representative])}" fill="none" stroke="${color}" stroke-width=".011" stroke-linecap="round" stroke-linejoin="round" opacity=".35" style="mix-blend-mode:screen"/>`;
  });
  style+='@media(prefers-reduced-motion:reduce){.chaos-loop,.chaos-loop .anim{animation:none!important}}';
  return `<defs><filter id="chaosGlow" filterUnits="userSpaceOnUse" x="-3" y="-3" width="6" height="6"><feGaussianBlur stdDeviation=".025"/></filter></defs><style>${style}</style><g class="chaos-loop">${drawing}<circle cx="0" cy="0" r=".025" fill="#edf5f1"/></g>`;
}
for(const [name,degrees,count] of [['chaos',120,12]]){
  const content=art(model(degrees,count));
  for(const suffix of ['','-mobile']){
    const file=path.join(assets,name+suffix+'.svg');
    const shell=fs.readFileSync(file,'utf8');
    if(!shell.includes('<!-- PENDULUM_ART -->'))throw new Error('Expected freshly generated SVG shell');
    fs.writeFileSync(file,shell.replace('<!-- PENDULUM_ART -->',content));
  }
}

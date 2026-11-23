/* Arden — introduzione indipendente. Nessuna modifica alla porta Enterprise. */
(()=>{
'use strict';
const MESSAGE="Benvenuti nella Dashboard del sito Nowcasting Italia. Sono Arden. Vi cedo il comando. Siete autorizzati. Il mio equipaggio vi fornirà le informazioni sul funzionamento degli strumenti.";
const style=document.createElement('style');
style.textContent=`
#ardenIntro{position:fixed;inset:0;z-index:1000;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;overflow:hidden;background:radial-gradient(ellipse at 50% 45%,#0b3663,#020a1b 80%);color:#eaffff;font-family:system-ui,Arial,sans-serif;isolation:isolate}
#ardenIntro .ardenPortrait{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center center;filter:drop-shadow(0 0 18px #0cf);z-index:1}
#ardenIntro .ardenBeam{position:absolute;inset:0;width:100%;height:100%;z-index:2;pointer-events:none}
#ardenIntro .ardenBubble{position:relative;z-index:3;width:min(92vw,540px);min-height:116px;margin:0 auto max(5dvh,18px);padding:16px 18px 19px;border:2px solid #60e9ff;border-radius:20px;background:rgba(1,13,32,.95);box-shadow:0 0 24px #00cfffaa;color:#f1ffff;font-size:clamp(15px,3.8vw,20px);line-height:1.45;font-weight:650}
#ardenIntro .ardenCursor{display:inline-block;color:#61efff;animation:ardenBlink .6s steps(1) infinite}
#ardenIntro .ardenSkip{position:absolute;right:12px;top:max(12px,env(safe-area-inset-top));z-index:5;padding:10px 14px;background:#062447;color:#fff;border:1px solid #66eaff;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer}
#ardenIntro .ardenPortrait{animation:ardenArrive 1.25s ease-out both}
#ardenIntro.departing .ardenPortrait{animation:ardenLeave 1.25s ease-in forwards}
#ardenIntro.departing .ardenBubble{opacity:0;transition:opacity .5s}
@keyframes ardenArrive{0%{opacity:0;clip-path:inset(100% 0 0);filter:brightness(4) blur(12px)}40%{opacity:.8;filter:brightness(2.5) blur(3px)}100%{opacity:1;clip-path:inset(0);filter:drop-shadow(0 0 18px #0cf)}}
@keyframes ardenLeave{0%{opacity:1;clip-path:inset(0)}45%{opacity:.95;filter:brightness(3) blur(2px)}100%{opacity:0;clip-path:inset(0 0 100%);filter:brightness(5) blur(10px)}}
@keyframes ardenBlink{50%{opacity:0}}
@media(min-width:700px){#ardenIntro .ardenPortrait{height:100%;max-width:680px;left:50%;transform:translateX(-50%)}#ardenIntro .ardenBubble{margin-bottom:3vh}}
@media(prefers-reduced-motion:reduce){#ardenIntro .ardenPortrait,#ardenIntro .ardenCursor{animation:none!important}}
`;
document.head.appendChild(style);
const el=document.createElement('section');
el.id='ardenIntro';el.setAttribute('role','dialog');el.setAttribute('aria-label','Benvenuto del capitano Arden');
el.innerHTML='<img class="ardenPortrait" src="arden.png" alt="Capitano Arden, Nowcasting Italia"><canvas class="ardenBeam" aria-hidden="true"></canvas><button class="ardenSkip" type="button">SALTA INTRO ▶</button><div class="ardenBubble" aria-live="polite"><span class="ardenTyped"></span><span class="ardenCursor" aria-hidden="true">▌</span></div>';
document.body.appendChild(el);
const portrait=el.querySelector('img'),canvas=el.querySelector('canvas'),typed=el.querySelector('.ardenTyped'),cursor=el.querySelector('.ardenCursor');
let frame=0,timer=0,closing=false;
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
function finish(){if(closing)return;closing=true;clearTimeout(timer);cancelAnimationFrame(frame);el.remove();}
el.querySelector('button').addEventListener('click',finish);
portrait.addEventListener('error',()=>{typed.textContent=MESSAGE;cursor.remove();});
function particles(entering){
 if(reduced)return;
 cancelAnimationFrame(frame);
 const rect=canvas.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,2),w=canvas.width=Math.max(1,Math.round(rect.width*ratio)),h=canvas.height=Math.max(1,Math.round(rect.height*ratio)),ctx=canvas.getContext('2d');
 if(!ctx)return;
 const left=w*.22,right=w*.78,top=h*.08,bottom=h*.87;
 const dots=Array.from({length:innerWidth<700?90:190},()=>({x:left+Math.random()*(right-left),y:top+Math.random()*(bottom-top),vx:(Math.random()-.5)*w*.12,vy:(Math.random()-.5)*h*.24,r:(.6+Math.random()*2.5)*ratio}));
 const start=performance.now();
 function draw(now){
  if(!el.isConnected)return;
  const p=Math.min(1,(now-start)/1250),d=entering?1-p:p,a=entering?Math.max(0,1-p*.85):Math.max(0,1-p);
  ctx.clearRect(0,0,w,h);ctx.save();ctx.globalCompositeOperation='lighter';
  for(const q of dots){ctx.fillStyle='rgba(95,238,255,'+a+')';ctx.shadowColor='#00cfff';ctx.shadowBlur=12*ratio;ctx.fillRect(q.x+q.vx*d,q.y+q.vy*d,q.r,q.r*3);}
  const bx=(left+right)/2,g=ctx.createLinearGradient(bx-35*ratio,0,bx+35*ratio,0);
  g.addColorStop(0,'rgba(0,160,255,0)');g.addColorStop(.5,'rgba(90,235,255,'+(Math.sin(Math.PI*p)*.35)+')');g.addColorStop(1,'rgba(0,160,255,0)');
  ctx.fillStyle=g;ctx.fillRect(bx-35*ratio,top,70*ratio,bottom-top);ctx.restore();
  if(p<1)frame=requestAnimationFrame(draw);else ctx.clearRect(0,0,w,h);
 }
 frame=requestAnimationFrame(draw);
}
particles(true);
let index=0;
function type(){
 if(closing)return;
 if(index<MESSAGE.length){typed.textContent=MESSAGE.slice(0,++index);timer=setTimeout(type,40);return;}
 cursor.style.visibility='hidden';
 timer=setTimeout(()=>{
  if(closing)return;
  el.classList.add('departing');particles(false);
  timer=setTimeout(finish,reduced?100:1350);
 },1800);
}
timer=setTimeout(type,reduced?100:1500);
window.addEventListener('pagehide',finish,{once:true});
})();

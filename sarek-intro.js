/* Sarek: introduzione autonoma per S.I.B.I.L.L.A.; nessun intervento sui tracker. */
(()=>{
'use strict';
const MESSAGE='Salve, sono Sarek, ufficiale scientifico. Qui abbiamo diverse risorse sperimentali per il nowcasting. E ricordate: la bomba d’acqua non esiste. È illogica.';
const style=document.createElement('style');
style.textContent=`
#sarekIntro{position:fixed;inset:0;z-index:2147483641;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;overflow:hidden;background:radial-gradient(ellipse at 50% 45%,#0b3663,#020a1b 80%);color:#eaffff;font-family:system-ui,Arial,sans-serif;isolation:isolate}
#sarekIntro .sarekPortrait{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 0 18px #0cf);z-index:1;animation:sarekArrive 1.25s ease-out both}
#sarekIntro .sarekBeam{position:absolute;inset:0;width:100%;height:100%;z-index:2;pointer-events:none}
#sarekIntro .sarekBubble{position:relative;z-index:3;width:min(92vw,540px);min-height:116px;margin:0 auto max(5dvh,18px);padding:16px 18px 19px;border:2px solid #60e9ff;border-radius:20px;background:rgba(1,13,32,.95);box-shadow:0 0 24px #00cfffaa;font-size:clamp(15px,3.8vw,20px);line-height:1.45;font-weight:650}
#sarekIntro .sarekListen,#sarekIntro .sarekSkip{position:absolute;top:max(12px,env(safe-area-inset-top));z-index:5;padding:10px 12px;border:1px solid #66eaff;border-radius:10px;color:#fff;background:#062447;font-size:14px;font-weight:700;cursor:pointer}
#sarekIntro .sarekListen{left:12px}#sarekIntro .sarekSkip{right:12px}
#sarekIntro .sarekCursor{color:#61efff;animation:sarekBlink .6s steps(1) infinite}
#sarekIntro.departing .sarekPortrait{animation:sarekLeave 1.25s ease-in forwards}
#sarekIntro.departing .sarekBubble{opacity:0;transition:opacity .5s}
@keyframes sarekArrive{0%{opacity:0;clip-path:inset(100% 0 0);filter:brightness(4) blur(12px)}40%{opacity:.8;filter:brightness(2.5) blur(3px)}100%{opacity:1;clip-path:inset(0);filter:drop-shadow(0 0 18px #0cf)}}
@keyframes sarekLeave{0%{opacity:1;clip-path:inset(0)}45%{opacity:.95;filter:brightness(3) blur(2px)}100%{opacity:0;clip-path:inset(0 0 100%);filter:brightness(5) blur(10px)}}
@keyframes sarekBlink{50%{opacity:0}}
@media(min-width:700px){#sarekIntro .sarekPortrait{max-width:680px;left:50%;transform:translateX(-50%)}}
@media(prefers-reduced-motion:reduce){#sarekIntro .sarekPortrait,#sarekIntro .sarekCursor{animation:none!important}}
`;
document.head.appendChild(style);
let closeActive=()=>{};
window.showSarekWelcome=function(){
 closeActive();
 const el=document.createElement('section');el.id='sarekIntro';el.setAttribute('role','dialog');el.setAttribute('aria-label','Sarek, ufficiale scientifico');
 el.innerHTML='<img class="sarekPortrait" src="sarek.png" alt="Sarek, ufficiale scientifico"><canvas class="sarekBeam" aria-hidden="true"></canvas><button class="sarekListen" type="button">▶ ASCOLTA SAREK</button><button class="sarekSkip" type="button">SALTA INTRO ▶</button><div class="sarekBubble"><span class="sarekTyped"></span><span class="sarekCursor" aria-hidden="true">▌</span></div>';
 document.body.appendChild(el);
 const voice=new Audio('sarek-voice.mp3');voice.preload='none';
 const typed=el.querySelector('.sarekTyped'),listen=el.querySelector('.sarekListen');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 let timer=0,frame=0,closed=false,started=false,typingDone=false,audioDone=false,departing=false;
 function maybeDepart(){if(typingDone&&audioDone&&!departing&&!closed){departing=true;timer=setTimeout(depart,850);}}
 function close(){if(closed)return;closed=true;clearTimeout(timer);cancelAnimationFrame(frame);voice.pause();voice.removeAttribute('src');el.remove();if(closeActive===close)closeActive=()=>{};}
 closeActive=close;
 el.querySelector('.sarekSkip').addEventListener('click',close);
 const canvas=el.querySelector('.sarekBeam');
 function particles(entering){
  if(reduced)return;
  cancelAnimationFrame(frame);
  const rect=canvas.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,2),w=canvas.width=Math.max(1,Math.round(rect.width*ratio)),h=canvas.height=Math.max(1,Math.round(rect.height*ratio)),ctx=canvas.getContext('2d');
  if(!ctx)return;
  const dots=Array.from({length:innerWidth<700?90:190},()=>({x:w*(.22+Math.random()*.56),y:h*(.08+Math.random()*.79),vx:(Math.random()-.5)*w*.12,vy:(Math.random()-.5)*h*.24,r:(.6+Math.random()*2.5)*ratio}));
  const start=performance.now();
  function draw(now){
   if(closed)return;
   const p=Math.min(1,(now-start)/1250),d=entering?1-p:p,a=entering?1-p*.85:1-p;
   ctx.clearRect(0,0,w,h);ctx.save();ctx.globalCompositeOperation='lighter';ctx.fillStyle='rgba(95,238,255,'+a+')';ctx.shadowColor='#00cfff';ctx.shadowBlur=12*ratio;
   for(const q of dots)ctx.fillRect(q.x+q.vx*d,q.y+q.vy*d,q.r,q.r*3);
   ctx.restore();
   if(p<1)frame=requestAnimationFrame(draw);
  }
  frame=requestAnimationFrame(draw);
 }
 function depart(){if(closed)return;el.classList.add('departing');particles(false);timer=setTimeout(close,reduced?100:1350);}
 function type(i=0){
  if(closed)return;
  if(i<MESSAGE.length){typed.textContent=MESSAGE.slice(0,i+1);timer=setTimeout(()=>type(i+1),55);return;}
  el.querySelector('.sarekCursor').style.visibility='hidden';
  typingDone=true;maybeDepart();
 }
 listen.addEventListener('click',()=>{
  if(started||closed)return;
  started=true;listen.remove();
  voice.addEventListener('ended',()=>{audioDone=true;maybeDepart();},{once:true});
  voice.addEventListener('error',()=>{audioDone=true;maybeDepart();},{once:true});
  voice.play().catch(()=>{audioDone=true;maybeDepart();});
  type();
 });
 el.querySelector('.sarekPortrait').addEventListener('error',()=>{el.querySelector('.sarekPortrait').style.display='none';});
 particles(true);
 timer=setTimeout(()=>{if(!started)depart();},30000);
};
window.closeSarekWelcome=()=>closeActive();
})();

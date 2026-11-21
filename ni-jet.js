/* N.I. SINOTTICA: continuous 250 hPa jet ribbons from NOAA GFS U/V.
   Canvas rendering only; no synthetic meteorological input. */
(function(){
'use strict';
const canvas=document.createElement('canvas');
canvas.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:450';
document.getElementById('map').appendChild(canvas);
const ctx=canvas.getContext('2d',{alpha:true});
let ribbon=null,wind=null,last=0,phase=0,cacheKey='',paused=false,streamlines=[];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const mix=(a,b,t)=>a+(b-a)*t;
function interp(w,lat,lon){
 if(!w||!w.lat||!w.lon||!w.u||!w.v||w.lat.length<2||w.lon.length<2)return null;
 const la=w.lat,lo=w.lon,dy=la[1]-la[0],dx=lo[1]-lo[0];
 const y=(lat-la[0])/dy,x=(lon-lo[0])/dx;
 if(x<0||y<0||x>=lo.length-1||y>=la.length-1)return null;
 const i=Math.floor(y),j=Math.floor(x),a=x-j,b=y-i;
 const u00=w.u[i]?.[j],u10=w.u[i]?.[j+1],u01=w.u[i+1]?.[j],u11=w.u[i+1]?.[j+1];
 const v00=w.v[i]?.[j],v10=w.v[i]?.[j+1],v01=w.v[i+1]?.[j],v11=w.v[i+1]?.[j+1];
 if(![u00,u10,u01,u11,v00,v10,v01,v11].every(Number.isFinite))return null;
 return [mix(mix(u00,u10,a),mix(u01,u11,a),b),mix(mix(v00,v10,a),mix(v01,v11,a),b)];
}
function velocity(x,y){
 const ll=map.containerPointToLatLng([x,y]),v=interp(wind,ll.lat,ll.lng);
 if(!v)return null;
 const speed=Math.hypot(v[0],v[1])*3.6;
 const scale=clamp(Math.cos(ll.lat*Math.PI/180),.24,1);
 const dx=v[0]/scale,dy=-v[1],norm=Math.hypot(dx,dy);
 return norm>0?[dx/norm,dy/norm,speed]:null;
}
function color(speed){
 const stops=[[80,[15,38,105]],[110,[12,80,215]],[145,[0,185,246]],
 [180,[36,220,155]],[215,[243,224,40]],[255,[255,126,28]],[300,[244,38,44]]];
 let a=stops[0],b=stops[stops.length-1];
 for(let i=1;i<stops.length;i++)if(speed<stops[i][0]){a=stops[i-1];b=stops[i];break}
 const t=clamp((speed-a[0])/(b[0]-a[0]),0,1);
 return a[1].map((v,i)=>Math.round(mix(v,b[1][i],t)));
}
function raster(){
 const sz=map.getSize(),step=5,w=Math.ceil(sz.x/step),h=Math.ceil(sz.y/step);
 const off=document.createElement('canvas');off.width=w;off.height=h;
 const c=off.getContext('2d'),im=c.createImageData(w,h);
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const v=velocity(x*step,y*step),i=(y*w+x)*4;
  if(!v||v[2]<85)continue;
  const rgb=color(v[2]),alpha=clamp((v[2]-85)/35,0,.58);
  im.data[i]=rgb[0];im.data[i+1]=rgb[1];im.data[i+2]=rgb[2];im.data[i+3]=Math.round(alpha*255);
 }
 c.putImageData(im,0,0);return off;
}
function buildStreamlines(){
 const sz=map.getSize(),out=[],spacing=48;
 for(let yy=0;yy<sz.y;yy+=spacing)for(let xx=0;xx<sz.x;xx+=spacing){
  let x=xx,y=yy,pts=[],maxSpeed=0;
  for(let n=0;n<65;n++){
   const v=velocity(x,y);if(!v||v[2]<110)break;
   pts.push([x,y]);maxSpeed=Math.max(maxSpeed,v[2]);
   x+=v[0]*3.5;y+=v[1]*3.5;
   if(x<0||y<0||x>sz.x||y>sz.y)break;
  }
  if(pts.length>=14)out.push({pts,speed:maxSpeed,offset:out.length*13});
 }
 return out;
}
function resize(){const sz=map.getSize(),d=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(sz.x*d);canvas.height=Math.round(sz.y*d);canvas.style.width=sz.x+'px';canvas.style.height=sz.y+'px';ctx.setTransform(d,0,0,d,0,0);cacheKey=''}
function animate(t){
 requestAnimationFrame(animate);
 const frame=frames[index],active=frame&&document.getElementById('jet').checked&&map.hasLayer(groups.jet)&&frame.wind_vectors;
 const sz=map.getSize();ctx.clearRect(0,0,sz.x,sz.y);
 if(!active){wind=null;last=t;return}
 const key=frame.valid_utc+':'+map.getZoom()+':'+map.getCenter().toString()+':'+sz.x+':'+sz.y;
 if(key!==cacheKey){wind=frame.wind_vectors;ribbon=raster();streamlines=buildStreamlines();cacheKey=key}
 if(ribbon){ctx.imageSmoothingEnabled=true;ctx.drawImage(ribbon,0,0,sz.x,sz.y)}
 const dt=clamp((t-last)/1000,0,.05);last=t;if(!paused)phase+=dt*7;
 // Streamline geometry is stable: only a broad, continuous luminous wave travels.
 // The forecast Play/Pause changes forecast time, NOT the wind-flow animation.
 ctx.lineCap='round';ctx.lineJoin='round';
 for(const line of streamlines){
  const pts=line.pts,n=pts.length;
  const wave=(phase*.85+line.offset)%n;
  for(let i=1;i<n;i++){
   const dist=Math.abs(i-wave),wrapped=Math.min(dist,n-dist);
   const glow=Math.exp(-(wrapped*wrapped)/(2*10*10));
   ctx.strokeStyle='rgba(240,252,255,'+(0.035+0.25*glow).toFixed(3)+')';
   ctx.lineWidth=0.8+0.6*glow;
   ctx.beginPath();ctx.moveTo(pts[i-1][0],pts[i-1][1]);ctx.lineTo(pts[i][0],pts[i][1]);ctx.stroke();
  }
 }
}
map.on('zoomend moveend resize',resize);
resize();requestAnimationFrame(animate);
window.niJetPause=flag=>{paused=!!flag};
})();

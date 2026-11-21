/* N.I. SINOTTICA: continuous 250 hPa jet ribbons from NOAA GFS U/V.
   Canvas rendering only; no synthetic meteorological input. */
(function(){
'use strict';
const canvas=document.createElement('canvas');
canvas.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:450';
document.getElementById('map').appendChild(canvas);
const ctx=canvas.getContext('2d',{alpha:true});
let wind=null,last=0,phase=0,cacheKey='',paused=false;
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
function resize(){
 const sz=map.getSize(),d=Math.min(devicePixelRatio||1,2);
 canvas.width=Math.round(sz.x*d);canvas.height=Math.round(sz.y*d);
 canvas.style.width=sz.x+'px';canvas.style.height=sz.y+'px';
 ctx.setTransform(d,0,0,d,0,0);cacheKey='';
}
let pixels=null,off=null,offctx=null,field=null,lastDraw=0;
function prepare(){
 const sz=map.getSize(),step=6,w=Math.ceil(sz.x/step),h=Math.ceil(sz.y/step);
 off=document.createElement('canvas');off.width=w;off.height=h;
 offctx=off.getContext('2d');pixels=offctx.createImageData(w,h);
 field=new Float32Array(w*h*5);
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const v=velocity(x*step,y*step),i=(y*w+x)*5;
  if(!v||v[2]<85)continue;
  const ll=map.containerPointToLatLng([x*step,y*step]);
  const uv=interp(wind,ll.lat,ll.lng);
  if(!uv)continue;
  field[i]=v[2];field[i+1]=uv[0];field[i+2]=uv[1];
  field[i+3]=ll.lng;field[i+4]=ll.lat;
 }
}
function animate(t){
 requestAnimationFrame(animate);
 if(t-lastDraw<65)return;
 const dt=last?clamp((t-last)/1000,0,.15):0;last=t;lastDraw=t;
 const frame=frames[index];
 const active=frame&&document.getElementById('jet').checked&&map.hasLayer(groups.jet)&&frame.wind_vectors;
 const sz=map.getSize();
 if(!active){ctx.clearRect(0,0,sz.x,sz.y);wind=null;return}
 const key=frame.valid_utc+':'+map.getZoom()+':'+map.getCenter().toString()+':'+sz.x+':'+sz.y;
 if(key!==cacheKey){wind=frame.wind_vectors;prepare();cacheKey=key}
 if(!paused)phase+=dt;
 const w=off.width,h=off.height,data=pixels.data;
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const j=y*w+x,i=j*5,k=j*4,spd=field[i];
  if(!spd){data[k+3]=0;continue}
  const u=field[i+1],v=field[i+2],lon=field[i+3],lat=field[i+4];
  // Advect the colored texture backwards along the actual GFS wind vector.
  // Positive zonal wind U moves the pattern eastward; V moves it northward.
  const adv=phase*0.018;
  const ax=lon-u*adv/Math.max(.25,Math.cos(lat*Math.PI/180));
  const ay=lat-v*adv;
  const texture=Math.sin(ax*2.4+Math.sin(ay*1.7))*Math.sin(ay*3.1-ax*.9);
  const shimmer=.83+.17*texture;
  const rgb=color(spd);
  data[k]=Math.round(rgb[0]*shimmer);
  data[k+1]=Math.round(rgb[1]*shimmer);
  data[k+2]=Math.round(rgb[2]*shimmer);
  data[k+3]=Math.round(255*clamp((spd-85)/35,0,.58)*(.83+.17*texture));
 }
 offctx.putImageData(pixels,0,0);
 ctx.clearRect(0,0,sz.x,sz.y);
 ctx.imageSmoothingEnabled=true;
 ctx.drawImage(off,0,0,sz.x,sz.y);
}
map.on('zoomend moveend resize',resize);
resize();requestAnimationFrame(animate);
window.niJetPause=flag=>{paused=!!flag};
})();

/* N.I. SINOTTICA — 250 hPa continuous semi-Lagrangian texture advection.
   Velocity is interpolated from NOAA GFS U/V; no particles or moving strokes. */
(function(){
'use strict';
const canvas=document.createElement('canvas');
canvas.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:450';
document.getElementById('map').appendChild(canvas);
const gl=canvas.getContext('webgl2',{alpha:true,antialias:false,preserveDrawingBuffer:false});
if(!gl){console.warn('N.I. Jet: WebGL2 unavailable');return}
const vert=`#version 300 es
in vec2 position;
out vec2 uv;
void main(){uv=(position+1.0)*0.5;gl_Position=vec4(position,0.,1.);}`;
const advFrag=`#version 300 es
precision highp float;
in vec2 uv;out vec4 result;
uniform sampler2D prevTex;
uniform sampler2D flowTex;
uniform float dt;
uniform float injection;
uniform float tick;
vec2 vel(vec2 p){return (texture(flowTex,clamp(p,0.,1.)).rg*255.-128.)/4000.;}
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
 vec2 v1=vel(uv);
 vec2 mid=uv-0.5*dt*v1;
 vec2 v2=vel(mid);
 vec2 back=uv-dt*v2;
 float old=texture(prevTex,clamp(back,0.,1.)).r;
 float noise=old;
 result=vec4(noise,0.,0.,1.);
}`;
const drawFrag=`#version 300 es
precision highp float;
in vec2 uv;out vec4 result;
uniform sampler2D advTex;
uniform sampler2D flowTex;
vec3 palette(float s){
 vec3 a=vec3(.06,.15,.41),b=vec3(.05,.32,.84),c=vec3(0.,.72,.96);
 vec3 d=vec3(.14,.86,.61),e=vec3(.95,.88,.16),f=vec3(1.,.49,.11),g=vec3(.96,.15,.17);
 if(s<110.)return mix(a,b,clamp((s-80.)/30.,0.,1.));
 if(s<145.)return mix(b,c,(s-110.)/35.);
 if(s<180.)return mix(c,d,(s-145.)/35.);
 if(s<215.)return mix(d,e,(s-180.)/35.);
 if(s<255.)return mix(e,f,(s-215.)/40.);
 return mix(f,g,clamp((s-255.)/45.,0.,1.));
}
void main(){
 float speed=texture(flowTex,uv).b*320.;
 if(speed<85.){result=vec4(0.);return;}
 float n=texture(advTex,uv).r;
 // Texture contrast is deliberately broad and continuous, never discrete streaks.
 float variation=.91+.09*smoothstep(.18,.82,n);
 float opacity=clamp((speed-85.)/35.,0.,.53)*variation;
 result=vec4(palette(speed)*variation,opacity);
}`;
function program(fs){
 const compile=(type,src)=>{let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s};
 const p=gl.createProgram();gl.attachShader(p,compile(gl.VERTEX_SHADER,vert));gl.attachShader(p,compile(gl.FRAGMENT_SHADER,fs));gl.linkProgram(p);
 if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));
 return p;
}
const adv=program(advFrag),draw=program(drawFrag);
const vao=gl.createVertexArray();gl.bindVertexArray(vao);
const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
for(const p of [adv,draw]){const a=gl.getAttribLocation(p,'position');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0)}
function tex(w,h,data,filter=gl.LINEAR){
 const t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,filter);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,filter);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
 gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
 gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,data);return t;
}
const fbo=gl.createFramebuffer();
let flow=null,states=[],size=[0,0],cache='',last=0,step=0;
function bilinear(w,lat,lon){
 const la=w.lat,lo=w.lon;if(!la||!lo||la.length<2||lo.length<2)return null;
 const x=(lon-lo[0])/(lo[1]-lo[0]),y=(lat-la[0])/(la[1]-la[0]);
 if(x<0||y<0||x>=lo.length-1||y>=la.length-1)return null;
 const i=Math.floor(y),j=Math.floor(x),a=x-j,b=y-i;
 const vals=[w.u[i]?.[j],w.u[i]?.[j+1],w.u[i+1]?.[j],w.u[i+1]?.[j+1],w.v[i]?.[j],w.v[i]?.[j+1],w.v[i+1]?.[j],w.v[i+1]?.[j+1]];
 if(!vals.every(Number.isFinite))return null;
 const lerp=(p,q,t)=>p+(q-p)*t;
 return [lerp(lerp(vals[0],vals[1],a),lerp(vals[2],vals[3],a),b),lerp(lerp(vals[4],vals[5],a),lerp(vals[6],vals[7],a),b)];
}
function reset(wind){
 const sz=map.getSize(),w=Math.max(1,Math.ceil(sz.x/3)),h=Math.max(1,Math.ceil(sz.y/3));
 size=[w,h];canvas.width=sz.x;canvas.height=sz.y;canvas.style.width=sz.x+'px';canvas.style.height=sz.y+'px';
 const field=new Uint8Array(w*h*4),initial=new Uint8Array(w*h*4);
 // Y in texture is bottom-to-top, unlike Leaflet container pixels.
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const px=(x+.5)*sz.x/w,py=sz.y-(y+.5)*sz.y/h;
  const ll=map.containerPointToLatLng([px,py]),uv=bilinear(wind,ll.lat,ll.lng);
  const i=(y*w+x)*4;
  // Smooth, spatially coherent scalar field; no random pixel noise/ripples.
  const nx=x/w,ny=y/h;
  const seed=.5+.23*Math.sin(nx*17.0+ny*8.0)+.17*Math.sin(nx*9.0-ny*13.0);
  initial[i]=Math.round(Math.max(0,Math.min(255,seed*255)));initial[i+3]=255;
  if(!uv)continue;
  const speed=Math.hypot(...uv)*3.6;
  // Pixel displacement in mercator: positive U -> right, positive V -> up.
  const merc=256*Math.pow(2,map.getZoom())/(2*Math.PI*6371000);
  const east=uv[0]*merc*sz.x/w;
  const north=uv[1]*merc*sz.y/h/Math.max(.15,Math.cos(ll.lat*Math.PI/180));
  // 128 denotes zero velocity, signed components encoded in RG.
  // 0.0025 scales real wind displacement into perceptible animation time.
  field[i]=Math.round(Math.max(0,Math.min(255,128+east*4000)));
  field[i+1]=Math.round(Math.max(0,Math.min(255,128+north*4000)));
  field[i+2]=Math.round(Math.min(255,speed/320*255));field[i+3]=255;
 }
 if(flow)gl.deleteTexture(flow);for(const t of states)gl.deleteTexture(t);
 flow=tex(w,h,field);states=[tex(w,h,initial),tex(w,h,initial)];
 step=0;
}
function bind(t,unit){gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,t)}
function uniform(p,name,val){gl.uniform1f(gl.getUniformLocation(p,name),val)}
function animate(t){
 requestAnimationFrame(animate);
 if(t-last<45)return;
 const dt=last?Math.min((t-last)/1000,.12):0;last=t;
 const frame=frames[index],sz=map.getSize();
 const active=frame?.wind_vectors&&document.getElementById('jet').checked&&map.hasLayer(groups.jet);
 if(!active){gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);return}
 const key=frame.valid_utc+':'+map.getZoom()+':'+map.getCenter().toString()+':'+sz.x+':'+sz.y;
 if(key!==cache){reset(frame.wind_vectors);cache=key}
 const [w,h]=size;gl.viewport(0,0,w,h);
 gl.useProgram(adv);bind(states[step%2],0);bind(flow,1);
 gl.uniform1i(gl.getUniformLocation(adv,'prevTex'),0);
 gl.uniform1i(gl.getUniformLocation(adv,'flowTex'),1);
 // Signed velocity stored around 128/255; decode in shader.
 uniform(adv,'dt',dt);uniform(adv,'injection',.008);uniform(adv,'tick',t*.001);
 gl.bindFramebuffer(gl.FRAMEBUFFER,fbo);
 gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,states[(step+1)%2],0);
 gl.drawArrays(gl.TRIANGLE_STRIP,0,4);step++;
 gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,0,canvas.width,canvas.height);
 gl.useProgram(draw);bind(states[step%2],0);bind(flow,1);
 gl.uniform1i(gl.getUniformLocation(draw,'advTex'),0);
 gl.uniform1i(gl.getUniformLocation(draw,'flowTex'),1);
 gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);
 gl.drawArrays(gl.TRIANGLE_STRIP,0,4);gl.disable(gl.BLEND);
}
map.on('zoomend moveend resize',()=>{cache=''});
// Switching the satellite must not retain an old advected texture.
const satelliteToggle=document.getElementById('satellite');
if(satelliteToggle)satelliteToggle.addEventListener('change',()=>{cache=''});
requestAnimationFrame(animate);
})();
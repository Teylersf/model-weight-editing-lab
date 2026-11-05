"use strict";
const byId = id => document.getElementById(id);
const runs = byId("runs"), pause = byId("pause"), range = byId("range");
const svg = byId("pace"), chart = byId("chart"), tip = byId("trace-tip");
const select = byId("weight-select"), canvas = byId("heatmap");
const NS = "http://www.w3.org/2000/svg";
const colors = ["#ff77a8","#ffac73","#ffe084","#7cf5a8","#62eafa","#879dff","#d9a4ff"];
const number = new Intl.NumberFormat(undefined,{maximumFractionDigits:1});
let snapshot, windowSize = 0, chartKey = "", eventKey = "", weightsKey = "";
let scale, plotted = [], marker, cursor, hover = -1;
let paused = false, timer, liveController, weightController, heat;
const heatCache = new Map();

function node(name, attrs, label) {
  const element = document.createElementNS(NS,name);
  for (const [key,value] of Object.entries(attrs)) element.setAttribute(key,value);
  if (label !== undefined) element.textContent = label;
  return element;
}
function human(value) { return String(value || "Waiting").replaceAll("_"," "); }
function fmt(value) { return Number.isFinite(value) ? number.format(value) : "—"; }
function value(id,text) { const item=byId(id); if(item.textContent!==text) item.textContent=text; }
function updateOptions(element, options) {
  const signature=JSON.stringify(options);
  if(element.dataset.choices===signature) return;
  const current=element.value;
  element.replaceChildren(...options.map(([label,id]) => new Option(label,id)));
  if(options.some(([,id]) => id===current)) element.value=current;
  element.dataset.choices=signature;
}
function tone(status) {
  if (status==="Watching") return "active";
  if (/cap|stop|error|unavailable/i.test(status)) return "warning";
  return "neutral";
}
function status(text,type=tone(text)) {
  value("status",text);
  byId("status").dataset.tone=type;
}
function geometry() {
  const rect=svg.getBoundingClientRect();
  const w=Math.max(230,Math.round(rect.width)),h=Math.max(200,Math.round(rect.height));
  return {w,h,left:w<380?47:58,right:w-18,top:20,bottom:h-28};
}
function seriesSignature(points) {
  if(!points.length) return "";
  const a=points[0],z=points.at(-1);
  return [points.length,a[0],a[1],z[0],z[1],points[Math.floor(points.length/2)]?.join(",")].join(":");
}
function pathFor(points,getX,getY) {
  return points.map((point,i)=>(i?"L":"M")+getX(point[0]).toFixed(2)+" "+getY(point[1]).toFixed(2)).join(" ");
}
function clearCursor() {
  hover=-1;
  if(cursor) cursor.setAttribute("visibility","hidden");
  if(marker) marker.setAttribute("visibility","hidden");
  tip.hidden=true;
}
function updateGraph() {
  if(!snapshot) return;
  const all=(snapshot.pace || []).filter(p=>Array.isArray(p)&&Number.isFinite(p[0])&&Number.isFinite(p[1]));
  const points=windowSize ? all.slice(-windowSize) : all;
  const frame=geometry();
  const elapsed=snapshot.pace_axis ? snapshot.pace_axis==="elapsed_seconds" : !snapshot.capture;
  const unit="tokens";
  const key=[snapshot.run,snapshot.case,snapshot.pace_axis,unit,frame.w,frame.h,windowSize,seriesSignature(points)].join("|");
  if(key===chartKey) return;
  chartKey=key;
  clearCursor();
  plotted=points;
  svg.setAttribute("viewBox","0 0 "+frame.w+" "+frame.h);
  if(!points.length) {
    svg.replaceChildren(node("text",{x:18,y:frame.h/2,class:"axis-label"},"Waiting for trace samples"));
    svg.setAttribute("aria-label","Waiting for trace samples");
    value("chart-domain","Waiting for telemetry");
    return;
  }
  const {left,right,top,bottom,w}=frame;
  const first=points[0],last=points.at(-1);
  const isTail=first[1]>1;
  const minX=windowSize||isTail?first[0]:Math.min(0,first[0]);
  const maxX=Math.max(minX+0.001,last[0]);
  const minY=windowSize||isTail?Math.max(0,Math.min(...points.map(p=>p[1]))):0;
  const maxY=Math.max(minY+1,...points.map(p=>p[1]));
  const ratePoints=[];
  if(elapsed) for(let i=1;i<points.length;i++){
    const a=points[Math.max(0,i-7)],b=points[i], dt=b[0]-a[0];
    if(dt>0&&b[1]>=a[1]) ratePoints.push([b[0],(b[1]-a[1])/dt]);
  }
  const showRate=ratePoints.length>=5;
  const maxRate=Math.max(1,...ratePoints.map(p=>p[1]));
  const mainBottom=showRate ? bottom-57 : bottom;
  const x=v=>left+(right-left)*(v-minX)/(maxX-minX);
  const y=v=>mainBottom-(mainBottom-top)*(v-minY)/(maxY-minY);
  scale={x,y,left,right,top,bottom,minX,maxX,w,elapsed,unit};
  const defs=node("defs",{});
  const line=node("linearGradient",{id:"signal",gradientUnits:"userSpaceOnUse",x1:left,x2:right,y1:0,y2:0});
  const area=node("linearGradient",{id:"area-fill",x1:0,x2:0,y1:0,y2:1});
  colors.forEach((color,i)=>line.append(node("stop",{offset:i/(colors.length-1),"stop-color":color})));
  area.append(node("stop",{offset:0,"stop-color":"#7587f7","stop-opacity":".24"}),node("stop",{offset:1,"stop-color":"#7587f7","stop-opacity":".02"}));
  defs.append(line,area);
  const grid=node("g",{});
  const divisions=w<460?4:6;
  for(let i=0;i<=divisions;i++){
    const tx=left+(right-left)*i/divisions;
    const time=minX+(maxX-minX)*i/divisions;
    grid.append(node("path",{d:"M"+tx+" "+top+"V"+bottom,class:"grid"}));
    grid.append(node("text",{x:tx,y:bottom+17,"text-anchor":i===0?"start":i===divisions?"end":"middle",class:"axis-label"},elapsed?fmt(time)+"s":fmt(Math.round(time))));
  }
  for(let i=0;i<=4;i++){
    const ty=mainBottom-(mainBottom-top)*i/4;
    grid.append(node("path",{d:"M"+left+" "+ty+"H"+right,class:"grid"}));
    grid.append(node("text",{x:left-7,y:ty+4,"text-anchor":"end",class:"axis-label"},fmt(Math.round(minY+(maxY-minY)*i/4))));
  }
  const plot=pathFor(points,x,y);
  const polygon=plot+" L"+x(last[0])+" "+mainBottom+" L"+x(first[0])+" "+mainBottom+" Z";
  const bits=[defs,grid,node("path",{d:polygon,fill:"url(#area-fill)"}),node("path",{d:plot,class:"signal-shadow"}),node("path",{d:plot,class:"signal-line"})];
  if(showRate){
    const low=mainBottom+17;
    const rateY=v=>bottom-(bottom-low)*v/maxRate;
    bits.push(node("path",{d:"M"+left+" "+low+"H"+right+"M"+left+" "+bottom+"H"+right,class:"grid"}));
    bits.push(node("text",{x:left-7,y:low+5,"text-anchor":"end",class:"axis-label"},unit==="tokens"?"tok/s":"st/s"));
    bits.push(node("path",{d:pathFor(ratePoints,x,rateY),class:"signal-line",opacity:.65}));
  }
  bits.push(node("circle",{cx:x(last[0]),cy:y(last[1]),r:4,fill:"#d9a4ff",stroke:"#101827","stroke-width":1.5}));
  cursor=node("path",{class:"cursor-line",visibility:"hidden"});
  marker=node("circle",{r:4,fill:"#f2f6ff",visibility:"hidden"});
  svg.replaceChildren(...bits,cursor,marker);
  svg.setAttribute("aria-label",fmt(last[1])+" "+unit+"; use arrow keys to inspect "+points.length+" samples");
  value("chart-domain",elapsed?fmt(last[0]-minX)+" s displayed"+(isTail?" · retained trace":""):points.length+" capture points · sample order");
}
function showPoint(index){
  if(!scale || !plotted.length) return;
  hover=Math.max(0,Math.min(index,plotted.length-1));
  const [tx,n]=plotted[hover],x=scale.x(tx),y=scale.y(n);
  cursor.setAttribute("d","M"+x+" "+scale.top+"V"+scale.bottom);
  cursor.removeAttribute("visibility");
  marker.setAttribute("cx",x);marker.setAttribute("cy",y);marker.removeAttribute("visibility");
  tip.textContent=fmt(n)+" "+scale.unit+" · "+(scale.elapsed?fmt(tx)+" s":"sample "+fmt(tx));
  tip.hidden=false;
  const maxLeft=Math.max(8,chart.clientWidth-tip.offsetWidth-8);
  tip.style.left=Math.max(8,Math.min(maxLeft,x+9))+"px";
  tip.style.top=Math.max(8,y-31)+"px";
}
svg.addEventListener("pointermove",event=>{
  if(!scale||!plotted.length) return;
  const rect=svg.getBoundingClientRect(),px=(event.clientX-rect.left)*scale.w/rect.width;
  const t=scale.minX+(scale.maxX-scale.minX)*(px-scale.left)/(scale.right-scale.left);
  let l=0,r=plotted.length-1;
  while(l<r){const m=(l+r)>>1;if(plotted[m][0]<t)l=m+1;else r=m;}
  showPoint(l>0&&Math.abs(plotted[l-1][0]-t)<Math.abs(plotted[l][0]-t)?l-1:l);
});
svg.addEventListener("pointerleave",clearCursor);
svg.addEventListener("blur",clearCursor);
svg.addEventListener("keydown",e=>{
  if(e.key==="Escape"){clearCursor();return;}
  if(!["ArrowLeft","ArrowRight","Home","End"].includes(e.key)||!plotted.length) return;
  e.preventDefault();
  showPoint(e.key==="Home"?0:e.key==="End"?plotted.length-1:hover<0?plotted.length-1:hover+(e.key==="ArrowLeft"?-1:1));
});
range.addEventListener("click",e=>{
  const button=e.target.closest("button[data-window]");
  if(!button) return;
  windowSize=Number(button.dataset.window);
  for(const item of range.querySelectorAll("button"))item.setAttribute("aria-pressed",String(item===button));
  updateGraph();
});
if("ResizeObserver" in window) new ResizeObserver(updateGraph).observe(chart);
else window.addEventListener("resize",updateGraph);

const palette=[[19,26,55],[69,67,148],[35,141,185],[53,205,181],[228,250,150],[255,199,128]];
function drawHeat(data){
  if(!data || !Number.isInteger(data.rows)||!Number.isInteger(data.columns)||data.rows<1||data.columns<1||
    !Array.isArray(data.rms)||data.rms.length!==data.rows*data.columns||data.rms.length>131072) return;
  heat=data;
  const values=data.rms, width=data.columns, height=data.rows;
  let max=Number.EPSILON;
  for(const v of values) if(Number.isFinite(v)&&v>max) max=v;
  canvas.width=width;canvas.height=height;
  const ctx=canvas.getContext("2d");
  if(!ctx) return;
  const image=ctx.createImageData(width,height);
  values.forEach((v,i)=>{
    const position=Math.sqrt(Math.max(0,Number.isFinite(v)?v/max:0))*(palette.length-1);
    const n=Math.min(palette.length-2,Math.floor(position)), fraction=position-n;
    for(let c=0;c<3;c++) image.data[i*4+c]=Math.round(palette[n][c]+fraction*(palette[n+1][c]-palette[n][c]));
    image.data[i*4+3]=255;
  });
  ctx.putImageData(image,0,0);
  value("weight-note",data.label);
  value("weight-ratio",Number.isFinite(data.relative_percent)?data.relative_percent.toFixed(3)+"% change":"—");
  value("weight-resolution",height+" × "+width+" · "+values.length.toLocaleString()+" measured cells");
  value("weight-cell","");
  canvas.setAttribute("aria-label",data.label+", "+height+" rows by "+width+" columns of RMS changes");
  byId("legend").hidden=false;
}
async function fetchHeat(meta){
  if(!meta)return;
  if(heatCache.has(meta.id)){if(weightController)weightController.abort();drawHeat(heatCache.get(meta.id));return;}
  if(weightController)weightController.abort();
  const controller=new AbortController();
  weightController=controller;
  try{
    const resp=await fetch("/api/weights?id="+encodeURIComponent(meta.id),{signal:controller.signal,cache:"no-store"});
    if(!resp.ok) throw Error("Weight comparison unavailable");
    const raw=await resp.json(),data=raw.weights||raw;
    if(controller.signal.aborted||select.value!==meta.id||data.id!==meta.id) return;
    if(heatCache.size>=4)heatCache.delete(heatCache.keys().next().value);
    heatCache.set(meta.id,data);drawHeat(data);
  }catch(error){if(!controller.signal.aborted)value("weight-note","Comparison is temporarily unavailable");}
}
let comparisons=[];
function renderWeights(data){
  comparisons=Array.isArray(data.comparisons)?data.comparisons.filter(w=>w&&typeof w.id==="string"&&typeof w.label==="string"):[data.weights,data.reference_weights].filter(Boolean);
  comparisons.sort((a,b)=>b.rows*b.columns-a.rows*a.columns);
  const signature=comparisons.map(w=>w.id+"|"+w.label+"|"+w.rows+"|"+w.columns+"|"+w.relative_percent).join("\n");
  if(signature===weightsKey) return;
  weightsKey=signature;
  updateOptions(select,comparisons.map(w=>[w.label,w.id]));
  select.disabled=!comparisons.length;
  const choice=comparisons.find(w=>w.id===select.value);
  if(choice?.rms)drawHeat(choice);
  else if(choice)fetchHeat(choice);
}
select.addEventListener("change",()=>{
  const choice=comparisons.find(w=>w.id===select.value);
  if(choice?.rms)drawHeat(choice);else fetchHeat(choice);
});
canvas.addEventListener("pointermove",e=>{
  if(!heat)return;
  const rect=canvas.getBoundingClientRect();
  const col=Math.max(0,Math.min(heat.columns-1,Math.floor((e.clientX-rect.left)*heat.columns/rect.width)));
  const row=Math.max(0,Math.min(heat.rows-1,Math.floor((e.clientY-rect.top)*heat.rows/rect.height)));
  value("weight-cell","Row "+(row+1)+" · Col "+(col+1)+" · RMS "+heat.rms[row*heat.columns+col].toExponential(3));
});
canvas.addEventListener("pointerleave",()=>value("weight-cell",""));

function renderEvents(events){
  const key=JSON.stringify(events);
  if(key===eventKey)return;
  eventKey=key;
  value("event-count",String(events.length));
  const rows=events.slice().reverse().map(e=>{
    const tr=document.createElement("tr");
    const time=e.time?new Date(e.time).toLocaleTimeString(undefined,{hour12:false}):e.elapsed_ms>=0?fmt(e.elapsed_ms/1000)+" s":"—";
    const name=human(e.event)+(Number.isFinite(e.margin)?" · "+e.margin.toFixed(3):"");
    const tdTime=document.createElement("td"),tdName=document.createElement("td"),tdStep=document.createElement("td");
    tdTime.textContent=time;tdStep.textContent=fmt(e.step>=0?e.step:e.processed_tokens);
    const label=document.createElement("span");
    label.className="event-name";label.textContent=name;
    if(/complete|ready/i.test(e.event))label.style.setProperty("--event","#69e6ad");
    else if(/error|stop|cap/i.test(e.event))label.style.setProperty("--event","#ffb78f");
    else if(/capture/i.test(e.event))label.style.setProperty("--event","#b0a0ff");
    tdName.append(label);tr.append(tdTime,tdName,tdStep);return tr;
  });
  byId("events").replaceChildren(...rows);
}
function render(data){
  snapshot=data;
  updateOptions(runs,[["Follow newest run",""],...(data.choices||[]).map(x=>[x,x])]);
  status(data.status||"Waiting for trace");
  const token=data.latest_token||{}, capture=data.latest_capture||{};
  const count=Number.isFinite(token.step)?token.step+1:NaN;
  const samples=(data.pace||[]).length;
  const latest=data.latest||{};
  value("stage",human(latest.event));
  value("count-label",data.capture?"Captured states":"Generated tokens");
  value("rate-label",data.capture?"Next-token matches":"Decode rate");
  value("tokens",fmt(data.capture?(capture.captured_rows??capture.processed_tokens):count));
  value("rate",data.capture?fmt(capture.native_next_matches):token.decode_elapsed_ms>0?fmt(count*1000/token.decode_elapsed_ms)+" tok/s":"—");
  value("samples",fmt(samples));
  value("trace-label",data.capture?"Capture trace":"Token trace");
  value("line-key-label",data.capture?"Processed tokens":"Cumulative tokens");
  value("case",data.case||"Waiting for a case");
  value("finish",{length:"Token cap reached",eog:"Natural end token"}[data.finish]||"");
  updateGraph();renderEvents(data.events||[]);renderWeights(data);
}
function stopLive(){clearTimeout(timer);if(liveController){liveController.abort();liveController=undefined;}}
async function refresh(){
  clearTimeout(timer);
  if(paused||document.hidden||liveController)return;
  const controller=new AbortController();
  liveController=controller;
  try{
    const response=await fetch("/api/live?weights=0&run="+encodeURIComponent(runs.value),{signal:controller.signal,cache:"no-store"});
    if(!response.ok)throw Error("Trace unavailable");
    const data=await response.json();
    if(!controller.signal.aborted&&!paused)render(data);
  }catch(error){if(!controller.signal.aborted&&!paused)status("Connection unavailable","warning");}
  finally{
    if(liveController===controller){liveController=undefined;if(!paused&&!document.hidden)timer=setTimeout(refresh,1200);}
  }
}
pause.addEventListener("click",()=>{
  paused=!paused;pause.setAttribute("aria-pressed",String(paused));
  pause.textContent=paused?"▶  Resume view":"Ⅱ  Pause view";
  if(paused){stopLive();status("View paused","paused");}else refresh();
});
runs.addEventListener("change",()=>{stopLive();if(!paused)refresh();});
document.addEventListener("visibilitychange",()=>{if(document.hidden)stopLive();else refresh();});
refresh();

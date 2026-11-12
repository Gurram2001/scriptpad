const T=['scene','action','character','paren','dialogue','trans'];
const LABEL={scene:'Scene',action:'Action',character:'Character',paren:'Paren',dialogue:'Dialogue',trans:'Transition'};
const NEXT={scene:'action',action:'action',character:'dialogue',paren:'dialogue',dialogue:'character',trans:'scene'};
const SHORT={scene:'Scene',action:'Action',character:'Char',paren:'Paren',dialogue:'Dialog',trans:'Trans'};
const PH={scene:'INT. PLACE - DAY',action:'Describe what we see…',character:'CHARACTER',paren:'(beat)',dialogue:'Dialogue',trans:'CUT TO:'};
const $=s=>document.querySelector(s);
function fresh(seed){
 const id=Date.now()+Math.floor(Math.random()*999);
 return {id,title:seed?'My First Screenplay':'Untitled Screenplay',blocks:seed?[
  {t:'scene',x:'INT. KITCHEN - EARLY MORNING'},
  {t:'action',x:'Steam curls from a pot of filter coffee. MEERA (30s) stares at a blank page.'},
  {t:'character',x:'MEERA'},
  {t:'paren',x:'(to herself)'},
  {t:'dialogue',x:'Every story’s got to start somewhere.'},
  {t:'action',x:''}
 ]:[{t:'scene',x:''}]};
}
let S=null;
function cleanScript(s){
 if(!s||typeof s!=='object'||!Array.isArray(s.blocks))return null;
 const id=Number(s.id);if(!Number.isSafeInteger(id)||id<=0)return null;
 const str=(v,n)=>typeof v==='string'?v.slice(0,n):'';
 const blk=a=>a.slice(0,20000).map(b=>({t:b&&T.includes(b.t)?b.t:'action',x:str(b&&b.x,20000)}));
 const o={id,title:str(s.title,200)||'Untitled Screenplay',blocks:blk(s.blocks)};
 if(!o.blocks.length)o.blocks=[{t:'scene',x:''}];
 if(Number(s.u)>0)o.u=Number(s.u);
 if(s.author)o.author=str(s.author,200);
 if(Number(s.sn)>0)o.sn=Math.min(Number(s.sn),1e6);
 if(Array.isArray(s.snaps))o.snaps=s.snaps.slice(0,15).filter(v=>v&&Array.isArray(v.blocks)).map(v=>({t:Number(v.t)||0,name:str(v.name,60),blocks:blk(v.blocks)}));
 return o;
}
function cleanState(r){
 if(!r||typeof r!=='object'||!Array.isArray(r.scripts))return null;
 const seen=new Set(),scripts=[];
 r.scripts.forEach(x=>{const c=cleanScript(x);if(c&&!seen.has(c.id)){seen.add(c.id);scripts.push(c)}});
 if(!scripts.length)return null;
 const dead=(Array.isArray(r.dead)?r.dead:[]).map(d=>({id:Number(d&&d.id),u:Number(d&&d.u)||0})).filter(d=>Number.isSafeInteger(d.id)&&d.id>0).slice(0,500);
 return {cur:seen.has(Number(r.cur))?Number(r.cur):scripts[0].id,scripts,dead};
}
function objUrl(b){const u=URL.createObjectURL(b);setTimeout(()=>URL.revokeObjectURL(u),30000);return u}
try{const raw=localStorage.getItem('scriptpad1');if(raw){try{S=cleanState(JSON.parse(raw))}catch(e){S=null}if(!S)localStorage.setItem('scriptpad1-corrupt',raw)}}catch(e){}
if(!S||!S.scripts||!S.scripts.length){const f=fresh(true);S={cur:f.id,scripts:[f]}}
let act=0,timer,delT;
const cur=()=>S.scripts.find(s=>s.id===S.cur)||S.scripts[0];
let toastT;
function say(m){$('#sv').textContent=m;if(!/^(Saved|Saving…)$/.test(m)){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(toastT);toastT=setTimeout(()=>t.classList.remove('on'),2400)}}

function fit(t){t.style.height='auto';t.style.height=t.scrollHeight+'px'}
function setT(b,t,type){b.t=type;t.className=type;t.placeholder=PH[type];fit(t);tbHi();refreshContd()}
function tbHi(){const b=cur().blocks[act];document.querySelectorAll('#tb button').forEach(x=>x.classList.toggle('on',!!b&&x.dataset.t===b.t));sug()}
function focusAt(i,pos){const t=$('#ed').children[i];if(!t)return;t.focus();const p=pos==='end'?t.value.length:0;t.setSelectionRange(p,p);t.scrollIntoView({block:'nearest'})}
function bind(t,b){
 const idx=()=>cur().blocks.indexOf(b);
 t.oninput=()=>{
  b.x=t.value;
  if(b.t==='action'&&/^(int|ext|est|int\.?\/ext|i\/e)[. ]/i.test(b.x))setT(b,t,'scene');
  fit(t);save();stats();sug();if(b.t==='scene')scenes();if(document.body.classList.contains('focus'))t.scrollIntoView({block:'center'});
 };
 t.onfocus=()=>{act=idx();tbHi()};
 t.onblur=()=>setTimeout(refreshContd,0);
 t.onkeydown=e=>{
  const i=idx(),bl=cur().blocks,k=e.key;
  if(k==='Enter'&&!e.shiftKey&&!e.isComposing){
   e.preventDefault();
   if(!b.x&&b.t!=='action'){setT(b,t,'action');save();return}
   const p=t.selectionStart,rest=b.x.slice(p);
   b.x=b.x.slice(0,p);t.value=b.x;
   bl.splice(i+1,0,{t:rest?b.t:NEXT[b.t],x:rest});
   render();focusAt(i+1,'start');refreshContd();save();return;
  }
  if(k==='Tab'){e.preventDefault();setT(b,t,T[(T.indexOf(b.t)+(e.shiftKey?5:1))%6]);save();return}
  if(k==='Backspace'&&!b.x&&i>0){e.preventDefault();bl.splice(i,1);render();focusAt(i-1,'end');save();return}
  if(k==='ArrowUp'&&t.selectionStart===0&&t.selectionEnd===0&&i>0){e.preventDefault();focusAt(i-1,'end');return}
  if(k==='ArrowDown'&&t.selectionStart===t.value.length&&i<bl.length-1){e.preventDefault();focusAt(i+1,'start');return}
  if((e.ctrlKey||e.altKey)&&k>='1'&&k<='6'){e.preventDefault();setT(b,t,T[k-1]);save()}
 };
}
function render(){
 const ed=$('#ed');ed.innerHTML='';
 cur().blocks.forEach(b=>{
  const t=document.createElement('textarea');
  t.rows=1;t.value=b.x;t.className=b.t;t.placeholder=PH[b.t];
  ed.appendChild(t);bind(t,b);
 });
 ed.querySelectorAll('textarea').forEach(fit);
 if(H.id!==cur().id){H.id=cur().id;H.u=[];H.r=[];H.last=JSON.stringify(cur().blocks)}
 head();snapUI();stats();tbHi();scenes();refreshContd();if(!$('#ol').hidden)outline();
}
function head(){
 const sel=$('#sel');sel.innerHTML='';
 S.scripts.forEach(s=>{const o=document.createElement('option');o.value=s.id;o.textContent=s.title||'Untitled';o.selected=s.id===S.cur;sel.appendChild(o)});
 $('#ttl').value=cur().title;$('#aut').value=cur().author||'';
}
function stats(){
 const bl=cur().blocks;let w=0,ln=0;
 bl.forEach(b=>{
  const n=b.x.trim()?b.x.trim().split(/\s+/).length:0;w+=n;
  const width=b.t==='dialogue'?35:b.t==='paren'?25:b.t==='character'?30:60;
  ln+=Math.max(1,Math.ceil(b.x.length/width))+(b.t==='dialogue'||b.t==='paren'?0:1);
 });
 $('#wc').textContent=w+' words · about '+(n=>n+(n===1?' page':' pages'))(Math.max(1,Math.round(ln/55)));
}
function fountain(){
 const s=cur(),o=['Title: '+s.title].concat(s.author?['Author: '+s.author]:[]).concat(['']);
 withContd().forEach(b=>{
  const x=b.x.trim();if(!x)return;
  if(b.t==='scene'){o.push('',(/^(int|ext|est|i\/e)/i.test(x)?'':'.')+x.toUpperCase())}
  else if(b.t==='action'){o.push('',x)}
  else if(b.t==='character'){o.push('',x.toUpperCase())}
  else if(b.t==='paren'){o.push(/^\(.*\)$/.test(x)?x:'('+x.replace(/^\(|\)$/g,'')+')')}
  else if(b.t==='dialogue'){o.push(x)}
  else if(b.t==='trans'){o.push('','> '+x.toUpperCase())}
 });
 return o.join('\n')+'\n';
}
function copyText(txt){
 const fb=()=>{const a=document.createElement('textarea');a.value=txt;document.body.appendChild(a);a.select();let ok=false;try{ok=document.execCommand('copy')}catch(e){}a.remove();say(ok?'Copied .fountain text':'Copy blocked by browser')};
 if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(txt).then(()=>say('Copied .fountain text'),fb);else fb();
}
T.forEach(type=>{
 const b=document.createElement('button');b.innerHTML='<span class="f">'+LABEL[type]+'</span><span class="s">'+SHORT[type]+'</span>';b.setAttribute('aria-label',LABEL[type]);b.dataset.t=type;
 b.onmousedown=e=>e.preventDefault();
 b.onclick=()=>{const bl=cur().blocks[act],t=$('#ed').children[act];if(!bl||!t)return;setT(bl,t,type);save();t.focus()};
 $('#tb').appendChild(b);
});
$('#sel').onchange=e=>{S.cur=+e.target.value;act=0;render();save()};
$('#ttl').oninput=e=>{cur().title=e.target.value;const o=$('#sel').selectedOptions[0];if(o)o.textContent=e.target.value||'Untitled';save()};
$('#bn').onclick=()=>{const f=fresh(false);S.scripts.push(f);S.cur=f.id;act=0;render();focusAt(0,'start');save()};
function sug(){
 const g=$('#sg');g.innerHTML='';
 const bl=cur().blocks,b=bl[act],t=$('#ed').children[act];
 if(!b||!t)return;
 let items=[];
 if(b.t==='character'){
  const q=b.x.trim().toUpperCase();
  const base=nameOf(q),names=[...new Set(bl.filter(x=>x.t==='character'&&x!==b).map(x=>nameOf(x.x)).filter(Boolean))];
  items=names.filter(n=>n!==q&&n.startsWith(q)).slice(0,8).map(n=>[n,n]);
  if(base&&q===base)items.push(['(V.O.)',base+' (V.O.)'],['(O.S.)',base+' (O.S.)']);
  if(base)items.push(['Rename all','__rename']);
 }else if(b.t==='scene'){
  const q=b.x.toUpperCase().trim();
  if(!/^(INT|EXT)/.test(q))items=['INT. ','EXT. ','INT./EXT. '].map(v=>[v.trim(),v]);
  else if(!q.includes(' - ')){
   const locs=[...new Set(bl.filter(x=>x.t==='scene'&&x!==b).map(x=>x.x.toUpperCase().split(' - ')[0].trim()))].filter(l=>l&&l!==q&&l.startsWith(q)).slice(0,4);
   items=locs.map(l=>[l,l+' - ']).concat(['DAY','NIGHT','MORNING','EVENING'].map(x=>[x,b.x.replace(/\s*-?\s*$/,'')+' - '+x]));
  }
 }
 items.forEach(([lab,val])=>{
  const c=document.createElement('button');c.textContent=lab;
  c.onmousedown=e=>e.preventDefault();
  c.onclick=()=>{if(val==='__rename')return renameUI(b);b.x=val;t.value=val;fit(t);save();stats();if(b.t==='scene')scenes();sug();t.focus();t.setSelectionRange(val.length,val.length)};
  g.appendChild(c);
 });
}
function scenes(){
 const s=$('#sc'),bl=cur().blocks;
 s.innerHTML='<option value="">Jump</option>';
 const g1=document.createElement('optgroup'),g2=document.createElement('optgroup'),cast=Object.create(null);
 g1.label='Scenes';g2.label='Characters';
 bl.forEach((b,i)=>{
  if(b.t==='scene'&&b.x.trim()){const o=document.createElement('option');o.value=i;o.textContent=(g1.children.length+1)+'. '+b.x.toUpperCase().slice(0,40);g1.appendChild(o)}
  if(b.t==='character'&&b.x.trim()){const n=nameOf(b.x);(cast[n]=cast[n]||{i,c:0}).c++}
 });
 Object.keys(cast).forEach(n=>{const o=document.createElement('option');o.value=cast[n].i;o.textContent=n+' ('+cast[n].c+')';g2.appendChild(o)});
 if(g1.children.length)s.appendChild(g1);
 if(g2.children.length)s.appendChild(g2);
}
$('#sc').onchange=e=>{const i=e.target.value;if(i!==''){const t=$('#ed').children[+i];if(t){t.scrollIntoView({block:'start'});focusAt(+i,'end')}}e.target.value=''};
function parseF(txt){
 const f=fresh(false);f.blocks=[];f.title='Imported Screenplay';
 txt.replace(/\r/g,'').split(/\n\s*\n/).forEach((p,pi)=>{
  const ls=p.split('\n').map(l=>l.trim()).filter(Boolean);
  if(!ls.length)return;
  const first=ls[0];
  if(pi===0&&/^(title|author|credit|source|draft date|contact):/i.test(first)){
   ls.forEach(l=>{let m=l.match(/^title:\s*(.*)/i);if(m)f.title=m[1];m=l.match(/^author:\s*(.*)/i);if(m)f.author=m[1]});return;
  }
  if(/^\.[^.]/.test(first)||/^(int|ext|est|int\.?\/ext|i\/e)[. ]/i.test(first)){
   f.blocks.push({t:'scene',x:first.replace(/^\./,'')});ls.slice(1).forEach(l=>f.blocks.push({t:'action',x:l}));return;
  }
  if(ls.length===1&&(/^>[^<]*$/.test(first)||(/TO:$/.test(first)&&first===first.toUpperCase()))){f.blocks.push({t:'trans',x:first.replace(/^>\s*/,'')});return}
  if(ls.length>1&&first===first.toUpperCase()&&/[A-Z]/.test(first)){
   f.blocks.push({t:'character',x:first.replace(/^@/,'')});
   ls.slice(1).forEach(l=>f.blocks.push({t:/^\(.*\)$/.test(l)?'paren':'dialogue',x:l}));return;
  }
  f.blocks.push({t:'action',x:ls.join('\n')});
 });
 if(!f.blocks.length)f.blocks.push({t:'scene',x:''});
 return f;
}
function cover(){$('#cv1').textContent=cur().title;$('#cv2').textContent=cur().author?'Written by\n'+cur().author:''}
window.addEventListener('beforeprint',cover);
$('#aut').oninput=e=>{cur().author=e.target.value;save()};
$('#bc').onclick=()=>{$('#mh').textContent='Export, import & backup';$('#mt').value=fountain();$('#md').hidden=false};
$('#mx').onclick=()=>{$('#md').hidden=true};
$('#mc').onclick=()=>copyText($('#mt').value);
$('#mi').onclick=()=>{const raw=$('#mt').value;if(raw.length>2e6){say('That text is too large to import (2 MB max)');return}const f=cleanScript(parseF(raw));if(!f){say('Could not import that text');return}S.scripts.push(f);S.cur=f.id;act=0;$('#md').hidden=true;render();save()};
window.addEventListener('keydown',e=>{if(e.key==='Escape'){$('#md').hidden=true;$('#sm').hidden=true;document.body.classList.remove('focus')}});
const nameOf=x=>x.replace(/(\s*\([^)]*\))+\s*$/,'').trim().toUpperCase();
function refreshContd(){
 const bl=cur().blocks,tas=$('#ed').children;let last=null,ch=false;
 bl.forEach((b,i)=>{
  if(b.t==='scene')last=null;
  if(b.t!=='character'||!b.x.trim())return;
  const base=b.x.replace(/\s*\(CONT['\u2019]D\)\s*$/i,'').trim(),n=nameOf(base);
  const x=n===last?base+" (CONT'D)":base;
  if(x!==b.x.trim()&&document.activeElement!==tas[i]){b.x=x;if(tas[i]){tas[i].value=x;fit(tas[i])}ch=true}
  last=n;
 });
 if(ch){save();scenes()}
}
let dip=null;
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();dip=e});
window.addEventListener('appinstalled',()=>{dip=null;say('Installed')});
async function installHelp(){
 const L=[],standalone=matchMedia('(display-mode: standalone)').matches||navigator.standalone;
 L.push(standalone?'Already running as an installed app.':'Running in a browser tab.');
 L.push('Secure (https) page: '+(isSecureContext?'yes':'NO - open the https:// link'));
 let mf='not found in page';
 try{const l=document.querySelector('link[rel=manifest]');if(l){const r=await fetch(l.href);mf=r.ok?'loaded (HTTP '+r.status+')':'FAILED (HTTP '+r.status+') - upload manifest.webmanifest and the icon files'}}catch(e){mf='failed to load'}
 L.push('Manifest: '+mf);
 let sw='not supported here';
 try{if('serviceWorker' in navigator){const r=await navigator.serviceWorker.getRegistration();sw=r?(r.active?'active':'installing - reload once'):'not registered - upload sw.js'}}catch(e){sw='error'}
 L.push('Offline worker: '+sw);
 L.push('Browser install prompt ready: '+(dip?'yes - tap Install again':'no'));
 L.push('');
 L.push(/iphone|ipad|ipod/i.test(navigator.userAgent)?'iPhone/iPad: open this page in Safari, tap Share, then Add to Home Screen.':'Android Chrome: menu (three dots), then Install app or Add to Home screen. Desktop Chrome/Edge: install icon in the address bar. In-app browsers and private tabs do not offer install: open the link in Chrome or Safari.');
 $('#mh').textContent='Install help';$('#mt').value=L.join('\n');$('#md').hidden=false;
}
$('#bi').onclick=async()=>{
 if(dip){const p=dip;dip=null;p.prompt();try{await p.userChoice}catch(e){}return}
 installHelp();
};
const CFG=window.SCRIPTPAD||{};
let AU=null;try{AU=JSON.parse(localStorage.getItem('scriptpad-auth'))}catch(e){}
const BASE=String(CFG.supabaseUrl||'').replace(/\/+$/,'');
const sbOn=()=>!!CFG.supabaseKey&&/^(https:\/\/[^\/\s]+|http:\/\/(127\.0\.0\.1|localhost)(:\d+)?)$/.test(BASE);
let H={id:0,u:[],r:[],last:'[]'},ht,syT,syncing=false;
function persist(){try{localStorage.setItem('scriptpad1',JSON.stringify(S));say('Saved')}catch(e){say('Not saved – storage blocked')}}
function save(){cur().u=Date.now();hist();say('Saving…');clearTimeout(timer);timer=setTimeout(()=>{persist();clearTimeout(syT);if(AU&&sbOn())syT=setTimeout(syncNow,3000)},300)}
function commit(){clearTimeout(ht);const j=JSON.stringify(cur().blocks);if(j===H.last)return;H.u.push(H.last);if(H.u.length>200)H.u.shift();H.r=[];H.last=j}
function hist(){
 const b=cur().blocks,a=JSON.parse(H.last);
 if(JSON.stringify(b)===H.last)return;
 if(a.length!==b.length||a.some((x,i)=>!b[i]||x.t!==b[i].t))commit();else{clearTimeout(ht);ht=setTimeout(commit,700)}
}
function jump(){act=Math.min(act,cur().blocks.length-1);render();focusAt(act,'end');save()}
function undo(){commit();if(!H.u.length){say('Nothing to undo');return}H.r.push(H.last);H.last=H.u.pop();cur().blocks=JSON.parse(H.last);jump()}
function redo(){commit();if(!H.r.length){say('Nothing to redo');return}H.u.push(H.last);H.last=H.r.pop();cur().blocks=JSON.parse(H.last);jump()}
window.addEventListener('keydown',e=>{
 const m=e.ctrlKey||e.metaKey,k=e.key.toLowerCase();
 if(!m||e.altKey||(e.target.closest&&!e.target.closest('#ed')&&e.target!==document.body))return;
 if(k==='z'){e.preventDefault();e.shiftKey?redo():undo()}else if(k==='y'){e.preventDefault();redo()}
},true);
$('#bu').onclick=undo;$('#br').onclick=redo;
$('#bf').onclick=()=>{document.body.classList.add('focus');const t=$('#ed').children[act];if(t)t.focus()};
$('#fx').onclick=()=>document.body.classList.remove('focus');
function groups(){const g=[];let c=null;cur().blocks.forEach(b=>{if(b.t==='scene'||!c){c={s:b.t==='scene',b:[]};g.push(c)}c.b.push(b)});return g}
function outline(){
 const o=$('#ol'),g=groups();o.innerHTML='';let n=0;
 const h=document.createElement('p');h.textContent='Outline – tap a scene to jump, use the arrows to reorder';h.style.cssText='margin:0 0 8px;font-size:12px;color:var(--mute)';o.appendChild(h);
 g.forEach((x,gi)=>{
  if(!x.s)return;n++;
  const a=x.b.find(b=>b.t==='action'&&b.x.trim()),d=document.createElement('div'),t=document.createElement('b'),s=document.createElement('span');
  d.className='card';t.textContent=n+'. '+(x.b[0].x.trim().toUpperCase()||'(untitled scene)');s.textContent=a?a.x.trim().slice(0,90):'No action yet';
  d.append(t,s);
  [['▲',-1],['▼',1]].forEach(([l,dir])=>{
   const bt=document.createElement('button');bt.textContent=l;bt.setAttribute('aria-label',dir<0?'Move scene up':'Move scene down');
   bt.onclick=e=>{e.stopPropagation();const j=gi+dir;if(!g[j]||!g[j].s)return;[g[gi],g[j]]=[g[j],g[gi]];cur().blocks=g.flatMap(y=>y.b);render();save();outline()};
   d.appendChild(bt);
  });
  d.onclick=()=>{const i=cur().blocks.indexOf(x.b[0]),t=$('#ed').children[i];if(t){t.scrollIntoView({block:'center'});focusAt(i,'end')}if(innerWidth<700)$('#ol').hidden=true};
  o.appendChild(d);
 });
 if(!n){const e=document.createElement('p');e.textContent='No scenes yet. Start with a scene heading like INT. KITCHEN - DAY.';o.appendChild(e)}
}
$('#bo').onclick=()=>{const o=$('#ol');o.hidden=!o.hidden;if(!o.hidden)outline()};
class MiniPDF{
 constructor(){this.pages=[[]]}
 addPage(){this.pages.push([])}
 text(t,x,y,o){t=String(t);const w=t.length*7.2;if(o&&o.align==='right')x-=w;else if(o&&o.align==='center')x-=w/2;this.pages[this.pages.length-1].push([t,x,y])}
 build(){
  const M={8217:146,8216:145,8220:147,8221:148,8211:150,8212:151,8230:133};
  const enc=s=>{let o='';for(const ch of s){let c=ch.charCodeAt(0);c=M[c]||c;if(c>255)c=63;if(c<32)c=32;o+=(c===40||c===41||c===92)?'\\'+String.fromCharCode(c):String.fromCharCode(c)}return o};
  const objs=[],n=this.pages.length;
  objs.push('<</Type/Catalog/Pages 2 0 R>>');
  objs.push('<</Type/Pages/Kids['+this.pages.map((_,i)=>(4+2*i)+' 0 R').join(' ')+']/Count '+n+'>>');
  objs.push('<</Type/Font/Subtype/Type1/BaseFont/Courier/Encoding/WinAnsiEncoding>>');
  this.pages.forEach((p,i)=>{
   const cs=p.map(([t,x,y])=>'BT /F1 12 Tf '+x.toFixed(2)+' '+(792-y).toFixed(2)+' Td ('+enc(t)+') Tj ET').join('\n');
   objs.push('<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources<</Font<</F1 3 0 R>>>>/Contents '+(5+2*i)+' 0 R>>');
   objs.push('<</Length '+cs.length+'>>\nstream\n'+cs+'\nendstream');
  });
  let out='%PDF-1.4\n';const off=[];
  objs.forEach((o,i)=>{off.push(out.length);out+=(i+1)+' 0 obj\n'+o+'\nendobj\n'});
  const x=out.length;
  return out+'xref\n0 '+(objs.length+1)+'\n0000000000 65535 f \n'+off.map(v=>String(v).padStart(10,'0')+' 00000 n \n').join('')+'trailer\n<</Size '+(objs.length+1)+'/Root 1 0 R>>\nstartxref\n'+x+'\n%%EOF';
 }
 save(name){
  const s=this.build(),u=new Uint8Array(s.length);for(let i=0;i<s.length;i++)u[i]=s.charCodeAt(i)&255;
  const a=document.createElement('a');a.href=objUrl(new Blob([u],{type:'application/pdf'}));a.download=name;document.body.appendChild(a);a.click();a.remove();
 }
}
const ssay=m=>{$('#ss').textContent=m};
function syUI(){
 const on=sbOn(),si=!!AU;
 ssay(!on?'Sync is not set up yet. Add your Supabase URL and public key to config.js (see README).':si?'Signed in as '+AU.user.email:'Sign in or create an account to sync your scripts across devices.');
 ['#se','#sp','#si','#su'].forEach(q=>$(q).hidden=!on||si);
 ['#sn','#so'].forEach(q=>$(q).hidden=!(on&&si));
}
function setAU(d){
 AU={access_token:d.access_token,refresh_token:d.refresh_token,expires_at:d.expires_at||Math.floor(Date.now()/1000)+(d.expires_in||3600),user:d.user?{id:d.user.id,email:d.user.email}:(AU&&AU.user)};
 try{localStorage.setItem('scriptpad-auth',JSON.stringify(AU))}catch(e){}
}
async function sb(path,opt={},useAuth=true){
 const h={apikey:CFG.supabaseKey,'Content-Type':'application/json',...(opt.headers||{})};
 if(useAuth&&AU){
  if(AU.expires_at*1000<Date.now()+60000){try{const d=await sb('/auth/v1/token?grant_type=refresh_token',{method:'POST',body:JSON.stringify({refresh_token:AU.refresh_token})},false);setAU(d)}catch(e){AU=null;try{localStorage.removeItem('scriptpad-auth')}catch(x){}syUI();throw new Error('Session expired – please sign in again')}}
  h.Authorization='Bearer '+AU.access_token;
 }
 const r=await fetch(BASE+path,{...opt,headers:h}),t=await r.text();
 if(!r.ok)throw new Error(r.status+' '+t.slice(0,100));
 return t?JSON.parse(t):null;
}
const isSeed=s=>!s.u&&s.blocks[0]&&s.blocks[0].x==='INT. KITCHEN - EARLY MORNING'&&s.blocks.length<=6;
async function syncNow(){
 if(syncing||!AU||!sbOn())return;
 syncing=true;ssay('Syncing…');
 try{
  const rows=await sb('/rest/v1/scripts?select=id,data,updated_at,deleted'),remote=new Map(rows.map(r=>[String(r.id),r]));
  let changed=false;S.dead=S.dead||[];
  rows.forEach(r=>{
   const t=Date.parse(r.updated_at),i=S.scripts.findIndex(s=>String(s.id)===String(r.id)),loc=S.scripts[i],dead=S.dead.find(d=>String(d.id)===String(r.id));
   if(r.deleted){if(loc&&(loc.u||0)<=t){S.scripts.splice(i,1);changed=true}return}
   if(dead&&dead.u>=t)return;
   const cd=cleanScript({...(r.data&&typeof r.data==='object'?r.data:{}),id:r.id});if(!cd)return;cd.u=cd.u||t;if(!loc){S.scripts.push(cd);changed=true}else if(t>(loc.u||0)+1){S.scripts[i]=cd;changed=true}
  });
  const up=[];
  S.scripts.forEach(s=>{
   if(!s.u&&!isSeed(s)&&s.blocks.some(b=>b.x.trim()))s.u=Date.now();
   const r=remote.get(String(s.id));
   if(s.u&&(!r||(!r.deleted&&s.u>Date.parse(r.updated_at)+1)||(r.deleted&&s.u>Date.parse(r.updated_at)+1)))up.push({user_id:AU.user.id,id:s.id,data:s,updated_at:new Date(s.u).toISOString(),deleted:false});
  });
  S.dead.forEach(d=>{const r=remote.get(String(d.id));if(!r||(!r.deleted&&d.u>Date.parse(r.updated_at)))up.push({user_id:AU.user.id,id:d.id,data:{id:d.id,title:'',blocks:[]},updated_at:new Date(d.u).toISOString(),deleted:true})});
  if(up.length)await sb('/rest/v1/scripts?on_conflict=user_id,id',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=minimal'},body:JSON.stringify(up)});
  if(!S.scripts.length)S.scripts.push(fresh(false));
  if(!S.scripts.some(s=>s.id===S.cur))S.cur=S.scripts[0].id;
  persist();if(changed){act=0;render()}
  ssay('Synced at '+new Date().toLocaleTimeString()+' ('+rows.length+' in cloud, '+up.length+' sent)');say('Synced');
 }catch(e){ssay('Sync failed ('+(navigator.onLine?e.message:'offline')+'). Your scripts are safe on this device.')}
 syncing=false;
}
async function doAuth(kind){
 try{
  const em=$('#se').value.trim(),pw=$('#sp').value;
  if(!/^\S+@\S+\.\S+$/.test(em)||(kind==='up'&&pw.length<8)){ssay('Enter a valid email and, for a new account, a password of at least 8 characters.');return}
  ssay('Working…');
  const d=await sb(kind==='up'?'/auth/v1/signup':'/auth/v1/token?grant_type=password',{method:'POST',body:JSON.stringify({email:$('#se').value.trim(),password:$('#sp').value})},false);
  if(!d||!d.access_token){ssay('Account created. Check your email to confirm it, then sign in.');return}
  setAU(d);syUI();await syncNow();
 }catch(e){ssay('Failed: '+e.message)}
}
$('#by').onclick=()=>{syUI();$('#sm').hidden=false};
$('#sx').onclick=()=>{$('#sm').hidden=true};
$('#si').onclick=()=>doAuth('in');$('#su').onclick=()=>doAuth('up');
$('#sn').onclick=syncNow;
$('#so').onclick=async()=>{const t=AU;AU=null;try{localStorage.removeItem('scriptpad-auth')}catch(e){}syUI();ssay('Signed out. Your scripts stay on this device.');if(t&&sbOn()){try{await fetch(BASE+'/auth/v1/logout',{method:'POST',headers:{apikey:CFG.supabaseKey,Authorization:'Bearer '+t.access_token}})}catch(e){}}};
window.addEventListener('online',()=>{if(AU&&sbOn())syncNow()});
setTimeout(()=>{if(AU&&sbOn())syncNow()},600);
function stamp(){try{localStorage.setItem('scriptpad-bk',Date.now())}catch(e){}}
function withContd(){
 const out=[];let last=null;
 cur().blocks.forEach(b=>{
  if(!b.x.trim())return;
  if(b.t==='scene')last=null;
  let x=b.x.trim();
  if(b.t==='character'){const n=nameOf(x);if(n===last&&!/CONT/i.test(x))x+=" (CONT'D)";last=n}
  out.push({t:b.t,x});
 });
 return out;
}
function renameUI(b){
 const g=$('#sg'),old=nameOf(b.x);g.innerHTML='';
 const i=document.createElement('input'),ok=document.createElement('button');
 i.value=old;i.setAttribute('aria-label','New name');
 i.style.cssText='flex:1;min-width:0;font:inherit;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:4px 8px';
 ok.textContent='Rename all';
 ok.onclick=()=>{
  const nw=i.value.trim().toUpperCase();
  if(!nw||nw===old){sug();return}
  const re=new RegExp('\\b'+old.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'\\b','g');
  cur().blocks.forEach(x=>{
   if(x.t==='character'&&nameOf(x.x)===old)x.x=nw+x.x.trim().slice(old.length);
   else if(x.t==='action')x.x=x.x.replace(re,nw);
  });
  render();save();say('Renamed '+old+' to '+nw);
 };
 g.append(i,ok);i.focus();i.select();
}
function pdf(){
 const s=cur(),d=new MiniPDF();
 const C={scene:[108,60],action:[108,60],character:[266,30],paren:[223,25],dialogue:[180,35],trans:[540,15]};
 const wrap=(v,n)=>{const o=[];String(v).split('\n').forEach(p=>{let l='';p.split(' ').forEach(w=>{if(l&&(l+' '+w).length>n){o.push(l);l=w}else l=l?l+' '+w:w});o.push(l)});return o};
 if(s.title||s.author){
  d.text((s.title||'').toUpperCase(),306,300,{align:'center'});
  if(s.author){d.text('Written by',306,348,{align:'center'});d.text(s.author,306,372,{align:'center'})}
  d.addPage();
 }
 let pg=1,ln=0,cue='';
 const put=(txt,t,y)=>d.text(txt,C[t][0],72+(y+1)*12-3,t==='trans'?{align:'right'}:undefined);
 const next=()=>{d.addPage();pg++;ln=0;d.text(pg+'.',540,40,{align:'right'})};
 const it=withContd();
 it.forEach((b,i)=>{
  const t=b.t,L=wrap(['scene','character','trans'].includes(t)?b.x.toUpperCase():b.x,C[t][1]);
  if(t==='character')cue=b.x;
  const pv=it[i-1],tight=(t==='dialogue'||t==='paren')&&pv&&['character','paren','dialogue'].includes(pv.t);
  let gap=ln&&!tight?1:0;
  const nx=it[i+1],need=gap+L.length+((t==='scene'||t==='character')&&nx?Math.min(2,wrap(nx.x,C[nx.t][1]).length):0);
  if(ln+need>54&&ln>0){
   const fit=54-ln-gap-1;
   if(t==='dialogue'&&fit>=2&&L.length-fit>=2){
    L.slice(0,fit).forEach((l,k)=>put(l,t,ln+gap+k));
    put('(MORE)',t,ln+gap+fit);
    next();put(nameOf(cue)+" (CONT'D)",'character',0);ln=1;
    L.slice(fit).forEach(l=>{put(l,t,ln);ln++});
    return;
   }
   next();gap=0;
  }
  ln+=gap;L.forEach(l=>{put(l,t,ln);ln++});
 });
 d.save((s.title||'script').replace(/[^\w-]+/g,'_')+'.pdf');stamp();say('PDF created');
}
function dl(name,txt){
 try{const a=document.createElement('a');a.href=objUrl(new Blob([txt],{type:'text/plain'}));a.download=name;document.body.appendChild(a);a.click();a.remove();stamp();say('Download requested')}
 catch(e){say('Download blocked – copy instead')}
}
$('#mp').onclick=pdf;
$('#mdl').onclick=()=>{const v=$('#mt').value;dl(v.trim().startsWith('{')?'scriptpad-backup.json':(cur().title||'script').replace(/[^\w-]+/g,'_')+'.fountain',v)};
$('#mk').onclick=()=>{$('#mt').value=JSON.stringify(S,null,1);stamp();say('Backup ready – copy or download it')};
$('#mr').onclick=()=>{
 try{
  if($('#mt').value.length>5e6)throw 0;
  const p=JSON.parse($('#mt').value);
  if(!Array.isArray(p.scripts))throw 0;
  const okS=p.scripts.map(cleanScript).filter(Boolean);if(!okS.length)throw 0;
  okS.forEach(n=>{const k=S.scripts.findIndex(x=>x.id===n.id);if(k<0)S.scripts.push(n);else S.scripts[k]=n});
  act=0;$('#md').hidden=true;render();save();say('Backup restored');
 }catch(e){say('That is not a valid backup')}
};
const root=document.documentElement;
try{const th=localStorage.getItem('scriptpad-theme');if(th)root.dataset.theme=th}catch(e){}
$('#bt').onclick=()=>{
 const dark=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;
 const m=dark?'light':'dark';root.dataset.theme=m;
 try{localStorage.setItem('scriptpad-theme',m)}catch(e){}
};
try{navigator.storage&&navigator.storage.persist&&navigator.storage.persist()}catch(e){}
$('#bp').onclick=()=>{try{window.print()}catch(e){say('Print blocked – use your browser menu')}};
$('#bd').onclick=()=>{
 const b=$('#bd');
 if(b.textContent!=='Delete'){
  clearTimeout(delT);b.textContent='Delete';
  (S.dead=S.dead||[]).push({id:S.cur,u:Date.now()});S.scripts=S.scripts.filter(s=>s.id!==S.cur);
  if(!S.scripts.length)S.scripts.push(fresh(false));
  S.cur=S.scripts[0].id;act=0;render();save();return;
 }
 b.textContent='Tap again to delete';
 delT=setTimeout(()=>{b.textContent='Delete'},3000);
};
const mn=$('#mn'),mnb=$('#mnb');
function menu(o){mn.hidden=!o;mnb.setAttribute('aria-expanded',String(o))}
mnb.onclick=e=>{e.stopPropagation();menu(mn.hidden)};
document.addEventListener('click',e=>{if(!mn.hidden&&!mn.contains(e.target)&&e.target!==mnb)menu(false)});
mn.addEventListener('click',e=>{const b=e.target.closest('button');if(b&&!['bd','bt'].includes(b.id))menu(false)});
$('#sel').addEventListener('change',()=>menu(false));
window.addEventListener('keydown',e=>{if(e.key==='Escape')menu(false)});
try{if(!localStorage.getItem('scriptpad-tip'))$('#tip').hidden=false}catch(e){}
$('#tipx').onclick=()=>{$('#tip').hidden=true;try{localStorage.setItem('scriptpad-tip','1')}catch(e){}};
if(matchMedia('(display-mode: standalone)').matches||navigator.standalone)$('#bi').hidden=true;
window.addEventListener('resize',()=>document.querySelectorAll('#ed textarea').forEach(fit));
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(()=>document.querySelectorAll('#ed textarea').forEach(fit));
try{
 if(!localStorage.getItem('scriptpad-bk'))stamp();
 if(Date.now()-(+localStorage.getItem('scriptpad-bk')||0)>12096e5)setTimeout(()=>say('Tip: Fountain → Backup all'),800);
}catch(e){}
render();
function snapUI(){
 const sel=$('#vs'),sn=cur().snaps||[];
 sel.innerHTML='<option value="">Restore a version…</option>';
 sn.forEach((v,i)=>{const o=document.createElement('option');o.value=i;o.textContent=v.name+' · '+new Date(v.t).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});sel.appendChild(o)});
}
function addSnap(name){const s=cur();s.snaps=s.snaps||[];s.snaps.unshift({t:Date.now(),name,blocks:JSON.parse(JSON.stringify(s.blocks))});s.snaps=s.snaps.slice(0,15)}
$('#bv').onclick=()=>{const s=cur();s.sn=(s.sn||0)+1;addSnap('Draft '+s.sn);save();snapUI();say('Version saved')};
$('#vs').onchange=e=>{
 const v=(cur().snaps||[])[+e.target.value];if(!v)return;
 commit();addSnap('Before restore');
 cur().blocks=JSON.parse(JSON.stringify(v.blocks));act=0;render();save();say('Restored '+v.name);
};
if('serviceWorker' in navigator)addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}));

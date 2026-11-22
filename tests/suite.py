import sys, os, json, subprocess, time, atexit, urllib.request, re, shutil, tempfile
from playwright.sync_api import sync_playwright
URL=os.environ.get('URL','http://localhost:8765/')
HERE=os.path.dirname(os.path.abspath(__file__))
srv=subprocess.Popen([sys.executable,os.path.join(HERE,'mock_supabase.py'),'8766']); atexit.register(srv.terminate); time.sleep(1)
R=[]
CSPJS="window.__csp=[];document.addEventListener('securitypolicyviolation',e=>window.__csp.push(e.violatedDirective+' '+e.blockedURI))"
def ok(name,cond,info=''):
    R.append((name,bool(cond),info)); print(('PASS ' if cond else 'FAIL ')+name+('' if cond else '  -> '+str(info)))
STUB="""
window.__pdf={pages:1,calls:[],fonts:[],saved:null};
window.jspdf={jsPDF:class{constructor(o){window.__pdf.opts=o}
 setFont(f,s){window.__pdf.fonts.push(f)} setFontSize(){}
 text(t,x,y,o){window.__pdf.calls.push({t,x,y,p:window.__pdf.pages,al:o&&o.align})}
 addPage(){window.__pdf.pages++} save(n){window.__pdf.saved=n}}};
"""
MENU=('#bn','#bc','#bt','#bi','#bd','#bp','#aut')
def mclick(pg,sel):
    if not pg.is_visible('#mn'): pg.click('#mnb')
    pg.click(sel)
def mfill(pg,sel,v):
    if not pg.is_visible('#mn'): pg.click('#mnb')
    pg.fill(sel,v)
def blocks(pg): return pg.evaluate("cur().blocks.map(b=>[b.t,b.x])")
def vals(pg): return pg.evaluate("[...document.querySelectorAll('#ed textarea')].map(t=>[t.className,t.value])")
def fresh(pg):
    mclick(pg,'#bn'); pg.wait_for_timeout(100)
with sync_playwright() as p:
    b=p.chromium.launch(); c=b.new_context(viewport={'width':1100,'height':800})
    c.add_init_script(CSPJS); pg=c.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(1200)
    ok('A1 loads with seed script (6 blocks)', len(blocks(pg))==6, blocks(pg))
    ok('A2 no JS page errors', not errs, errs)
    # B: typing flow
    fresh(pg)
    k=pg.keyboard
    k.type('int. kitchen - day'); 
    ok('B1 scene typed',blocks(pg)[0]==['scene','int. kitchen - day'],blocks(pg))
    k.press('Enter'); k.type('Meera enters.')
    ok('B2 Enter after scene -> action',blocks(pg)[1][0]=='action',blocks(pg))
    k.press('Enter'); k.press('Alt+3'); k.type('meera'); k.press('Enter'); k.type('Hello there.')
    ok('B3 character->dialogue',[x[0] for x in blocks(pg)][-2:]==['character','dialogue'],blocks(pg))
    k.press('Enter'); ok('B4 dialogue Enter -> character',blocks(pg)[-1][0]=='character',blocks(pg))
    k.type('RAVI'); k.press('Enter'); k.type('Hi.')
    k.press('Enter'); k.type('MEERA'); k.press('Enter'); k.type('Again.')
    k.press('Enter'); k.press('Alt+2'); k.type('She sighs.')
    k.press('Enter'); k.press('Alt+3'); k.type('MEERA'); k.press('Enter'); k.type('More.')
    k.press('Enter'); k.press('Alt+3'); k.type('MEERA'); k.press('Enter'); k.type('Without action between.')
    pg.wait_for_timeout(200)
    v=vals(pg); cues=[x[1] for x in v if x[0]=='character']
    print('   editor cues:',cues)
    ok('B5 CONT\'D visible in editor for repeat speaker after action', any("CONT'D" in c.upper() for c in cues), cues)
    ok('B6 no CONT\'D when RAVI spoke between (2nd MEERA cue plain)', cues[2].strip().upper()=='MEERA', cues)
    ftn=pg.evaluate("fountain()")
    print('   fountain:\n'+ftn)
    ok('B7 fountain has CONT\'D on repeat cue', "MEERA (CONT'D)" in ftn, '')
    ok('B8 fountain scene uppercase', 'INT. KITCHEN - DAY' in ftn)
    # C auto scene
    k.press('Enter'); k.press('Alt+2'); k.type('ext. park - night')
    ok('C1 action starting EXT. converts to scene',blocks(pg)[-1][0]=='scene',blocks(pg)[-1])
    # D backspace / arrows
    n=len(blocks(pg)); k.press('Enter'); ok('D0 Enter on scene -> action',blocks(pg)[-1][0]=='action')
    k.press('Backspace'); ok('D1 Backspace on empty block deletes it',len(blocks(pg))==n,len(blocks(pg)))
    k.press('Enter'); k.press('Enter')
    ok('D2 Enter on empty non-action turns to action (not new block)', blocks(pg)[-1][0]=='action')
    k.press('ArrowUp'); ok('D3 ArrowUp moves focus', pg.evaluate("document.activeElement.dataset.i||[...document.querySelectorAll('#ed textarea')].indexOf(document.activeElement)")!=len(blocks(pg))-1)
    # E chips
    cuei=[i for i,x in enumerate(blocks(pg)) if x[0]=='character'][0]
    pg.click(f'#ed textarea:nth-child({cuei+1})'); pg.wait_for_timeout(100)
    chips=pg.evaluate("[...document.querySelectorAll('#sg button')].map(b=>b.textContent)")
    print('   chips on character:',chips)
    ok('E1 V.O./O.S./Rename chips on character', '(V.O.)' in chips and 'Rename all' in chips, chips)
    pg.click("#sg button:has-text('(V.O.)')"); 
    ok('E2 V.O. chip appends', 'V.O.' in blocks(pg)[cuei][1], blocks(pg)[cuei])
    # rename
    pg.click("#sg button:has-text('Rename all')"); pg.fill('#sg input','Meera Devi'.upper()); pg.click("#sg button:has-text('Rename all')"); pg.wait_for_timeout(150)
    names=[x[1] for x in blocks(pg) if x[0]=='character']
    print('   after rename:',names)
    ok('E3 rename changes every MEERA cue', all('MEERA' not in n.upper().split(' (')[0] or 'MEERA DEVI' in n.upper() for n in names) and any('MEERA DEVI' in n.upper() for n in names), names)
    pg.evaluate("cur().blocks.push({t:'action',x:'ZORRO runs. ZORRO jumps.'});render()"); pg.click('#ed textarea:nth-child(1)')
    zi=[i for i,x in enumerate(blocks(pg)) if x[0]=='character'][1]
    pg.evaluate("cur().blocks.push({t:'character',x:'ZORRO'});render()"); zi=len(blocks(pg))-1; pg.click(f'#ed textarea:nth-child({zi+1})'); pg.click("#sg button:has-text('Rename all')"); pg.fill('#sg input','EL ZORRO'); pg.click("#sg button:has-text('Rename all')"); pg.wait_for_timeout(150)
    ok('E4 rename also replaces uppercase mentions in action text', 'EL ZORRO runs. EL ZORRO jumps.' in [x[1] for x in blocks(pg)], [x[1] for x in blocks(pg) if x[0]=='action'])
    ok('E5 rename box triggers no security-policy violation (no inline styles)', pg.evaluate('window.__csp')==[], pg.evaluate('window.__csp'))
    # scenes jump
    opts=pg.evaluate("[...document.querySelectorAll('#sc option')].map(o=>[o.textContent,o.parentElement.label||''])")
    print('   jump menu:',opts)
    ok('F1 jump menu lists scenes and characters', any(g=='Scenes' for _,g in opts) and any(g=='Characters' for _,g in opts), opts)
    pg.select_option('#sc', index=1); pg.wait_for_timeout(100)
    ok('F2 jump focuses a textarea', pg.evaluate("document.activeElement.tagName")=='TEXTAREA')
    # G persistence
    pg.wait_for_timeout(500); before=blocks(pg); pg.reload(); pg.wait_for_timeout(800)
    ok('G1 persists across reload', blocks(pg)==before, '')
    # H new/delete
    ns=pg.evaluate("S.scripts.length"); mclick(pg,'#bn'); ok('H1 new script',pg.evaluate("S.scripts.length")==ns+1)
    mclick(pg,'#bd'); t1=pg.inner_text('#bd'); mclick(pg,'#bd'); ok('H2 delete two-tap',pg.evaluate("S.scripts.length")==ns and 'Tap' in t1,t1)
    # I theme
    mclick(pg,'#bt'); t=pg.evaluate("document.documentElement.dataset.theme"); mclick(pg,'#bt'); t2=pg.evaluate("document.documentElement.dataset.theme")
    ok('I1 theme toggles', t!=t2 and t in('dark','light'), (t,t2))
    # J fountain modal round trip
    mclick(pg,'#bc'); ft=pg.input_value('#mt'); ok('J1 modal opens with text', len(ft)>20 and pg.is_visible('#md'))
    before=blocks(pg); pg.click('#mi'); pg.wait_for_timeout(200)
    after=blocks(pg)
    print('   import round trip types:',[x[0] for x in after][:12])
    ok('J2 import round-trip keeps block types', [x[0] for x in before if x[1].strip()]==[x[0] for x in after if x[1].strip()], ([x[0] for x in before],[x[0] for x in after]))
    ok('J3 import creates an extra script with the exported title', pg.evaluate("cur().title")==ft.split(chr(10))[0].replace('Title: ','') and pg.evaluate("S.scripts.length")>=2, pg.evaluate("cur().title"))
    mclick(pg,'#bc'); pg.click('#mk'); js=pg.input_value('#mt'); ok('J4 backup JSON valid', json.loads(js)['scripts'])
    n0=pg.evaluate("S.scripts.length"); pg.evaluate("S.scripts.pop()"); pg.fill('#mt',js); pg.click('#mr'); pg.wait_for_timeout(150)
    ok('J5 restore merges scripts back', pg.evaluate("S.scripts.length")==n0, (n0,pg.evaluate("S.scripts.length")))
    mclick(pg,'#bc'); pg.keyboard.press('Escape'); ok('J6 Escape closes modal', not pg.is_visible('#md'))
    # K stats
    ok('K1 stats shows words/pages','words' in pg.inner_text('#wc'), pg.inner_text('#wc'))
    # PDF logic via stub
    mclick(pg,'#bn'); pg.fill('#ttl','Test Script'); mfill(pg,'#aut','G')
    pg.evaluate("""cur().blocks=[{t:'scene',x:'INT. ROOM - DAY'},{t:'character',x:'MEERA'},{t:'dialogue',x:('word '.repeat(700)).trim()}];render()""")
    mclick(pg,'#bc')
    with pg.expect_download() as dl: pg.click('#mp')
    path=dl.value.path(); data=open(path,'rb').read()
    from pypdf import PdfReader
    pages=[x.extract_text() for x in PdfReader(path).pages]; texts='\n'.join(pages)
    print('   pdf pages',len(pages))
    ok('L1 real PDF downloads, parses, cover has title', data[:5]==b'%PDF-' and 'TEST SCRIPT' in pages[0] and dl.value.suggested_filename=='Test_Script.pdf', (data[:8],pages[:1]))
    ok("L2 long dialogue splits with (MORE) and CONT'D", '(MORE)' in texts and "(CONT'D)" in texts)
    ok('L3 page numbers start on script page 2', len(pages)>=3 and '2.' in pages[2] and not pages[1].strip().startswith('1.'))
    ok('L4 no empty or garbled pages', all(len(p.strip())>20 for p in pages))
    ok('L5 PDF export triggers no security-policy violation', pg.evaluate('window.__csp')==[], pg.evaluate('window.__csp'))
    pg.keyboard.press('Escape')
    # print css
    pg.emulate_media(media='print'); ok('M1 print hides chrome, shows cover', not pg.is_visible('header') and pg.evaluate("getComputedStyle(document.querySelector('#cover')).display")=='block'); pg.emulate_media(media='screen')
    # offline
    c.set_offline(True); pg.reload(); pg.wait_for_timeout(800); ok('N1 loads offline via service worker', pg.evaluate("typeof S")=='object' and len(vals(pg))>0); c.set_offline(False)

    # ---- extra: CONT'D details, install, mobile ----
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(600); fresh(pg)
    pg.evaluate("""cur().blocks=[{t:'scene',x:'INT. A - DAY'},{t:'character',x:'ANU'},{t:'dialogue',x:'One.'},{t:'action',x:'Beat.'},{t:'character',x:'ANU'},{t:'dialogue',x:'Two.'},{t:'character',x:'BOB'},{t:'dialogue',x:'Three.'},{t:'scene',x:'INT. B - DAY'},{t:'character',x:'BOB'},{t:'dialogue',x:'Four.'}];render()""")
    cues=[x[1] for x in vals(pg) if x[0]=='character']; print('   cues:',cues)
    ok("P1 CONT'D only on same speaker continuing (ANU 2nd), not after BOB/new scene", cues==['ANU',"ANU (CONT'D)",'BOB','BOB'], cues)
    pg.evaluate("cur().blocks.splice(6,2)"); pg.evaluate("render()")
    cues=[x[1] for x in vals(pg) if x[0]=='character']
    ok("P2 CONT'D removed/recomputed when sequence changes", cues[:2]==['ANU',"ANU (CONT'D)"] , cues)
    pg.evaluate("cur().blocks.splice(3,1)"); pg.evaluate("render()")
    pg.wait_for_timeout(500); pg.reload(); pg.wait_for_timeout(600)
    ok("P4 CONT'D persists after reload", any("CONT'D" in x[1] for x in vals(pg) if x[0]=='character'), vals(pg))
    ftn=pg.evaluate("fountain()"); ok("P5 CONT'D not doubled in export", ftn.count("CONT'D")==ftn.count("(CONT'D)") and "(CONT'D) (CONT'D)" not in ftn, ftn)
    # typing live: second cue gets CONT'D after leaving it
    fresh(pg); k=pg.keyboard
    k.type('INT. X - DAY'); k.press('Enter'); k.press('Alt+3'); k.type('ZED'); k.press('Enter'); k.type('a'); k.press('Enter'); k.press('Alt+2'); k.type('b'); k.press('Enter'); k.press('Alt+3'); k.type('ZED'); k.press('Enter'); pg.wait_for_timeout(100)
    cues=[x[1] for x in vals(pg) if x[0]=='character']; ok("P6 live typing: CONT'D appears right after pressing Enter on the cue", cues==['ZED',"ZED (CONT'D)"], cues)
    # install UI
    mclick(pg,'#bi'); pg.wait_for_timeout(500); t=pg.input_value('#mt'); print('   '+t.replace('\n','\n   '))
    ok('Q1 install help shows manifest loaded + worker active', 'Manifest: loaded' in t and 'Offline worker: active' in t and 'Secure (https) page: yes' in t, t)
    pg.keyboard.press('Escape')
    cdp=c.new_cdp_session(pg); ie=cdp.send('Page.getInstallabilityErrors')['installabilityErrors']; ok('Q2 Chrome reports no installability errors', ie==[], ie)
    mf=pg.evaluate("fetch('manifest.webmanifest').then(r=>r.json())"); ok('Q3 manifest has 192+512 png, standalone', mf['display']=='standalone' and {i['sizes'] for i in mf['icons']}>={'192x192','512x512'}, mf)
    ok('Q4 icons reachable', all(pg.evaluate("u=>fetch(u).then(r=>r.status)",i['src'])==200 for i in mf['icons']))
    # mobile
    m=b.new_context(viewport={'width':390,'height':780},has_touch=True,is_mobile=True); mp=m.new_page(); mp.goto(URL); mp.wait_for_timeout(800)
    mp.click('#ed textarea:nth-child(2)'); mp.click('#tb button[data-t=character]'); ok('R1 mobile toolbar changes type', blocks(mp)[1][0]=='character', blocks(mp)[1])
    sw=mp.evaluate("document.documentElement.scrollWidth<=window.innerWidth+1"); ok('R2 no horizontal page scroll on phone', sw)
    mclick(mp,'#bi'); mp.wait_for_timeout(400); ok('R3 install help opens on phone', mp.is_visible('#md'))

    # ---- undo / redo ----
    fresh(pg); k=pg.keyboard
    k.type('INT. U - DAY'); pg.wait_for_timeout(900); k.press('Enter'); k.type('hello world'); pg.wait_for_timeout(900)
    k.press('Control+z'); pg.wait_for_timeout(200)
    ok('U1 Ctrl+Z undoes the last typed text', blocks(pg)[1][1]=='', blocks(pg))
    k.press('Control+Shift+z'); pg.wait_for_timeout(200)
    ok('U2 Ctrl+Shift+Z redoes it', blocks(pg)[1][1]=='hello world', blocks(pg))
    n=len(blocks(pg)); k.press('Enter'); k.press('Backspace'); pg.wait_for_timeout(100)
    k.press('Control+z'); pg.wait_for_timeout(200)
    ok('U3 undo restores a deleted block', len(blocks(pg))==n+1, (n,len(blocks(pg))))
    pg.click('#bu'); pg.wait_for_timeout(150)
    ok('U4 header undo button works', len(blocks(pg))==n, (n,len(blocks(pg))))
    # ---- outline + focus ----
    pg.evaluate("cur().blocks=[{t:'scene',x:'INT. A - DAY'},{t:'action',x:'First scene action.'},{t:'scene',x:'INT. B - DAY'},{t:'action',x:'Second.'},{t:'scene',x:'INT. C - NIGHT'}];render()")
    mclick(pg,'#bo'); pg.wait_for_timeout(100)
    ok('O1 outline lists 3 scene cards', pg.evaluate("document.querySelectorAll('#ol .card').length")==3)
    ok('O5 outline panel triggers no security-policy violation (no inline styles)', pg.evaluate('window.__csp')==[], pg.evaluate('window.__csp'))
    pg.click('#ol .card:nth-of-type(1) button:nth-of-type(2)'); pg.wait_for_timeout(100)
    ok('O2 moving a scene down moves its action with it', [x[1] for x in blocks(pg) if x[0]=='scene']==['INT. B - DAY','INT. A - DAY','INT. C - NIGHT'] and blocks(pg)[1][1]=='Second.', blocks(pg))
    pg.click('#ol .card:nth-of-type(3)'); ok('O3 clicking a card focuses that scene', pg.evaluate("document.activeElement.value")=='INT. C - NIGHT')
    mclick(pg,'#bo'); ok('O4 outline toggles closed', not pg.is_visible('#ol'))
    mclick(pg,'#bf'); ok('F1 focus mode hides header and shows exit button', not pg.is_visible('header') and pg.is_visible('#fx'))
    pg.keyboard.press('Escape'); ok('F2 Escape exits focus mode', pg.is_visible('header'))
    # ---- cloud sync against a mock Supabase ----
    # test copy of the site whose CSP also allows the mock sync server (the real CSP only allows *.supabase.co)
    site0=os.path.join(tempfile.mkdtemp(),'site'); shutil.copytree(os.path.join(HERE,'..'),site0,ignore=shutil.ignore_patterns('tests','.git','.github'))
    ix=os.path.join(site0,'index.html'); html0=open(ix).read().replace("connect-src 'self'","connect-src 'self' http://127.0.0.1:8766"); open(ix,'w').write(html0)
    s3=subprocess.Popen([sys.executable,'-m','http.server','8768','-d',site0],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); atexit.register(s3.terminate); time.sleep(1); SYNCURL='http://localhost:8768/'
    def jr(): return json.load(urllib.request.urlopen('http://127.0.0.1:8766/_rows'))
    CFGJS="window.SCRIPTPAD={supabaseUrl:'http://127.0.0.1:8766',supabaseKey:'k'};"
    def dev():
        cx=b.new_context(viewport={'width':1100,'height':800},service_workers='block'); cx.add_init_script(CSPJS); cx.route('**/config.js',lambda r:r.fulfill(body=CFGJS,content_type='application/javascript'))
        q=cx.new_page(); q.goto(SYNCURL); q.wait_for_timeout(700); return q
    def login(q,kind,em='g@test.dev',pw='secret12'):
        mclick(q,'#by'); q.fill('#se',em); q.fill('#sp',pw); q.click('#si' if kind=='in' else '#su'); q.wait_for_timeout(900)
    mclick(pg,'#by'); ok('S0 without config the sync panel explains setup', 'not set up' in pg.inner_text('#ss')); pg.keyboard.press('Escape')
    A=dev(); A.evaluate("cur().title='Cloud Test';cur().blocks=[{t:'scene',x:'INT. CLOUD - DAY'},{t:'action',x:'From device A.'}];render();save()")
    login(A,'up'); rows=jr(); titles=[r['data']['title'] for r in rows if not r['deleted']]
    ok('S1 account created and edited script uploaded', A.evaluate("!!AU") and 'Cloud Test' in titles, titles)
    ok('S2 untouched sample script is not uploaded', 'My First Screenplay' not in titles, titles)
    B=dev(); login(B,'in')
    ok('S3 second device signs in and downloads the script', 'Cloud Test' in B.evaluate("S.scripts.map(s=>s.title)"), B.evaluate("S.scripts.map(s=>s.title)"))
    B.evaluate("S.cur=S.scripts.find(s=>s.title==='Cloud Test').id;render();cur().blocks[1].x='Edited on B';save()"); B.wait_for_timeout(500); B.click('#sn'); B.wait_for_timeout(700)
    A.click('#sn'); A.wait_for_timeout(700)
    ok('S4 edit on device B arrives on device A', A.evaluate("cur().blocks[1].x")=='Edited on B', A.evaluate("cur().blocks[1].x"))
    A.click('#sx'); mclick(A,'#bd'); mclick(A,'#bd'); A.wait_for_timeout(500); mclick(A,'#by'); A.click('#sn'); A.wait_for_timeout(700)
    B.click('#sn'); B.wait_for_timeout(700)
    ok('S5 deleting on A removes it on B', 'Cloud Test' not in B.evaluate("S.scripts.map(s=>s.title)"), B.evaluate("S.scripts.map(s=>s.title)"))
    C=dev(); login(C,'in',pw='wrong'); ok('S6 wrong password shows an error', 'Failed' in C.inner_text('#ss') and not C.evaluate("!!AU"), C.inner_text('#ss'))
    A.context.set_offline(True); A.click('#sn'); A.wait_for_timeout(500)
    ok('S7 offline sync fails gracefully and keeps local data', 'Sync failed' in A.inner_text('#ss') and A.evaluate("S.scripts.length")>=1, A.inner_text('#ss'))
    A.context.set_offline(False)
    ok('S9 sync devices trigger no security-policy violation', A.evaluate('window.__csp')==[] and B.evaluate('window.__csp')==[], (A.evaluate('window.__csp'),B.evaluate('window.__csp')))
    ok('S8 service worker never caches Supabase calls', "(rest|auth)" in open(os.path.join(HERE,'..','sw.js')).read())

    # ---- security hardening ----
    PAY="<img src=x onerror=window.__x=1><script>window.__x=1</script>"
    pg.evaluate("p=>{cur().title=p;cur().blocks=[{t:'scene',x:p},{t:'action',x:p},{t:'character',x:p},{t:'dialogue',x:p}];render();save()}",PAY)
    mclick(pg,'#bv'); mclick(pg,'#bo'); pg.wait_for_timeout(200)
    ok('X1 script text containing HTML never becomes page elements', pg.evaluate("document.querySelectorAll('#ed img,#ol img,#sc img,#vs img,#sg img,header img,#ol script').length")==0 and pg.evaluate("window.__x")is None and pg.input_value('#ttl')==PAY)
    mclick(pg,'#bo')
    mclick(pg,'#bc'); pg.fill('#mt',json.dumps({"scripts":[{"id":99,"title":"<b>x</b>","blocks":[{"t":"__proto__","x":"hi"},{"t":"scene","x":5},None,{"t":"character","x":"a"}]},{"id":"bad","blocks":[]},{"id":100,"blocks":"nope"}],"cur":99})); pg.click('#mr'); pg.wait_for_timeout(200)
    sc=pg.evaluate("S.scripts.find(s=>s.id===99)")
    ok('X2 restored backup is sanitised (bad types fixed, invalid scripts dropped)', sc and all(b['t'] in ['scene','action','character','paren','dialogue','trans'] and isinstance(b['x'],str) for b in sc['blocks']) and not pg.evaluate("S.scripts.some(s=>s.id===100||s.id==='bad')"), sc)
    for raw in ['{broken','{"scripts":[{"id":"x","blocks":"no"}]}']:
        c3=b.new_context(service_workers='block'); q=c3.new_page(); q.goto(URL); q.wait_for_timeout(500); q.evaluate("r=>localStorage.setItem('scriptpad1',r)",raw); q.reload(); q.wait_for_timeout(700)
        ok('X3 corrupt saved data ('+raw[:12]+') does not break the app and is kept aside', q.evaluate("cur().blocks.length")>0 and q.evaluate("localStorage.getItem('scriptpad1-corrupt')")==raw)
        c3.close()
    def post(path,tok,body):
        rq=urllib.request.Request('http://127.0.0.1:8766'+path,data=json.dumps(body).encode(),headers={'Authorization':'Bearer tok-'+tok,'Content-Type':'application/json'},method='POST'); urllib.request.urlopen(rq).read()
    now=time.strftime('%Y-%m-%dT%H:%M:%S.000Z',time.gmtime())
    post('/rest/v1/scripts?on_conflict=user_id,id','evil@t.dev',[{'id':555,'data':{'id':1,'title':PAY,'blocks':[{'t':'weird','x':'ok'}]},'updated_at':now,'deleted':False},{'id':556,'data':'garbage','updated_at':now,'deleted':False},{'id':557,'data':{'blocks':'x'},'updated_at':now,'deleted':False}])
    D=dev(); login(D,'up',em='evil@t.dev')
    got=D.evaluate("S.scripts.map(s=>[s.id,s.blocks[0].t])")
    ok('X4 malicious cloud rows are sanitised or ignored', [555,'action'] in got and not any(g[0] in (556,557) for g in got) and D.evaluate("document.querySelectorAll('img').length")==0 and D.evaluate("window.__x")is None, got)
    E=dev(); login(E,'up',em='short@t.dev',pw='abc12'); ok('X5 short passwords are refused before any request', 'at least 8' in E.inner_text('#ss') and not E.evaluate("!!AU"), E.inner_text('#ss'))
    A.click('#so'); A.wait_for_timeout(500); lg=json.load(urllib.request.urlopen('http://127.0.0.1:8766/_log'))
    ok('X6 sign-out also revokes the session on the server', any(x.startswith('logout') for x in lg) and not A.evaluate("!!AU"), lg)
    B.evaluate("AU.expires_at=1;AU.refresh_token='junk'"); B.click('#sn'); B.wait_for_timeout(700)
    ok('X7 a dead session signs you out cleanly instead of failing silently', 'sign in again' in B.inner_text('#ss').lower() and not B.evaluate("!!AU"), B.inner_text('#ss'))
    cb=b.new_context(service_workers='block'); cb.route('**/config.js',lambda r:r.fulfill(body="window.SCRIPTPAD={supabaseUrl:'http://evil.example',supabaseKey:'k'};",content_type='application/javascript')); q=cb.new_page(); hits=[]; q.on('request',lambda r:hits.append(r.url) if 'evil.example' in r.url else None)
    q.goto(URL); q.wait_for_timeout(600); q.evaluate("syncNow()"); q.wait_for_timeout(300)
    ok('X8 a non-HTTPS Supabase address is refused and never contacted', q.evaluate("sbOn()")==False and not hits, hits)
    mclick(pg,'#bc'); pg.evaluate("document.querySelector('#mt').value='x'.repeat(2100000)"); pg.click('#mi'); pg.wait_for_timeout(200)
    ok('X9 oversized import is refused', 'too large' in pg.evaluate("document.querySelector('#toast').textContent"), pg.evaluate("document.querySelector('#toast').textContent")); pg.keyboard.press('Escape')
    pg.evaluate("cur().blocks=[{t:'scene',x:'INT. X - DAY'},{t:'character',x:'A'},{t:'dialogue',x:'evil) Tj ET (x\\\\y'}];render()")
    mclick(pg,'#bc')
    with pg.expect_download() as dl2: pg.click('#mp')
    from pypdf import PdfReader as PR
    t2='\n'.join(x.extract_text() for x in PR(dl2.value.path()).pages)
    ok('X10 text with PDF syntax characters stays plain text in the PDF', 'evil) Tj ET (x' in t2 and 'y' in t2.split('(x')[1][:3], t2[:200]); pg.keyboard.press('Escape')
    hd=open(os.path.join(HERE,'..','_headers')).read(); ix=open(os.path.join(HERE,'..','index.html')).read(); sq=open(os.path.join(HERE,'..','supabase.sql')).read(); wf=open(os.path.join(HERE,'..','.github','workflows','test.yml')).read()
    ok('X11 headers, referrer policy, locked-down database and CI permissions are in place', all(k in hd for k in ('frame-ancestors',"Permissions-Policy",'nosniff')) and 'name="referrer"' in ix and 'revoke all on public.scripts from anon' in sq and 'contents: read' in wf)

    # ---- version snapshots ----
    fresh(pg)
    pg.evaluate("cur().blocks=[{t:'scene',x:'INT. V - DAY'},{t:'action',x:'Original.'}];render()")
    mclick(pg,'#bv'); pg.wait_for_timeout(150)
    pg.evaluate("cur().blocks[1].x='Changed.';render();save()"); pg.wait_for_timeout(300)
    opts=pg.evaluate("[...document.querySelectorAll('#vs option')].map(o=>o.textContent)")
    ok('V1 Save version adds a named snapshot', len(opts)==2 and opts[1].startswith('Draft 1'), opts)
    pg.evaluate("menu(true)"); pg.select_option('#vs',index=1); pg.evaluate("menu(false)"); pg.wait_for_timeout(200)
    ok('V2 restoring a version brings back that text', blocks(pg)[1][1]=='Original.', blocks(pg))
    opts=pg.evaluate("[...document.querySelectorAll('#vs option')].map(o=>o.textContent)")
    ok('V3 restore keeps a Before restore safety copy', any(o.startswith('Before restore') for o in opts), opts)
    pg.click('#bu'); pg.wait_for_timeout(200)
    ok('V4 undo after a restore returns the changed text', blocks(pg)[1][1]=='Changed.', blocks(pg))
    # ---- repo hygiene ----
    html=open(os.path.join(HERE,'..','index.html')).read()
    refs=re.findall(r'(?:src|href)="([^"]+)"',html)
    ext=[r for r in refs if re.match(r'https?:',r)]; miss=[r for r in refs if not re.match(r'https?:|#|data:',r) and not os.path.exists(os.path.join(HERE,'..',r))]
    ok('T1 page loads only files from the repo (no outside scripts or fonts)', not ext and not miss, (ext,miss))
    ok('T2 Content-Security-Policy present and blocks outside scripts', "default-src 'self'" in html and "script-src 'self'" in html)
    tmp=tempfile.mkdtemp(); site=os.path.join(tmp,'site'); shutil.copytree(os.path.join(HERE,'..'),site,ignore=shutil.ignore_patterns('tests','.git','.github'))
    s2=subprocess.Popen([sys.executable,'-m','http.server','8767','-d',site],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); atexit.register(s2.terminate); time.sleep(1)
    cx=b.new_context(); q=cx.new_page(); q.goto('http://localhost:8767/'); q.wait_for_timeout(1500)
    open(os.path.join(site,'app.js'),'a').write("\nwindow.__marker='v2';")
    q.reload(); q.wait_for_timeout(800)
    ok('T3 a new deploy arrives without bumping any version number', q.evaluate("window.__marker")=='v2')
    cx.set_offline(True); q.reload(); q.wait_for_timeout(800)
    ok('T4 offline still opens the latest cached version', q.evaluate("window.__marker")=='v2' and q.evaluate("typeof S")=='object')

    # ---- character name autocomplete ----
    SEED="""cur().blocks=[{t:'scene',x:'INT. A - DAY'},{t:'character',x:'MEERA'},{t:'dialogue',x:'One.'},{t:'character',x:'RAVI'},{t:'dialogue',x:'Two.'},{t:'character',x:'MEERA'},{t:'dialogue',x:'Three.'},{t:'character',x:'RAVI'},{t:'dialogue',x:'Four.'},{t:'action',x:'ZORRO enters. SUDDENLY he stops.'},{t:'character',x:''}];render()"""
    ITEMS="[...document.querySelectorAll('#ac .ac-i')].map(d=>[d.querySelector('b').textContent,d.querySelector('span').textContent])"
    fresh(pg); k=pg.keyboard; pg.evaluate(SEED); pg.evaluate("focusAt(cur().blocks.length-1,'end')"); pg.wait_for_timeout(200)
    it=pg.evaluate(ITEMS); print('   empty cue suggestions:',it)
    ok('AC1 empty cue pops up the cast, likely next speaker first, names from action included, filler words not', it and it[0]==['MEERA','likely next'] and any(x[0]=='ZORRO' and x[1]=='in action' for x in it) and not any(x[0]=='SUDDENLY' for x in it), it)
    k.type('ra'); pg.wait_for_timeout(100); it=pg.evaluate(ITEMS)
    ok('AC2 typing a few letters narrows the list to matching names', it and it[0][0]=='RAVI' and not any(x[0]=='MEERA' for x in it), it)
    k.press('Tab'); pg.wait_for_timeout(100)
    ok('AC3 Tab completes the name and closes the popup', blocks(pg)[-1]==['character','RAVI'] and not pg.is_visible('#ac'), blocks(pg)[-1])
    k.press('Control+a'); k.type('mera'); pg.wait_for_timeout(100); it=pg.evaluate(ITEMS)
    ok('AC4 a near-miss spelling still finds the existing name', it and it[0][0]=='MEERA', it)
    k.press('Control+a'); k.press('Backspace'); pg.wait_for_timeout(100); k.press('ArrowDown'); k.press('ArrowDown')
    picked=pg.evaluate("(document.querySelector('#ac .ac-i.on b')||{}).textContent"); k.press('Enter'); pg.wait_for_timeout(100)
    ok('AC5 arrow keys + Enter pick a suggestion', picked and blocks(pg)[-1]==['character',picked], (picked,blocks(pg)[-1]))
    k.press('Control+a'); k.type('zo'); pg.wait_for_timeout(100); k.press('Escape'); pg.wait_for_timeout(100)
    hid=not pg.is_visible('#ac'); k.press('Tab'); pg.wait_for_timeout(100)
    ok('AC6 Escape closes the popup, and Tab then changes the line type as before', hid and blocks(pg)[-1][0]=='paren', blocks(pg)[-1])
    pg.keyboard.press('Alt+3'); k.press('Control+a'); k.type('NEWGUY'); k.press('Enter'); pg.wait_for_timeout(100)
    ok('AC7 plain Enter keeps a brand-new name (never auto-replaced)', blocks(pg)[-2]==['character','NEWGUY'] and blocks(pg)[-1][0]=='dialogue', blocks(pg)[-2:])
    pg.evaluate("cur().blocks.push({t:'character',x:''});render();focusAt(cur().blocks.length-1,'end')"); pg.wait_for_timeout(200)
    first=pg.evaluate(ITEMS)[0][0]; pg.click('#ac .ac-i:nth-child(1)'); pg.wait_for_timeout(100)
    ok('AC8 clicking a suggestion fills it in', blocks(pg)[-1]==['character',first] and not pg.is_visible('#ac'), (first,blocks(pg)[-1]))
    pg.evaluate("cur().blocks=[{t:'scene',x:'INT. R - DAY'},{t:'character',x:'MEERA'},{t:'dialogue',x:'Hi.'},{t:'character',x:'RAVI'},{t:'dialogue',x:'Yo.'}];render();focusAt(4,'end')"); pg.wait_for_timeout(100)
    pg.keyboard.press('Enter'); pg.wait_for_timeout(250)
    ok('AC8b pressing Enter after dialogue opens a new character line with the popup already showing', blocks(pg)[-1][0]=='character' and pg.is_visible('#ac') and pg.evaluate(ITEMS)[0][0]=='MEERA', pg.evaluate(ITEMS))
    pg.evaluate("cur().blocks.push({t:'character',x:''});render();focusAt(cur().blocks.length-1,'end')"); pg.wait_for_timeout(200)
    r=pg.evaluate("(()=>{const r=document.querySelector('#ac').getBoundingClientRect();return [r.top,r.bottom,r.left,r.right,innerHeight,innerWidth]})()")
    ok('AC9 popup stays inside the visible window', r[0]>=0 and r[1]<=r[4] and r[2]>=0 and r[3]<=r[5], r)
    pg.evaluate("focusAt(1,'end')"); pg.wait_for_timeout(150)
    ok('AC10 no popup while writing dialogue', not pg.is_visible('#ac'))
    ok('AC11 autocomplete triggers no security-policy violation', pg.evaluate('window.__csp')==[], pg.evaluate('window.__csp'))
    mc2=b.new_context(viewport={'width':390,'height':780},is_mobile=True,has_touch=True,service_workers='block'); mq=mc2.new_page(); mq.goto(URL); mq.wait_for_timeout(600)
    mq.evaluate(SEED); mq.evaluate("focusAt(cur().blocks.length-1,'end')"); mq.wait_for_timeout(250)
    first=mq.evaluate(ITEMS)[0][0]; inview=mq.evaluate("(()=>{const r=document.querySelector('#ac').getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.right<=innerWidth})()")
    mq.tap('#ac .ac-i:nth-child(1)'); mq.wait_for_timeout(100)
    ok('AC12 on a phone the popup fits the screen and a tap fills the name', inview and mq.evaluate("cur().blocks[cur().blocks.length-1].x")==first, (first,inview))

    # ---- scene heading autocomplete ----
    SSEED="""cur().blocks=[{t:'scene',x:'INT. KITCHEN - DAY'},{t:'action',x:'a'},{t:'scene',x:'INT. KITCHEN - NIGHT'},{t:'action',x:'b'},{t:'scene',x:'EXT. PARK - DAY'},{t:'scene',x:'INT. KITCHEN - MORNING'},{t:'scene',x:''}];render();focusAt(6,'end')"""
    NAMES="[...document.querySelectorAll('#ac .ac-i')].map(d=>d.querySelector('b').textContent)"
    fresh(pg); k=pg.keyboard; pg.evaluate(SSEED); pg.wait_for_timeout(200); nm=pg.evaluate(NAMES)
    ok('SC1 empty scene heading offers INT./EXT. and the locations you use most', 'INT.' in nm and 'EXT.' in nm and 'INT. KITCHEN' in nm, nm)
    ok('SC2 the old scene chips are gone (one popup does it all)', pg.evaluate("document.querySelectorAll('#sg button').length")==0)
    k.type('i'); pg.wait_for_timeout(100); nm=pg.evaluate(NAMES); ok('SC3 typing "i" narrows to INT. options', 'INT.' in nm and 'EXT.' not in nm, nm)
    k.press('Tab'); pg.wait_for_timeout(100); nm=pg.evaluate(NAMES)
    ok('SC4 Tab fills INT. and immediately offers your locations', blocks(pg)[-1][1]=='INT. ' and 'KITCHEN' in nm and 'PARK' in nm, (blocks(pg)[-1],nm))
    k.press('Tab'); pg.wait_for_timeout(100); sp=pg.evaluate("[...document.querySelectorAll('#ac .ac-i')].map(d=>[d.querySelector('b').textContent,d.querySelector('span').textContent])")
    ok('SC5 choosing a location moves on to time of day, your past times first', blocks(pg)[-1][1]=='INT. KITCHEN - ' and sp[0][0]=='DAY' and 'used here' in sp[0][1] and any(x[0]=='EVENING' for x in sp), (blocks(pg)[-1],sp))
    k.type('n'); pg.wait_for_timeout(100); k.press('Tab'); pg.wait_for_timeout(100)
    ok('SC6 typing a letter picks the time and finishes the heading', blocks(pg)[-1][1]=='INT. KITCHEN - NIGHT' and not pg.is_visible('#ac'), blocks(pg)[-1])
    k.press('Control+a'); k.type('INT. PAR'); pg.wait_for_timeout(100); nm=pg.evaluate(NAMES); ok('SC7 a few letters of a location find it', nm and nm[0]=='PARK', nm)
    k.press('Control+a'); k.type('int. kitchn'); pg.wait_for_timeout(100); nm=pg.evaluate(NAMES); ok('SC8 a misspelt location still finds the right one', nm and nm[0]=='KITCHEN', nm)
    k.press('Control+a'); k.type('INT. GARAGE - DAY'); k.press('Enter'); pg.wait_for_timeout(100)
    ok('SC9 a brand-new location is kept exactly as typed', blocks(pg)[-2]==['scene','INT. GARAGE - DAY'] and blocks(pg)[-1][0]=='action', blocks(pg)[-2:])
    pg.evaluate("cur().blocks.push({t:'scene',x:''});render();focusAt(cur().blocks.length-1,'end')"); pg.wait_for_timeout(150); k.press('Escape'); k.press('Tab'); pg.wait_for_timeout(100)
    ok('SC10 Esc closes the popup and Tab changes the line type as before', blocks(pg)[-1][0]=='action', blocks(pg)[-1])
    ok('SC11 scene autocomplete triggers no security-policy violation', pg.evaluate('window.__csp')==[], pg.evaluate('window.__csp'))
    mq.evaluate(SSEED); mq.wait_for_timeout(250); mq.tap('#ac .ac-i:nth-child(1)'); mq.wait_for_timeout(150)
    ok('SC12 on a phone a tap fills the heading and shows the next step', mq.evaluate("cur().blocks[6].x").strip() in ('INT.','EXT.','INT. KITCHEN -','INT./EXT.') and mq.is_visible('#ac'), mq.evaluate("cur().blocks[6].x"))

    # ---- Final Draft (.fdx) export / import ----
    import xml.etree.ElementTree as ET
    fresh(pg); pg.evaluate("document.querySelector('#ttl').value=''")
    pg.evaluate("""cur().title='Tom & Jerry <Pilot>';cur().author='A. "Writer"';cur().blocks=[{t:'scene',x:'int. kitchen - day'},{t:'action',x:'Line one.\\nLine two & <three> "quoted" \\'apos\\' \\u0001 end \\u{1F600}'},{t:'character',x:'Meera'},{t:'paren',x:'to herself'},{t:'dialogue',x:'Hi.'},{t:'action',x:'Beat.'},{t:'character',x:'Meera (V.O.)'},{t:'dialogue',x:'Again.'},{t:'trans',x:'cut to:'},{t:'action',x:''}];render()""")
    pg.wait_for_timeout(150)
    fd=pg.evaluate("toFDX()")
    try: root=ET.fromstring(fd); okxml=True
    except Exception as e: root=None; okxml=False; print('   xml error',e)
    ok('FD1 export is well-formed XML with a FinalDraft root', okxml and root.tag=='FinalDraft', fd[:200])
    open('/tmp/t.fdx','w').write(fd); import subprocess as sp2; xl=sp2.run(['xmllint','--noout','/tmp/t.fdx'],capture_output=True,text=True)
    ok('FD2 independent XML checker (xmllint) accepts the file', xl.returncode==0, xl.stderr[:200])
    paras=[(p.get('Type'),''.join(x.text or '' for x in p.findall('Text'))) for p in root.find('Content')]
    print('   fdx paragraphs:',[p[0] for p in paras])
    ok('FD3 paragraph types and order are right (multi-line action split, empty block dropped)', [p[0] for p in paras]==['Scene Heading','Action','Action','Character','Parenthetical','Dialogue','Action','Character','Dialogue','Transition'], [p[0] for p in paras])
    ok('FD4 scene/character/transition upper-cased, parenthetical wrapped', paras[0][1]=='INT. KITCHEN - DAY' and paras[3][1]=='MEERA' and paras[4][1]=='(to herself)' and paras[9][1]=='CUT TO:', paras)
    ok('FD5 special characters survive escaping, control characters are removed', paras[2][1]=='Line two & <three> "quoted" \'apos\'  end \U0001F600', paras[2])
    ok("FD6 (CONT'D) is not written (Final Draft adds its own) but (V.O.) is kept", paras[7][1]=='MEERA (V.O.)' and not any("CONT" in p[1] for p in paras), paras)
    tpt=[''.join(x.text or '' for x in p.findall('Text')) for p in root.find('TitlePage').find('Content')]
    ok('FD7 title page has the title and author', 'TOM & JERRY <PILOT>' in tpt and 'A. "Writer"' in tpt, tpt)
    mclick(pg,'#bc'); pg.click('#mf')
    with pg.expect_download() as dfd: pg.click('#mdl')
    ok('FD8 Download saves a .fdx file with the same content', dfd.value.suggested_filename.endswith('.fdx') and open(dfd.value.path()).read()==fd, dfd.value.suggested_filename)
    n0=pg.evaluate("S.scripts.length"); pg.click('#mi'); pg.wait_for_timeout(250)
    rt=[[a,x.replace(" (CONT'D)",'')] for a,x in pg.evaluate("cur().blocks.map(b=>[b.t,b.x])")]
    exp=[['scene','INT. KITCHEN - DAY'],['action','Line one.'],['action','Line two & <three> "quoted" \'apos\'  end \U0001F600'],['character','MEERA'],['paren','(to herself)'],['dialogue','Hi.'],['action','Beat.'],['character','MEERA (V.O.)'],['dialogue','Again.'],['trans','CUT TO:']]
    ok('FD9 importing the exported file gives back the same script', pg.evaluate("S.scripts.length")==n0+1 and rt==exp and pg.evaluate("cur().author")=='A. "Writer"', rt)
    bad={'DOCTYPE/entity (XXE style)':'<?xml version="1.0"?><!DOCTYPE FinalDraft [<!ENTITY x SYSTEM "file:///etc/passwd">]><FinalDraft><Content><Paragraph Type="Action"><Text>&x;</Text></Paragraph></Content></FinalDraft>','broken XML':'<?xml version="1.0"?><FinalDraft><Content><Paragraph>','wrong root':'<?xml version="1.0"?><html><body>hi</body></html>'}
    for nm,xml in bad.items():
        n1=pg.evaluate("S.scripts.length"); mclick(pg,'#bc'); pg.evaluate("v=>{document.querySelector('#mt').value=v}",xml); pg.click('#mi'); pg.wait_for_timeout(150)
        ok('FD10 hostile or broken import refused: '+nm, pg.evaluate("S.scripts.length")==n1 and 'Could not import' in pg.evaluate("document.querySelector('#toast').textContent"), pg.evaluate("document.querySelector('#toast').textContent"))
        pg.keyboard.press('Escape')
    mclick(pg,'#bc'); pg.evaluate("v=>{document.querySelector('#mt').value=v}",'<?xml version="1.0"?><FinalDraft><Content><Paragraph Type="Shot"><Text>CLOSE ON</Text></Paragraph><Paragraph Type="Weird"><Text a="1">x</Text><Text>y</Text></Paragraph><Paragraph Type="General"/></Content></FinalDraft>'); pg.click('#mi'); pg.wait_for_timeout(200)
    ok('FD11 unknown paragraph types become action; multiple text runs are joined; empty ones dropped', pg.evaluate("cur().blocks.map(b=>[b.t,b.x])")==[['action','CLOSE ON'],['action','xy']], pg.evaluate("cur().blocks.map(b=>[b.t,b.x])"))
    cs=pg.evaluate('window.__csp')
    ok('FD12 FDX export/import trigger no script/network/image policy violation (only the browser\'s own XML-error page may note inline styles when a broken file is rejected)', all(v.startswith('style-src-attr') for v in cs) and len(cs)<=4, cs)
    ok('Z no page errors overall', not errs, errs)
    b.close()
f=[r for r in R if not r[1]]; print(f'\n{len(R)-len(f)}/{len(R)} passed'); sys.exit(1 if f else 0)

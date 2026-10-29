/* Dense, deep and live synthetic fixture acceptance. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url'),{chromium}=require('playwright');
(async()=>{
  const browser=await chromium.launch({headless:true}),dir=path.resolve(process.argv[2]);
  const page=await browser.newPage({viewport:{width:1560,height:1050}}),checks=[],errors=[];
  await page.addInitScript(()=>document.addEventListener('DOMContentLoaded',()=>requestAnimationFrame(()=>{
    window.initialTraces=document.getAnimations().filter(a=>a.playState==='running'&&a.effect.target.classList.contains('edge-reveal')).length;
  })));
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  const check=(name,value)=>{assert.ok(value,name);checks.push(name);};
  const open=async name=>{await page.goto(pathToFileURL(path.join(dir,name+'.html')).href);await page.waitForTimeout(280);};
  try {
    await open('mixed');await page.locator('[data-view=architecture]').click();
    await page.locator('[data-node-id="folder:0"] .expand').click();await page.waitForTimeout(280);
    const settled=await page.locator('[data-node-id="file:0"]').evaluate(el=>getComputedStyle(el).transform);
    await open('mixed');await page.locator('[data-view=architecture]').click();
    await page.locator('[data-node-id="folder:0"] .expand').click();
    await page.locator('[data-node-id="file:0"]').focus();await page.locator('[data-node-id="file:0"]').press('Enter');
    check('Interrupting an expansion still reaches the correct architecture position',await page.locator('[data-node-id="file:0"]').evaluate(el=>getComputedStyle(el).transform)===settled);
    check('Architecture has no expansion button for declarations excluded from that view',await page.locator('[data-node-id="file:0"] .expand').count()===0);
    await open('flow80');
    check('80 connections can animate',await page.locator('.edge-flow.flowing').count()===80);
    await open('flow81');
    check('81 connections stay static with an explanation',await page.locator('.edge-flow.flowing').count()===0&&Boolean(await page.locator('#flow-hint').textContent()));
    check('Connection arrival traces obey the same animation budget',await page.evaluate(()=>window.initialTraces===0));
    await page.locator('[data-node-id="file:0"]').focus();await page.locator('[data-node-id="file:0"]').press('Enter');
    check('Selecting a source bounds animated connections to its neighbors',await page.locator('.edge-flow.flowing').count()===1);
    await open('flow-overflow');
    await page.locator('[data-node-id="file:80"]').focus();await page.locator('[data-node-id="file:80"]').press('Enter');
    check('Drawing limits cannot conceal excess connections from the animation budget',await page.locator('.edge-flow.flowing').count()===0);
    const begin=Date.now();await open('wide');
    check('Dense graph stays bounded and finishes loading',await page.locator('.node').count()===500&&Date.now()-begin<10000);
    check('Drawing omissions keep the correct total',/1001/.test(await page.locator('#shown').textContent()));
    await page.locator('#search').fill('File-999.py');await page.waitForTimeout(280);
    check('Search reaches a source outside the initial drawing limit',await page.locator('[data-node-id="file:999"]').count()===1);
    await open('deep');await page.locator('[data-view=architecture]').click();await page.locator('#type').selectOption('folder');await page.waitForTimeout(280);
    check('Deep architecture is finite and spans its real depth',await page.evaluate(()=>{
      const xs=[...document.querySelectorAll('.node')].map(n=>new DOMMatrix(getComputedStyle(n).transform).m41);
      return xs.length===180&&xs.every(Number.isFinite)&&Math.max(...xs)-Math.min(...xs)>40000;
    }));
    for(const width of [1560,1024,768,390]) {
      await page.setViewportSize({width,height:844});await page.waitForTimeout(100);
      check('No horizontal overflow at '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    }
    await page.setViewportSize({width:1560,height:1050});
    // Route a synthetic live server in-process. No private HTML or real server is opened.
    const html=fs.readFileSync(path.join(dir,'live.html'),'utf8');
    let snapshot=JSON.parse(html.match(/<script type="application\/json" id="snapshot">(.*?)<\/script>/s)[1]),revision=1;
    await page.route('http://127.0.0.1:47813/fixture/**',route=>{
      const suffix=new URL(route.request().url()).pathname.split('/').at(-1);
      const body=suffix==='status'?{state:'Watching',published_generation:String(revision)}:suffix==='snapshot'?{snapshot,generation:String(revision)}:null;
      return route.fulfill({contentType:body?'application/json':'text/html',body:body?JSON.stringify(body):html});
    });
    await page.goto('http://127.0.0.1:47813/fixture/');await page.waitForTimeout(350);
    const folder=page.locator('[data-node-id="folder:0"]');await folder.focus();await folder.press('ArrowRight');
    const camera=await page.locator('#canvas').getAttribute('style');
    const before=await folder.evaluate(el=>getComputedStyle(el).transform);
    snapshot=structuredClone(snapshot);snapshot.index_generation=2;
    snapshot.nodes.push({id:'file:new',type:'file',label:'New.java',path:'module-0/New.java',details:{},status:'current'});
    snapshot.edges.push({id:'new-edge',source:'folder:0',target:'file:new',relation:'contains'});revision++;
    await page.waitForFunction(()=>document.querySelector('#project').textContent.includes('2'),null,{timeout:6000});await page.waitForTimeout(280);
    check('Live additions preserve manual positions and camera',await folder.getAttribute('data-pinned')==='true'&&await folder.evaluate(el=>getComputedStyle(el).transform)===before&&await page.locator('#canvas').getAttribute('style')===camera);
    await folder.locator('.expand').click();await page.waitForTimeout(280);
    check('Live additions become explorable',await page.locator('[data-node-id="file:new"]').count()===1);
    snapshot=structuredClone(snapshot);snapshot.index_generation=3;
    const changedLink=snapshot.edges.find(e=>e.relation==='related');changedLink.target='folder:2';revision++;
    await page.waitForFunction(()=>document.querySelector('#project').textContent.includes('3'),null,{timeout:6000});await page.waitForTimeout(280);
    check('Live relation-only changes update endpoints with unchanged node IDs',await page.locator('.connection[data-relation="related"][data-target="folder:2"]').count()===1&&await page.locator('.connection[data-relation="related"][data-target="folder:1"]').count()===0);
    await page.locator('[data-view=inventory]').click();
    snapshot=structuredClone(snapshot);snapshot.index_generation=4;snapshot.nodes=snapshot.nodes.filter(n=>n.id!=='file:new');snapshot.edges=snapshot.edges.filter(e=>e.id!=='new-edge');revision++;
    await page.waitForFunction(()=>document.querySelector('#project').textContent.includes('4'),null,{timeout:6000});
    check('Live publication preserves exclusive Inventory mode',!await page.locator('#graph').isVisible()&&await page.locator('.inventory-row').count()===100);
    check('No dense/live JS or CSP errors',errors.length===0);
    console.log(JSON.stringify({checks,errors},null,2));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

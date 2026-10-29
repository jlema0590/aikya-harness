/* Stateful presentation only: source relationships and the exported snapshot stay immutable. */
'use strict';
const AikyaMemoryGraph = ({svg,canvas,words,choose,refresh,status,motion}) => {
  const ns='http://www.w3.org/2000/svg', states=new Map(),groups=new Map(),links=new Map();
  const make=(name,attrs={})=>{const el=document.createElementNS(ns,name);for(const [key,value] of Object.entries(attrs))el.setAttribute(key,value);return el;};
  const edgesLayer=make('g'),nodesLayer=make('g');canvas.append(edgesLayer,nodesLayer);
  let snapshot=null,tree=null,current=null,params=null,mode=null,frame=0,displayed=new Map(),targets=new Map(),instantNext=false;
  let dragging=false,hovered=null,labelFrame=0,moveFrame=0,counts=new Map(),countsByView=new Map(),edgeCount=0,incidentCounts=new Map();
  function labels() {
    if(labelFrame)return;
    labelFrame=requestAnimationFrame(()=>{labelFrame=0;if(current)AikyaMemoryLabels(groups,displayed,current.camera,params.selected||hovered);});
  }
  function draw() {
    for(const [id,group] of groups) {
      const point=displayed.get(id);if(!point)continue;
      group.style.transform=`translate(${point[0]}px,${point[1]}px)`;
      group.dataset.pinned=String(current.manual.has(id));
    }
    for(const {group,edge} of links.values()) {
      const a=displayed.get(edge.source),b=displayed.get(edge.target);if(!a||!b)continue;
      const signature=[...a,...b].join(',');if(group.dataset.geometry===signature)continue;
      group.dataset.geometry=signature;
      const line=group.querySelector('.edge');
      for(const [key,value] of Object.entries({x1:a[0],y1:a[1],x2:b[0],y2:b[1]}))line.setAttribute(key,value);
      const d=`M ${a[0]} ${a[1]} L ${b[0]} ${b[1]}`;
      for(const path of group.querySelectorAll('path'))path.setAttribute('d',d);
    }
  }
  function flows() {
    const visible=mode!=='inventory'&&!document.hidden;
    const candidates=[...links.values()].filter(({edge})=>!params.selected||edge.source===params.selected||edge.target===params.selected);
    const total=params.selected?(incidentCounts.get(params.selected)||0):edgeCount;
    const enabled=visible&&motion()&&!dragging&&total<=80;
    const eligible=new Set(enabled?candidates.map(item=>item.edge.id):[]);
    for(const {group,edge} of links.values())group.querySelector('.edge-flow').classList.toggle('flowing',eligible.has(edge.id));
    const hint=document.getElementById('flow-hint');
    hint.textContent=total>80?words.flowLimit:words.flowHint;
    canvas.classList.toggle('paused',!visible||!motion()||dragging);
    canvas.classList.toggle('traces-off',edgeCount>80||Boolean(params.keyboard));
  }
  function stop() {
    if(frame){cancelAnimationFrame(frame);frame=0;}
    for(const [id,group] of groups)if(group.classList.contains('exiting')){group.remove();groups.delete(id);displayed.delete(id);}
  }
  const camera=AikyaMemoryCamera({svg,canvas,state:()=>mode==='inventory'?null:current,motion,labels,
    beforeGesture(){stop();for(const [id,point] of displayed)if(current.positions.has(id))current.positions.set(id,[...point]);dragging=true;flows();},
    move(id,point){current.positions.set(id,point);displayed.set(id,point);if(!moveFrame)moveFrame=requestAnimationFrame(()=>{moveFrame=0;draw();});},
    end(){if(moveFrame){cancelAnimationFrame(moveFrame);moveFrame=0;draw();}dragging=false;flows();}});
  function state(view) {
    if(!states.has(view))states.set(view,{expanded:new Set(),manual:new Map(),positions:new Map(),key:'',camera:{x:0,y:0,k:1},fitted:false,initialized:false});
    return states.get(view);
  }
  function rebuild(data) {
    if(data===snapshot)return;
    snapshot=data;tree=AikyaMemoryLayout.structure(data.nodes,data.edges);countsByView=new Map();
    const order=[],stack=[...tree.roots];
    while(stack.length){const id=stack.pop();order.push(id);stack.push(...tree.children.get(id));}
    for(const view of ['graph','architecture']) {
      const totals=new Map(data.nodes.map(n=>[n.id,0]));
      for(const id of [...order].reverse()) {
        const parent=tree.parent.get(id),included=view==='graph'||['project','folder','file'].includes(tree.byID.get(id).type);
        if(parent)totals.set(parent,totals.get(parent)+totals.get(id)+(included?1:0));
      }
      countsByView.set(view,totals);
    }
    for(const s of states.values())for(const collection of [s.manual,s.expanded,s.positions])for(const id of collection.keys())if(!tree.byID.has(id))collection.delete(id);
  }
  function expand(id,keyboard) {
    instantNext=keyboard;
    if(current.expanded.has(id))current.expanded.delete(id);else current.expanded.add(id);
    refresh();
    if(keyboard){const group=groups.get(id);group?.querySelector('.expand')?.focus();}
  }
  function addNode(node) {
    const group=make('g',{'role':'button',tabindex:'0'});group.dataset.nodeId=node.id;
    const title=make('title');group.append(title,make('circle',{'class':'hit',r:14}),make('circle',{'class':'body'}),make('text',{'class':'label',visibility:'hidden'}));
    group.onclick=()=>choose(node.id);
    group.onkeydown=event=>{
      if(event.target.closest('.expand'))return;
      if(event.key==='Enter'||event.key===' '){event.preventDefault();choose(node.id,true);}
      const direction={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]}[event.key];
      if(direction){event.preventDefault();camera.nudge(node.id,...direction);}
    };
    group.addEventListener('focusin',()=>{hovered=node.id;labels();});
    group.addEventListener('pointerenter',()=>{hovered=node.id;labels();});
    group.addEventListener('pointerleave',()=>{hovered=null;labels();});
    groups.set(node.id,group);nodesLayer.append(group);return group;
  }
  function updateNode(node,close) {
    const group=groups.get(node.id)||addNode(node),isSelected=node.id===params.selected;
    group.setAttribute('class','node '+node.type+(isSelected?' selected':'')+(params.selected&&!close.has(node.id)?' dimmed':''));
    group.removeAttribute('aria-hidden');group.setAttribute('tabindex','0');group.style.opacity='1';
    group.setAttribute('aria-label',node.type+': '+node.label);group.setAttribute('aria-pressed',String(isSelected));
    group.querySelector('.body').setAttribute('r',node.type==='project'?12:node.type==='folder'?8:6);
    group.querySelector('title').textContent=node.path||node.label;
    const count=counts.get(node.id),suffix=count?' · '+count:'';
    group.querySelector('.label').textContent=(node.label.length>26?node.label.slice(0,25)+'…':node.label)+suffix;
    let toggle=group.querySelector('.expand');
    if(count) {
      if(!toggle) {
        toggle=make('g',{'class':'expand',role:'button',tabindex:'0',visibility:'hidden'});toggle.append(make('circle',{r:12}),make('text',{y:4}));group.append(toggle);
        toggle.onclick=event=>{event.stopPropagation();expand(node.id,event.detail===0);};
        toggle.onkeydown=event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();event.stopPropagation();expand(node.id,true);}};
      }
      const open=current.expanded.has(node.id);toggle.setAttribute('aria-expanded',String(open));
      toggle.setAttribute('aria-label',(open?words.collapse:words.expand)+' '+node.label+' · '+count);
      toggle.querySelector('text').textContent=open?'−':'+';
    } else toggle?.remove();
  }
  function reconcileEdges(positions) {
    const edges=snapshot.edges.filter(e=>positions.has(e.source)&&positions.has(e.target)),shown=edges.slice(0,3000),ids=new Set(shown.map(e=>e.id));
    edgeCount=edges.length;incidentCounts=new Map();
    for(const edge of edges)for(const id of new Set([edge.source,edge.target]))incidentCounts.set(id,(incidentCounts.get(id)||0)+1);
    for(const [id,item] of links)if(!ids.has(id)){item.group.remove();links.delete(id);}
    for(const edge of shown) {
      let item=links.get(edge.id);
      if(!item) {
        const group=make('g',{'class':'connection','aria-hidden':'true'});
        group.dataset.source=edge.source;group.dataset.target=edge.target;group.dataset.relation=edge.relation;
        const title=make('title');title.textContent=edge.relation;
        const directed=edge.relation==='contains';
        group.append(title,make('line',{'class':'edge'}),make('path',{'class':'edge-reveal',pathLength:1}),make('path',{'class':'edge-flow '+(directed?'directed':'undirected')}));
        edgesLayer.append(group);item={group,edge};links.set(edge.id,item);
      }
      item.edge=edge;item.group.dataset.source=edge.source;item.group.dataset.target=edge.target;
      item.group.dataset.relation=edge.relation;item.group.querySelector('title').textContent=edge.relation;
      item.group.querySelector('.edge-flow').classList.toggle('directed',edge.relation==='contains');
      item.group.querySelector('.edge-flow').classList.toggle('undirected',edge.relation!=='contains');
      item.group.classList.toggle('active',edge.source===params.selected||edge.target===params.selected);
    }
    return edges.length-shown.length;
  }
  function paint(animate) {
    const from=new Map(displayed),start=performance.now();
    for(const [id,target] of targets)if(!displayed.has(id)) {
      const parent=tree.parent.get(id);displayed.set(id,from.get(parent)||target);from.set(id,displayed.get(id));
    }
    const finish=()=>{
      displayed=new Map(current.positions);
      for(const [id,group] of groups)if(!current.positions.has(id)){group.remove();groups.delete(id);}
      draw();labels();frame=0;
    };
    const changed=[...targets].some(([id,p])=>!from.has(id)||Math.hypot(p[0]-from.get(id)[0],p[1]-from.get(id)[1])>.01);
    if(!animate||!changed||targets.size>150){finish();return;}
    function step(now) {
      const t=Math.min(1,(now-start)/220),eased=1-Math.pow(1-t,3);
      for(const [id,b] of targets){const a=from.get(id)||b;displayed.set(id,[a[0]+(b[0]-a[0])*eased,a[1]+(b[1]-a[1])*eased]);}
      draw();if(t<1)frame=requestAnimationFrame(step);else finish();
    }
    frame=requestAnimationFrame(step);
  }
  function render(next) {
    camera.cancel();stop();rebuild(next.data);params=next;
    const changed=mode!==next.view;mode=next.view;
    counts=countsByView.get(mode);
    if(changed){groups.clear();links.clear();nodesLayer.replaceChildren();edgesLayer.replaceChildren();displayed=new Map();}
    current=state(mode);
    if(!current.initialized){for(const n of snapshot.nodes)if(n.type==='project')current.expanded.add(n.id);current.initialized=true;}
    const projection=AikyaMemoryLayout.project(next.nodes,tree,current.expanded,next.detail,next.selected);
    const nodes=projection.nodes,ids=new Set(nodes.map(n=>n.id));
    const edges=snapshot.edges.filter(e=>ids.has(e.source)&&ids.has(e.target));
    const key=JSON.stringify([nodes.map(n=>n.id),edges.map(e=>[e.id,e.source,e.target,e.relation])]);
    if(key!==current.key){current.positions=AikyaMemoryLayout.arrange(nodes,edges,mode,current.manual,current.positions);current.key=key;}
    targets=new Map(current.positions);
    const close=new Set([next.selected]);for(const e of edges)if(e.source===next.selected||e.target===next.selected){close.add(e.source);close.add(e.target);}
    for(const node of nodes)updateNode(node,close);
    for(const [id,group] of groups)if(!ids.has(id)) {
      group.classList.add('exiting');group.setAttribute('aria-hidden','true');group.setAttribute('tabindex','-1');
      group.querySelector('.expand')?.setAttribute('tabindex','-1');group.style.opacity='0';
      if(group.contains(document.activeElement))groups.get(tree.parent.get(id))?.focus();
      targets.set(id,current.positions.get(tree.parent.get(id))||displayed.get(id));
    }
    const omittedEdges=reconcileEdges(current.positions);
    const animate=!changed&&!instantNext&&!next.keyboard&&motion()&&!document.hidden;instantNext=false;
    paint(animate);camera.resize();if(!current.fitted&&nodes.length)camera.fit();else camera.apply();
    flows();status({...projection,omittedEdges});
  }
  function halt() {
    if(frame){cancelAnimationFrame(frame);frame=0;paint(false);}
    canvas.classList.remove('animate-camera');
    flows();
  }
  document.addEventListener('visibilitychange',()=>{if(document.hidden)halt();else flows();});
  document.getElementById('zoom-in').onclick=event=>camera.zoom(1.25,null,event.detail!==0);
  document.getElementById('zoom-out').onclick=event=>camera.zoom(.8,null,event.detail!==0);
  document.getElementById('zoom-reset').onclick=event=>camera.fit(event.detail!==0);
  document.getElementById('layout-reset').onclick=event=>{if(!current||mode==='inventory')return;current.manual.clear();current.positions=new Map();current.key='';instantNext=event.detail===0;refresh();};
  return {render,motionChanged:halt,hide(){camera.cancel();stop();mode='inventory';flows();},
    reveal(id){if(!tree)return;for(const view of ['graph','architecture']){let parent=tree.parent.get(id);const s=state(view);while(parent){s.expanded.add(parent);parent=tree.parent.get(parent);}}}};
};

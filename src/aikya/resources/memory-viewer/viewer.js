'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const spanish = document.documentElement.lang === 'es';
  const words = spanish ? {
    eyebrow:'Conocimiento local del proyecto',headline:'Cada cambio, en contexto.',structure:'Estructura del proyecto',
    treeHint:'Archivos y declaraciones verificables.',graph:'Grafo de conocimiento',architecture:'Arquitectura',inventory:'Inventario',
    search:'Buscar símbolos y rutas…',type:'Tipo',folder:'Carpeta',allTypes:'Todos los tipos',allFolders:'Todas las carpetas',
    neighbors:'Solo vecinos',reset:'Restablecer',previous:'Anterior',next:'Siguiente',evidenceOnly:'Relaciones con evidencia explícita',
    inspector:'Inspector de fuentes',traceHint:'La estructura estática no demuestra un recorrido de ejecución ni pruebas superadas.',
    select:'Selecciona una fuente',selectHint:'Explora el grafo o busca una clase para inspeccionar su procedencia.',
    nodes:'nodos',links:'relaciones',notes:'notas',empty:'No hay resultados dentro de estos filtros.',
    motionOn:'Movimiento activo',motionOff:'Movimiento desactivado',lightTheme:'Tema claro',darkTheme:'Tema oscuro',snapshot:'Instantánea local',
    sources:'Fuentes',folders:'Carpetas',files:'Archivos',symbols:'Declaraciones',documents:'Documentos y notas',
    partial:'Cobertura parcial',verified:'Verificado',removed:'La fuente seleccionada ya no está disponible.',
    disconnected:'Disconnected',limit:'Mostrando una selección acotada',of:'de',generation:'generación del índice',source:'Fuente',review:'Revisión',eligible:'Disponible para consultas',lines:'Líneas'
    ,fit:'Ajustar vista',layoutReset:'Restablecer distribución',expand:'Expandir',collapse:'Contraer',grouped:'agrupados',limited:'fuera del límite',edgeLimit:'conexiones fuera del límite',
    flowHint:'Flujo visual de relaciones verificadas; no representa ejecución.',flowLimit:'Selecciona un componente o filtra para animar hasta 80 conexiones.',
    graphHint:'Arrastra objetos para organizarlos; arrastra el fondo para navegar. +/− expande o contrae. Flechas: mover el objeto enfocado.',zoomIn:'Ampliar',zoomOut:'Alejar'
  } : {
    eyebrow:'Local project knowledge',headline:'Every change, in context.',structure:'Project structure',
    treeHint:'Source files and verifiable declarations.',graph:'Knowledge graph',architecture:'Architecture',inventory:'Inventory',
    search:'Search symbols and paths…',type:'Type',folder:'Folder',allTypes:'All types',allFolders:'All folders',
    neighbors:'Only neighbors',reset:'Reset',previous:'Previous',next:'Next',evidenceOnly:'Explicit source evidence only',
    inspector:'Source inspector',traceHint:'Static structure does not prove a runtime request flow or passing tests.',
    select:'Select a source',selectHint:'Explore the graph or find a class to inspect its provenance.',
    nodes:'nodes',links:'links',notes:'notes',empty:'No results within these filters.',
    motionOn:'Motion on',motionOff:'Motion off',lightTheme:'Light theme',darkTheme:'Dark theme',snapshot:'Local snapshot',
    sources:'Sources',folders:'Folders',files:'Files',symbols:'Declarations',documents:'Documents and notes',
    partial:'Partial coverage',verified:'Verified',removed:'The selected source is no longer available.',
    disconnected:'Disconnected',limit:'Showing a bounded selection',of:'of',generation:'index generation',source:'Source',review:'Review',eligible:'Eligible for recall',lines:'Lines'
    ,fit:'Fit view',layoutReset:'Reset layout',expand:'Expand',collapse:'Collapse',grouped:'grouped',limited:'outside drawing limit',edgeLimit:'links outside drawing limit',
    flowHint:'Visual flow of verified relationships; not runtime execution.',flowLimit:'Select a component or filter to animate up to 80 connections.',
    graphHint:'Drag objects to arrange; drag the background to pan. +/− expands or collapses. Arrow keys move the focused object.',zoomIn:'Zoom in',zoomOut:'Zoom out'
  };
  document.querySelectorAll('[data-i18n]').forEach(el => {el.textContent = words[el.dataset.i18n];});
  $('search').placeholder = words.search;
  $('empty').textContent = words.empty;
  let data = JSON.parse($('snapshot').textContent);
  let selected = null, view = 'graph', neighbors = false, page = 0, graphViewer=null;
  let motion = !matchMedia('(prefers-reduced-motion: reduce)').matches;
  let index = new Map(), openBranches = new Set();
  const text = (tag, value, className) => {
    const el = document.createElement(tag); el.textContent = value;
    if (className) el.className = className;
    return el;
  };
  function setMotion() {
    if(matchMedia('(prefers-reduced-motion: reduce)').matches)motion=false;
    document.body.classList.toggle('motion-off', !motion);
    $('motion').textContent = motion ? words.motionOn : words.motionOff;
    $('motion').setAttribute('aria-pressed', String(motion));
    graphViewer?.motionChanged();
  }
  $('motion').onclick = () => {motion = !motion; setMotion();};
  function setTheme() {
    $('theme').textContent = document.body.classList.contains('light') ? words.darkTheme : words.lightTheme;
  }
  $('theme').onclick = () => {document.body.classList.toggle('light');setTheme();};
  setTheme();
  matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', event => {if(event.matches) motion=false;setMotion();});
  setMotion();
  function options() {
    const oldType = $('type').value, oldFolder = $('folder').value;
    for (const [id, values, label] of [
      ['type', [...new Set(data.nodes.map(n => n.type))].sort(), words.allTypes],
      ['folder', [...new Set(data.nodes.filter(n => n.type === 'file').map(n => n.path.split('/')[0]))].sort(), words.allFolders]
    ]) {
      $(id).replaceChildren();
      const all = text('option', label); all.value = 'all'; $(id).append(all);
      values.forEach(value => {const opt=text('option',value);opt.value=value;$(id).append(opt);});
    }
    if ([...$('type').options].some(o=>o.value===oldType)) $('type').value=oldType;
    if ([...$('folder').options].some(o=>o.value===oldFolder)) $('folder').value=oldFolder;
  }
  function neighborIDs() {
    const ids=new Set([selected]);
    data.edges.forEach(e=>{if(e.source===selected) ids.add(e.target);if(e.target===selected) ids.add(e.source);});
    return ids;
  }
  function filtered() {
    const query=$('search').value.toLocaleLowerCase(), kind=$('type').value, folder=$('folder').value;
    const close=neighbors&&selected ? neighborIDs() : null;
    return data.nodes.filter(n => (!query || (n.label+' '+n.path+' '+(n.details.text||'')).toLocaleLowerCase().includes(query))
      && (kind==='all'||n.type===kind) && (folder==='all'||n.path.split('/')[0]===folder)
      && (!close||close.has(n.id)) && (view!=='architecture'||['project','folder','file'].includes(n.type)));
  }
  function detail() {
    const node=index.get(selected);
    $('detail-title').textContent=node?node.label:words.select;
    $('detail-type').textContent=node?node.type+' · '+node.status:'';
    $('detail-path').textContent=node?node.path:'';
    const info=node?node.details:{};
    const parts=[info.signature,info.text,info.excerpt];
    if(info.start_line)parts.push(words.lines+': '+info.start_line+'–'+info.end_line);
    if(info.review_state)parts.push(words.review+': '+info.review_state+'\n'+words.eligible+': '+info.eligible_for_recall);
    if(info.source)parts.push(words.source+': '+info.source+'\n'+info.source_status);
    if(info.coverage)parts.push(info.coverage+' / '+info.parser);
    if(node&&node.source_hash)parts.push('SHA-256: '+node.source_hash);
    $('detail-body').textContent=node?parts.filter(Boolean).join('\n\n'):words.selectHint;
    $('connections').replaceChildren();
    if(node) data.edges.filter(e=>e.source===node.id||e.target===node.id).slice(0,100).forEach(e=>{
      const other=index.get(e.source===node.id?e.target:e.source),source=index.get(e.source),target=index.get(e.target);
      if(!other||!source||!target)return;
      const button=text('button',source.label+' — '+e.relation+(e.relation==='contains'?' → ':' · ')+target.label);button.type='button';
      button.onclick=()=>choose(other.id);$('connections').append(button);
    });
  }
  function choose(id,keyboard=false) {
    selected=id;
    const node=index.get(id);
    if(node){const parts=node.path.split('/').slice(0,-1);parts.forEach((_,i)=>openBranches.add(parts.slice(0,i+1).join('/')));}
    graphViewer.reveal(id);detail();render(keyboard);
    if(keyboard){const target=[...$('canvas').querySelectorAll('.node')].find(el=>el.dataset.nodeId===id);if(target)target.focus();}
  }
  function tree() {
    $('tree').replaceChildren();
    const query=$('search').value.toLocaleLowerCase();
    const sources=data.nodes.filter(n=>['file','document','memory'].includes(n.type)
      &&(!query||(n.path+' '+n.label).toLocaleLowerCase().includes(query))).slice(0,500);
    const folders=new Map([['',$('tree')]]);
    sources.forEach(node=>{
      const parts=node.path.split('/');let parent='';
      parts.slice(0,-1).forEach(part=>{
        const key=parent?parent+'/'+part:part;
        if(!folders.has(key)) {
          const branch=document.createElement('details');branch.open=Boolean(query)||openBranches.has(key);
          branch.append(text('summary',part));
          const holder=document.createElement('div');branch.append(holder);
          branch.addEventListener('toggle',()=>{if(branch.open)openBranches.add(key);else openBranches.delete(key);});
          folders.get(parent).append(branch);folders.set(key,holder);
        }
        parent=key;
      });
      const button=text('button',parts.at(-1),'tree-button');button.type='button';button.title=node.path;
      button.classList.toggle('selected',node.id===selected);button.onclick=()=>choose(node.id);folders.get(parent).append(button);
    });
  }
  function inventory(nodes) {
    const container=$('inventory');container.replaceChildren();
    nodes.slice(page*100,(page+1)*100).forEach(node=>{
      const row=text('button','','inventory-row');row.type='button';
      row.append(text('span',node.label),text('span',node.type),text('small',node.path+' · '+node.status));
      row.onclick=()=>choose(node.id);container.append(row);
    });
  }
  function render(keyboard=false) {
    const nodes=filtered();page=Math.min(page,Math.max(0,Math.ceil(nodes.length/100)-1));
    $('graph').toggleAttribute('hidden',view==='inventory');$('inventory').hidden=view!=='inventory';$('pages').hidden=view!=='inventory';
    $('graph-controls').hidden=view==='inventory';$('graph-hints').hidden=view==='inventory';
    $('graph').setAttribute('aria-label',view==='architecture'?words.architecture:words.graph);
    $('empty').hidden=nodes.length!==0;
    if(view==='inventory') {
      graphViewer.hide();inventory(nodes);
      $('shown').textContent=Math.min(100,nodes.length-page*100)+' '+words.of+' '+nodes.length+' '+words.nodes;
    } else graphViewer.render({data,nodes,view,selected,keyboard,detail:Boolean($('search').value)||$('type').value!=='all'||$('folder').value!=='all'||neighbors});
    $('page').textContent=(page+1)+' / '+Math.max(1,Math.ceil(nodes.length/100));
    $('previous').disabled=page===0;$('next').disabled=(page+1)*100>=nodes.length;
    tree();
  }
  function accept(snapshot) {
    const previousSelection=index.get(selected);
    data=snapshot;index=new Map(data.nodes.map(n=>[n.id,n]));
    if(selected&&!index.has(selected)&&previousSelection){
      const candidates=data.nodes.filter(n=>n.type===previousSelection.type&&n.path===previousSelection.path&&n.label===previousSelection.label);
      const precise=candidates.filter(n=>n.details.signature===previousSelection.details.signature);
      const replacement=precise.length===1?precise[0]:candidates.length===1?candidates[0]:null;
      if(replacement)selected=replacement.id;
    }
    if(selected&&!index.has(selected)){selected=null;$('connection').textContent=words.removed;}
    $('project').textContent=data.project+' · '+words.generation+' '+data.index_generation;
    $('metrics').replaceChildren();
    for(const [count,label] of [[data.nodes.length,words.nodes],[data.edges.length,words.links],[data.nodes.filter(n=>n.type==='memory').length,words.notes]]) {
      const item=text('span',label);item.prepend(text('strong',String(count)));$('metrics').append(item);
    }
    const partial=Object.values(data.coverage).some(v=>['partial','invalid','missing'].includes(v))||data.diagnostics.length;
    $('coverage').textContent=(partial?words.partial:words.verified)+' · '+Object.entries(data.coverage).map(([k,v])=>k+': '+v).join(' / ');
    $('snapshot-time').textContent=new Date(data.generated_at*1000).toLocaleString()+' · '+words.snapshot;
    options();detail();render();
  }
  $('views').onclick=event=>{
    const button=event.target.closest('button[data-view]');if(!button)return;
    view=button.dataset.view;page=0;
    $('views').querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));render();
  };
  for(const id of ['search','type','folder'])$(id).addEventListener(id==='search'?'input':'change',()=>{page=0;render();});
  $('neighbors').onclick=()=>{neighbors=!neighbors;$('neighbors').setAttribute('aria-pressed',String(neighbors));render();};
  $('previous').onclick=()=>{page--;render();};$('next').onclick=()=>{page++;render();};
  $('zoom-in').setAttribute('aria-label',words.zoomIn);$('zoom-out').setAttribute('aria-label',words.zoomOut);
  graphViewer=AikyaMemoryGraph({svg:$('graph'),canvas:$('canvas'),words,choose,refresh:render,motion:()=>motion,
    status(result){$('shown').textContent=result.nodes.length+' '+words.of+' '+filtered().length+' '+words.nodes+' · '+result.grouped+' '+words.grouped+' · '+result.limited+' '+words.limited+(result.omittedEdges?' · '+result.omittedEdges+' '+words.edgeLimit:'');}});
  $('connection').textContent=words.snapshot;accept(data);
  if(document.documentElement.dataset.mode==='live') {
    let generation='',busy=false;
    const base=location.pathname.endsWith('/')?location.pathname:location.pathname+'/';
    async function tick(){
      if(document.hidden||busy)return;busy=true;
      try {
        const response=await fetch(base+'status',{cache:'no-store'});if(!response.ok)throw new Error('unavailable');
        const state=await response.json();$('connection').textContent=state.state;
        if(state.published_generation&&state.published_generation!==generation){
          const incoming=await fetch(base+'snapshot',{cache:'no-store'});if(!incoming.ok)throw new Error('unavailable');
          const current=await incoming.json();accept(current.snapshot);generation=current.generation;
        }
      }catch{$('connection').textContent=words.disconnected;}finally{busy=false;}
    }
    setInterval(tick,2000);document.addEventListener('visibilitychange',tick);tick();
  }
})();

/* Readable screen-size labels, placed around nodes without covering other labels. */
'use strict';
const AikyaMemoryLabels = (groups,positions,camera,selected) => {
  const k=camera.k,placed=[];
  const radius=group=>Math.max(12/k,Number(group.querySelector('.body').getAttribute('r'))+Math.max(2,2/k));
  const offset=group=>Math.max(28/k,radius(group)+16/k);
  const collides=(a,b)=>a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;
  const nodes=[...groups.entries()].filter(([id,g])=>positions.has(id)&&!g.classList.contains('exiting'));
  nodes.sort(([a,ga],[b,gb])=>{
    const priority=(id,g)=>id===selected?0:g.matches(':focus-within, :hover')?1:g.matches('.project,.folder')?2:3;
    return priority(a,ga)-priority(b,gb)||a.localeCompare(b);
  });
  const circles=nodes.map(([id,group])=>{const p=positions.get(id),r=radius(group);return {x:p[0]-r,y:p[1]-r,width:2*r,height:2*r};});
  for(const [id,group] of nodes)if(group.querySelector('.expand')){const p=positions.get(id);circles.push({x:p[0]-offset(group)-14/k,y:p[1]-14/k,width:28/k,height:28/k});}
  for(const [id,group] of nodes) {
    const label=group.querySelector('.label'),position=positions.get(id);
    label.style.fontSize=`${12/k}px`;label.setAttribute('text-anchor','start');
    const width=label.getComputedTextLength(),height=17/k,margin=Math.max(18/k,radius(group)+6/k);
    const choices=[[margin,4/k],[-width-margin,4/k],[-width/2,-margin],[-width/2,margin+height]];
    let chosen=null;
    for(const [x,y] of choices) {
      const box={x:position[0]+x-3/k,y:position[1]+y-height,width:width+6/k,height:height+4/k};
      if(!placed.some(b=>collides(box,b))&&!circles.some(b=>collides(box,b))){chosen={x,y,box};break;}
    }
    // Selection is readable even in a user-created overlap; other labels yield to it.
    if(!chosen&&id===selected)chosen={x:margin,y:4/k,box:{x:position[0]+margin,y:position[1]-height,width,height}};
    label.setAttribute('visibility',chosen?'visible':'hidden');
    if(chosen){label.setAttribute('x',chosen.x);label.setAttribute('y',chosen.y);placed.push(chosen.box);}
    const toggle=group.querySelector('.expand');
    if(toggle){toggle.setAttribute('transform',`translate(${-offset(group)},0) scale(${1/k})`);toggle.setAttribute('visibility','visible');}
    group.querySelector('.hit').setAttribute('r',Math.max(14/k,radius(group)));
  }
};

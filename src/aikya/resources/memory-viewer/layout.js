/* Pure, bounded layouts. Visual grouping never creates source relationships. */
'use strict';
const AikyaMemoryLayout = (() => {
  function structure(nodes, edges) {
    const byID=new Map(nodes.map(n=>[n.id,n])), parent=new Map();
    const children=new Map(nodes.map(n=>[n.id,[]]));
    for(const edge of edges) {
      if(edge.relation!=='contains'||!byID.has(edge.source)||!byID.has(edge.target)||parent.has(edge.target))continue;
      let cursor=edge.source;const seen=new Set([edge.target]);
      while(cursor&&!seen.has(cursor)){seen.add(cursor);cursor=parent.get(cursor);}
      if(cursor)continue; // Reject cyclic containment without hiding its original evidence.
      parent.set(edge.target,edge.source);children.get(edge.source).push(edge.target);
    }
    for(const ids of children.values())ids.sort((a,b)=>byID.get(a).path.localeCompare(byID.get(b).path)||a.localeCompare(b));
    return {byID,parent,children,roots:nodes.filter(n=>!parent.has(n.id)).map(n=>n.id)};
  }
  function project(nodes, tree, expanded, detail, selected, limit=500) {
    const eligible=nodes.filter(node=>{
      if(detail)return true;
      let id=tree.parent.get(node.id);
      while(id){if(!expanded.has(id))return false;id=tree.parent.get(id);}
      return true;
    });
    const chosen=eligible.slice(0,limit);
    const selection=eligible.find(n=>n.id===selected);
    if(selection&&!chosen.includes(selection))chosen[chosen.length-1]=selection;
    return {nodes:chosen,grouped:nodes.length-eligible.length,limited:Math.max(0,eligible.length-limit)};
  }
  function treePositions(nodes, edges) {
    const tree=structure(nodes,edges), positions=new Map();let row=0;
    const stack=tree.roots.slice().reverse().map(id=>[id,0,false]);
    while(stack.length) {
      const [id,depth,done]=stack.pop(), children=tree.children.get(id);
      if(!done&&children.length) {
        stack.push([id,depth,true]);
        for(const child of children.slice().reverse())stack.push([child,depth+1,false]);
      } else {
        const y=children.length?(positions.get(children[0])[1]+positions.get(children.at(-1))[1])/2:80+row++*72;
        positions.set(id,[80+depth*260,y]);
      }
    }
    return positions;
  }
  function arrange(nodes, edges, mode, manual=new Map(), previous=new Map()) {
    if(mode==='graph'&&nodes.length>150)return densePositions(nodes,manual,previous);
    const positions=treePositions(nodes,edges);
    if(mode==='graph') {
      const count=nodes.length, columns=Math.max(1,Math.ceil(Math.sqrt(count)));
      nodes.forEach((n,i)=>positions.set(n.id,previous.get(n.id)||[100+(i%columns)*190,100+Math.floor(i/columns)*100]));
      const ids=new Set(nodes.map(n=>n.id)), links=edges.filter(e=>ids.has(e.source)&&ids.has(e.target)).slice(0,3000);
      for(let step=0;step<28;step++) {
        for(const e of links) {
          const a=positions.get(e.source),b=positions.get(e.target),dx=b[0]-a[0],dy=b[1]-a[1],d=Math.max(1,Math.hypot(dx,dy));
          const force=(d-180)*.018;
          if(!manual.has(e.source))positions.set(e.source,[a[0]+dx/d*force,a[1]+dy/d*force]);
          if(!manual.has(e.target))positions.set(e.target,[b[0]-dx/d*force,b[1]-dy/d*force]);
        }
        separate(nodes,positions,manual,60);
        for(const [id,point] of manual)if(ids.has(id))positions.set(id,[...point]);
      }
      // Resolve the final spring pass; fixed positions are never shifted by collision handling.
      for(let step=0;step<18;step++)separate(nodes,positions,manual,60);
    }
    for(const [id,point] of manual)if(positions.has(id))positions.set(id,[...point]);
    return positions;
  }
  function densePositions(nodes, manual, previous) {
    // Large projections use spatial buckets, avoiding a synchronous quadratic force loop.
    const positions=new Map(),buckets=new Map(),columns=Math.ceil(Math.sqrt(nodes.length));let slot=0;
    const cell=p=>[Math.floor(p[0]/60),Math.floor(p[1]/60)];
    function occupied(p) {
      const [x,y]=cell(p);
      for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)
        for(const other of buckets.get((x+dx)+','+(y+dy))||[])
          if(Math.hypot(p[0]-other[0],p[1]-other[1])<60)return true;
      return false;
    }
    function place(id,p) {
      positions.set(id,[...p]);const key=cell(p).join(',');
      if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(p);
    }
    for(const node of nodes)if(manual.has(node.id))place(node.id,manual.get(node.id));
    for(const node of nodes)if(!positions.has(node.id)) {
      let p=previous.get(node.id);
      if(!p||occupied(p)) {
        do {p=[100+(slot%columns)*190,100+Math.floor(slot/columns)*100];slot++;}while(occupied(p));
      }
      place(node.id,p);
    }
    return positions;
  }
  function separate(nodes, positions, manual, distance) {
    for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++) {
      const a=nodes[i].id,b=nodes[j].id,pa=positions.get(a),pb=positions.get(b);
      let dx=pb[0]-pa[0],dy=pb[1]-pa[1],d=Math.hypot(dx,dy);
      if(d>=distance||manual.has(a)&&manual.has(b))continue;
      if(d<.01){dx=1;dy=0;d=1;}
      const shift=(distance-d)/(manual.has(a)||manual.has(b)?1:2);
      if(!manual.has(a))positions.set(a,[pa[0]-dx/d*shift,pa[1]-dy/d*shift]);
      if(!manual.has(b))positions.set(b,[pb[0]+dx/d*shift,pb[1]+dy/d*shift]);
    }
  }
  function bounds(positions) {
    if(!positions.size)return {x:0,y:0,width:500,height:350};
    const points=[...positions.values()], xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
    const x=Math.min(...xs)-100,y=Math.min(...ys)-60;
    return {x,y,width:Math.max(...xs)-x+230,height:Math.max(...ys)-y+80};
  }
  return {structure,project,arrange,bounds};
})();

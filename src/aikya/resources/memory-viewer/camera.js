/* A camera per view and pointer-safe node manipulation; never writes source data. */
'use strict';
const AikyaMemoryCamera = ({svg,canvas,state,beforeGesture,move,end,labels,motion}) => {
  let gesture=null,suppressUntil=0;
  const point=event=>new DOMPoint(event.clientX,event.clientY).matrixTransform(svg.getScreenCTM().inverse());
  const world=event=>new DOMPoint(event.clientX,event.clientY).matrixTransform(canvas.getScreenCTM().inverse());
  function apply(animate=false) {
    const current=state();if(!current)return;
    canvas.classList.toggle('animate-camera',animate&&motion());
    const {x,y,k}=current.camera;canvas.style.transform=`translate(${x}px,${y}px) scale(${k})`;
    labels();
  }
  function resize() {
    const box=svg.getBoundingClientRect();
    if(box.width&&box.height)svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);
  }
  function fit(animate=false) {
    if(!state())return;
    resize();const box=svg.getBoundingClientRect(),bounds=AikyaMemoryLayout.bounds(state().positions);
    const k=Math.min(2,Math.max(.001,Math.min((box.width-32)/bounds.width,(box.height-32)/bounds.height)));
    state().camera={k,x:box.width/2-(bounds.x+bounds.width/2)*k,y:box.height/2-(bounds.y+bounds.height/2)*k};
    state().fitted=true;apply(animate);
  }
  function zoom(factor,anchor,animate=false) {
    const current=state();if(!current)return;
    const box=svg.getBoundingClientRect(),p=anchor||{x:box.width/2,y:box.height/2};
    const c=current.camera,k=Math.min(5,Math.max(.001,c.k*factor));
    current.camera={k,x:p.x-(p.x-c.x)*k/c.k,y:p.y-(p.y-c.y)*k/c.k};apply(animate);
  }
  function finish(cancel=false) {
    if(!gesture)return;
    const old=gesture;gesture=null;
    if(cancel&&old.moved) {
      if(old.id){move(old.id,old.position);if(old.pin)state().manual.set(old.id,old.pin);else state().manual.delete(old.id);}
      else{state().camera=old.camera;apply();}
    }
    if(old.moved)suppressUntil=performance.now()+350;
    if(old.capture.hasPointerCapture(old.pointer))old.capture.releasePointerCapture(old.pointer);
    svg.classList.remove('dragging');end();labels();
  }
  svg.addEventListener('pointerdown',event=>{
    if(event.button!==0||!state())return;
    suppressUntil=0;
    if(event.target.closest('.expand'))return;
    if(gesture)finish(true);
    beforeGesture();canvas.classList.remove('animate-camera');
    const group=event.target.closest('.node:not(.exiting)'),id=group?.dataset.nodeId;
    gesture={pointer:event.pointerId,id,screen:[event.clientX,event.clientY],point:point(event),world:world(event),
      camera:{...state().camera},position:id?[...state().positions.get(id)]:null,pin:state().manual.get(id),moved:false,capture:group||svg};
    gesture.capture.setPointerCapture(event.pointerId);
  });
  svg.addEventListener('pointermove',event=>{
    if(!gesture||event.pointerId!==gesture.pointer)return;
    const g=gesture;
    if(!g.moved&&Math.hypot(event.clientX-g.screen[0],event.clientY-g.screen[1])<5)return;
    g.moved=true;svg.classList.add('dragging');
    if(g.id) {
      const p=world(event),position=[g.position[0]+p.x-g.world.x,g.position[1]+p.y-g.world.y];
      state().manual.set(g.id,position);move(g.id,position);
    } else {
      const p=point(event);state().camera={...g.camera,x:g.camera.x+p.x-g.point.x,y:g.camera.y+p.y-g.point.y};apply();
    }
  });
  svg.addEventListener('pointerup',()=>finish());
  svg.addEventListener('pointercancel',()=>finish(true));
  svg.addEventListener('lostpointercapture',()=>finish(true));
  svg.addEventListener('click',event=>{
    if(performance.now()<suppressUntil){event.stopImmediatePropagation();event.preventDefault();}
  },true);
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&gesture){event.preventDefault();finish(true);}
  });
  svg.addEventListener('wheel',event=>{
    event.preventDefault();if(!gesture)zoom(Math.exp(-Math.max(-100,Math.min(100,event.deltaY))*.002),point(event));
  },{passive:false});
  new ResizeObserver(()=>{resize();if(state()?.fitted)apply();}).observe(svg);
  return {apply,fit,zoom,resize,cancel:()=>finish(true),nudge(id,dx,dy){
    beforeGesture();canvas.classList.remove('animate-camera');const p=state().positions.get(id),k=state().camera.k;
    const next=[p[0]+dx/k,p[1]+dy/k];state().manual.set(id,next);move(id,next);end();labels();
  }};
};

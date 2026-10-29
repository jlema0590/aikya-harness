/* Run with node --test tests/memory_layout.test.cjs. No DOM or third-party library. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = path.join(__dirname, '../src/aikya/resources/memory-viewer/layout.js');
function layout() {
  assert.ok(fs.existsSync(source), 'A collision-aware, expandable source layout must be provided');
  return vm.runInNewContext(fs.readFileSync(source, 'utf8') + '\nAikyaMemoryLayout;');
}
const node = (id, type='file') => ({id, type, label:id, path:id});
const edge = (source, target, relation='contains') => ({id:source+'|'+target, source, target, relation});

test('architecture reserves space for every sibling and puts parents before children', () => {
  const api = layout(), nodes = [node('root','project'), ...Array.from({length:275},(_,i)=>node('file'+i))];
  const positions = api.arrange(nodes, nodes.slice(1).map(n=>edge('root',n.id)), 'architecture');
  const ys = nodes.slice(1).map(n=>positions.get(n.id)[1]).sort((a,b)=>a-b);
  assert.ok(ys.at(-1)-ys[0] >= 274*60, 'a fixed canvas must not squeeze siblings together');
  assert.ok(ys.slice(1).every((y,i)=>y-ys[i]>=60));
  assert.ok(nodes.slice(1).every(n=>positions.get(n.id)[0]>positions.get('root')[0]));
});
test('collapsed folders keep descendants accessible when searching and report hidden counts', () => {
  const api=layout(), nodes=[node('root','project'),node('folder','folder'),node('file'),node('symbol','class')];
  const tree=api.structure(nodes,[edge('root','folder'),edge('folder','file'),edge('file','symbol')]);
  const overview=api.project(nodes,tree,new Set(['root']),false,null);
  assert.deepEqual(Array.from(overview.nodes,n=>n.id),['root','folder']);
  assert.equal(overview.grouped,2);
  assert.deepEqual(Array.from(api.project([nodes[3]],tree,new Set(),true,null).nodes,n=>n.id),['symbol']);
});
test('projection bounds visible nodes without losing the true omission counts or selection', () => {
  const api=layout(), nodes=Array.from({length:1001},(_,i)=>node('n'+i));
  const result=api.project(nodes,api.structure(nodes,[]),new Set(),true,'n1000');
  assert.equal(result.nodes.length,500);assert.equal(result.limited,501);assert.equal(result.grouped,0);
  assert.ok(result.nodes.some(n=>n.id==='n1000'));
});
test('cyclic and missing containment endpoints cannot trap a layout traversal', () => {
  const api=layout(), nodes=[node('a','folder'),node('b','folder'),node('orphan')];
  const edges=[edge('a','b'),edge('b','a'),edge('missing','orphan')];
  const positions=api.arrange(nodes,edges,'architecture');
  assert.equal(positions.size,3);assert.ok([...positions.values()].flat().every(Number.isFinite));
});
for(const size of [100,500])test('network separates '+size+' node centers and respects manually pinned positions', () => {
  const api=layout(), nodes=Array.from({length:size},(_,i)=>node('n'+i));
  const edges=nodes.slice(1).map(n=>edge('n0',n.id));
  const started=performance.now();
  const positions=api.arrange(nodes,edges,'graph',new Map([['n0',[80,80]]]));
  if(size===500)assert.ok(performance.now()-started<500,'dense layout must not block the browser for half a second');
  assert.deepEqual(Array.from(positions.get('n0')),[80,80]);
  let minimum=Infinity;
  for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++) {
    const a=positions.get(nodes[i].id),b=positions.get(nodes[j].id);
    minimum=Math.min(minimum,Math.hypot(a[0]-b[0],a[1]-b[1]));
  }
  assert.ok(minimum>=40,'network nodes need a safe collision distance: '+minimum);
});

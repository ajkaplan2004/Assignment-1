// Captures a full-page, high-DPI PNG of the dashboard via Chrome DevTools Protocol.
// Chrome must be running headless with --remote-debugging-port=9222 and the page loaded.
const fs = require('fs');
const http = require('http');

const CDP = 'http://localhost:9222/json';
const WIDTH = 1280;
const SCALE = 2;

function get(url){ return new Promise((res,rej)=>{ http.get(url,r=>{ let d=''; r.on('data',c=>d+=c); r.on('end',()=>res(JSON.parse(d))); }).on('error',rej); }); }

(async () => {
  const targets = await get(CDP);
  const page = targets.find(t => t.type === 'page' && t.url.includes('dashboard.html'));
  if (!page) { console.error('dashboard.html target not found; targets:', targets.map(t=>t.url)); process.exit(1); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const pending = {};
  const send = (method, params={}) => new Promise((res,rej)=>{
    const mid = ++id; pending[mid] = {res,rej};
    ws.send(JSON.stringify({id:mid, method, params}));
  });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending[m.id]) { m.error ? pending[m.id].rej(m.error) : pending[m.id].res(m.result); delete pending[m.id]; } };
  ws.onerror = e => { console.error('ws error', e); process.exit(1); };
  await new Promise(r => ws.onopen = r);

  await send('Page.enable');
  await send('DOM.enable');
  // wait for network/JS to settle
  await new Promise(r => setTimeout(r, 1200));
  const { result } = await send('Runtime.evaluate', { expression: '({h:document.documentElement.scrollHeight, w:document.documentElement.scrollWidth})', returnByValue:true });
  const H = result.value.h, W = result.value.w;
  console.log('page size', W, 'x', H, 'css px');
  await send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: H, deviceScaleFactor: SCALE, mobile: false });
  await new Promise(r => setTimeout(r, 400));
  const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, fromSurface: true });
  const out = process.argv[2];
  fs.writeFileSync(out, Buffer.from(shot.data, 'base64'));
  console.log('saved', out, (Buffer.from(shot.data,'base64').length/1e6).toFixed(2), 'MB');
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });

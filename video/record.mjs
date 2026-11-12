// Records one continuous take of the real map page (1080x1350, 4:5) for LinkedIn and the README:
// a visible cursor clicking the real controls, a slow camera, one caption at a time.
// Page animations are stepped frame by frame, so the video is smooth and the same every run.
// Usage: PUPPETEER_FROM=/path/to/node_modules/ node video/record.mjs        (needs ffmpeg and gifski)
//        FOR=linkedin ... makes the cut that says "link in the comments"
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
const require = createRequire(process.env.PUPPETEER_FROM || path.join(process.cwd(), 'node_modules/'));
const puppeteer = require('puppeteer');
const dir = path.dirname(fileURLToPath(import.meta.url));
const frames = path.join(dir, '.frames'); fs.rmSync(frames, { recursive: true, force: true }); fs.mkdirSync(frames);
const FPS = 30, W = 1080, H = 1350, TOP = 190, BOT = 110, PAGE_W = 720, LI = process.env.FOR === 'linkedin';
const b = await puppeteer.launch({ headless: 'shell', protocolTimeout: 600000 });
const p = await b.newPage();
const errs = []; p.on('pageerror', e => errs.push(String(e)));
await p.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
await p.goto(pathToFileURL(path.join(dir, '..', 'examples', 'plant-2', 'out', 'graph.html')).href + '#rec', { waitUntil: 'networkidle0' });
await p.evaluate(() => document.fonts.ready);

await p.addStyleTag({ content: `
  html,body{overflow:hidden !important;background:#F5F6F8 !important}
  #cam{position:absolute;left:0;top:0;width:${PAGE_W}px;transform-origin:0 0;background:#F5F6F8}
  #topb{position:fixed;left:0;right:0;top:0;height:${TOP}px;background:#0B1220;display:flex;align-items:center;justify-content:center;padding:0 56px;box-sizing:border-box;z-index:50}
  #topb div{font:700 45px/1.18 Inter,sans-serif;letter-spacing:-.8px;color:#fff;text-align:center}
  #botb{position:fixed;left:0;right:0;bottom:0;height:${BOT}px;background:#0B1220;display:flex;align-items:center;justify-content:center;gap:14px;z-index:50;font:600 26px Inter,sans-serif;color:#fff}
  #botb i{width:22px;height:22px;border-radius:5px;background:#F06050;display:inline-block}#botb span{color:#94A3B8;font-weight:500}
  #cur{position:fixed;left:0;top:0;width:34px;height:34px;z-index:60;pointer-events:none;filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
  #rip{position:fixed;width:56px;height:56px;margin:-28px 0 0 -28px;border-radius:50%;border:4px solid #F06050;z-index:59;pointer-events:none;opacity:0}
  #cam header,#cam #cap,#cam footer,#cam .tip{display:none !important}
  #cam .wrap{padding:0 14px !important;max-width:none !important}
  #cam .story{padding:14px 0 12px !important}#cam .steps{flex-wrap:nowrap;gap:5px}#cam .steps button{font-size:12.5px;padding:8px 11px}
  #cam main{grid-template-columns:1fr !important;gap:12px}
  #cam svg#g{height:${Math.round((PAGE_W - 30) * 0.66)}px !important}
  #cam .ask label{display:block;font-size:14px}#cam .ask input{font-size:17px;font-weight:600}
  #cam .panel{max-height:none !important;overflow:visible !important;padding:18px 18px 400px}
  #cam .panel h2{font-size:25px}#cam .panel .sub{font-size:14.5px}
  #cam .sum b{font-size:44px}#cam .sum span{font-size:15px}#cam .sum div{padding:14px 14px 12px}
  #cam .iss b{font-size:17px}#cam .iss small{font-size:14.5px}#cam .q div{font-size:15.5px;line-height:1.45;padding:4px 0 4px 11px;margin-top:9px}#cam .q div b{font-size:15px}
  #cam .grp{font-size:15px}#cam .it b{font-size:15.5px}#cam .it small{font-size:13.5px}
  #cam .legend{font-size:10.5px;padding:5px 8px;gap:4px 9px}
` });
await p.evaluate(() => {
  const cam = document.createElement('div'); cam.id = 'cam';
  while (document.body.firstChild) cam.appendChild(document.body.firstChild);
  document.body.appendChild(cam);
  const add = h => { const d = document.createElement('div'); d.innerHTML = h; const e = d.firstElementChild; document.body.appendChild(e); return e; };
  add('<div id="topb"><div id="capt"></div></div>');
  add('<div id="botb"><i></i>SOP Graph<span>· free Claude skill · built by Ivan Getov</span></div>');
  add('<svg id="cur" viewBox="0 0 24 24"><path d="M4 2 L4 20 L9 15.5 L12.5 22.5 L15.5 21 L12 14 L19 14 Z" fill="#fff" stroke="#0B1220" stroke-width="1.6" stroke-linejoin="round"/></svg>');
  add('<div id="rip"></div>');
  window.__C = { tx: 0, ty: 0, s: 1, cx: 820, cy: 1100 }; window.__vt = 0;
  window.__R = {
    rect(sel) { const e = typeof sel === 'string' ? document.querySelector(sel) : sel, r = e.getBoundingClientRect(), C = __C;
      return { x: (r.left - C.tx) / C.s, y: (r.top - C.ty) / C.s, w: r.width / C.s, h: r.height / C.s }; },
    fit(r, top, bot, W, H, pad) { const aw = W - 2 * pad, ah = H - top - bot - 2 * pad, s = Math.min(aw / r.w, ah / r.h);
      return { s, tx: W / 2 - (r.x + r.w / 2) * s, ty: top + (H - top - bot) / 2 - (r.y + r.h / 2) * s }; },
    set(v) { Object.assign(__C, v); document.getElementById('cam').style.transform = `translate(${v.tx}px,${v.ty}px) scale(${v.s})`; },
    cap(t) { document.getElementById('capt').innerHTML = t; },
    cur(x, y) { __C.cx = x; __C.cy = y; document.getElementById('cur').style.transform = `translate(${x - 6}px,${y - 3}px)`; },
    el(sel, text) { return text ? [...document.querySelectorAll(sel)].find(x => x.textContent.includes(text)) : document.querySelector(sel); },
    target(sel, text, fx = 0.5, fy = 0.6) { const r = this.el(sel, text).getBoundingClientRect(); return { x: r.left + r.width * fx, y: r.top + Math.min(r.height * fy, 40) }; },
    click(sel, text) { this.el(sel, text).click(); },
    rip(o, sc) { const r = document.getElementById('rip'); r.style.left = __C.cx + 'px'; r.style.top = __C.cy + 'px'; r.style.opacity = o; r.style.transform = `scale(${sc})`; },
    // step every CSS transition by hand so captured frames are evenly spaced in time
    tick(dt) { __vt += dt; for (const a of document.getAnimations()) { if (a.__t0 === undefined) a.__t0 = __vt - dt; a.pause();
        const end = a.effect.getComputedTiming().endTime, t = __vt - a.__t0; if (t >= end) a.finish(); else a.currentTime = t; } },
  };
});

const R = (fn, ...a) => p.evaluate((fn, a) => __R[fn](...a), fn, a);
let fi = 0, cam = null;
const cdp = await p.createCDPSession();
const snap = async () => { const { data } = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 92 }); fs.writeFileSync(path.join(frames, String(fi++).padStart(5, '0') + '.jpg'), Buffer.from(data, 'base64')); };
const ease = x => x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2, lerp = (a, b, t) => a + (b - a) * t;
const frame = async (o = {}) => {
  await R('tick', 1000 / FPS);
  if (o.cam) await R('set', o.cam);
  if (o.cur) await R('cur', o.cur.x, o.cur.y);
  if (o.rip) await R('rip', o.rip[0], o.rip[1]);
  await p.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  await snap();
};
const hold = async sec => { for (let k = 0; k < Math.round(sec * FPS); k++) await frame(); };
const camTo = async (target, sec, pad = 20) => { const to = await R('fit', target, TOP, BOT, W, H, pad), from = cam;
  for (let k = 1; k <= Math.round(sec * FPS); k++) { const t = ease(k / (sec * FPS)); cam = { s: lerp(from.s, to.s, t), tx: lerp(from.tx, to.tx, t), ty: lerp(from.ty, to.ty, t) }; await frame({ cam }); } };
const moveTo = async (sel, text, fx, fy) => { const from = await p.evaluate(() => ({ x: __C.cx, y: __C.cy })), to = await R('target', sel, text, fx, fy), n = Math.round(0.7 * FPS);
  for (let k = 1; k <= n; k++) { const t = ease(k / n); await frame({ cur: { x: lerp(from.x, to.x, t), y: lerp(from.y, to.y, t) - Math.sin(t * Math.PI) * 26 } }); } };
const ripple = async () => { for (let k = 0; k < 9; k++) await frame({ rip: [1 - k / 9, 0.5 + k / 9] }); await R('rip', 0, 1); };
const clickOn = async (sel, text) => { await moveTo(sel, text); await R('click', sel, text); await ripple(); };
const rectOf = sel => p.evaluate(sel => __R.rect(sel), sel);
const box = (r, x, y, w, h) => ({ x: r.x + r.w * x, y: r.y + r.h * y, w: r.w * w, h: r.h * h });

// framings (page space)
const map = await rectOf('.gwrap'), svg = await rectOf('svg#g'), story = await rectOf('.story');
const whole = { x: 0, y: story.y - 4, w: PAGE_W, h: (H - TOP - BOT) * PAGE_W / W };         // pills, ask box, map, top of the panel
const pagesIn = box(svg, 0.16, 0.30, 0.50, 0.62);                                           // a few documents, close up
const ex = await p.evaluate(() => { const n = __sg.example; return { id: n.id, name: n.type === 'equipment' ? n.id : n.name, q: __sg.question }; });
const said = ex.q ? ex.q.replace(/\s*What.*$/, '').replace(/\.$/, '') : null;

cam = await R('fit', pagesIn, TOP, BOT, W, H, 0); await R('set', cam); await R('cur', 860, 1120);

// 1. what this is: real documents, close up, then all of them
await R('cap', 'I built a Claude skill that turns<br>your SOPs into a knowledge graph.');
await hold(1.0); await camTo(box(svg, 0.10, 0.22, 0.62, 0.74), 2.4, 0);
await R('cap', '20 procedures. 42 pages.<br>Different authors, different years.');
await camTo(whole, 1.6, 0); await hold(1.0);
// 2. the graph
await clickOn('#steps button', '2 ·');
await R('cap', 'Claude reads every page<br>and links them together.');
await hold(2.7);
// 3. change one thing: type it into the real box
await R('cap', 'Then ask it a question:<br>“We’re switching label supplier.”');
await camTo({ x: 0, y: map.y - 6, w: PAGE_W, h: 600 }, 0.9, 0);
await moveTo('#q', null, 0.2, 0.5); await ripple();
await p.evaluate(() => { __sg.setStep(2, true); document.getElementById('q').focus(); });
for (let k = 1; k <= ex.name.length; k++) { await p.evaluate(v => { document.getElementById('q').value = v; }, ex.name.slice(0, k)); await hold(0.11); }
await hold(0.25);
await p.evaluate((id, said) => { document.getElementById('q').blur(); __sg.pick(id, said); }, ex.id, said);
await hold(1.6);
const sum = await rectOf('#panel .sum');
await R('cap', 'Every procedure, role and form<br>that change touches lights up.');
await camTo({ x: 0, y: sum.y + sum.h + 30 - whole.h, w: PAGE_W, h: whole.h }, 1.3, 0);
await hold(2.7);
// 4. what doesn't add up
await camTo(whole, 1.0, 0);
await clickOn('#steps button', '4 ·');
await R('cap', 'It also finds where your<br>procedures disagree.');
await hold(2.2);
const card = await p.evaluate(() => { const e = [...document.querySelectorAll('#panel .iss')].find(x => /torque/i.test(x.textContent)) || document.querySelector('#panel .iss'); e.id = 'vidcard'; return __R.rect(e); });
await camTo({ x: 0, y: card.y + 190 - whole.h * 0.62, w: PAGE_W, h: whole.h }, 1.3, 0);
await clickOn('#vidcard');
await R('cap', 'Same cap. One procedure says 17.<br>Another still says 15.');
await hold(3.9);
// 5. the ask: back to the whole graph
await R('cap', 'Free Claude skill. Download it<br>and try it on your own procedures.');
await p.evaluate(LI => { document.querySelector('#botb').innerHTML = LI ? '<i></i>Free download<span>· link in the comments</span>' : '<i></i>SOP Graph<span>· github.com/ivanegetov-lab/sop-graph</span>'; }, LI);
await camTo(whole, 1.2, 0);
await clickOn('#steps button', '2 ·');
await hold(2.4);
await b.close();
if (errs.length) console.log('page errors:', errs);
console.log(fi, 'frames,', (fi / FPS).toFixed(1), 's');

const base = LI ? 'sop-graph-linkedin' : 'sop-graph-demo', mp4 = path.join(dir, base + '.mp4'), gif = path.join(dir, base + '.gif');
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', path.join(frames, '%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'slow', '-movflags', '+faststart', mp4]);
const gf = path.join(dir, '.gif'); fs.rmSync(gf, { recursive: true, force: true }); fs.mkdirSync(gf);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', mp4, '-vf', 'fps=12,scale=540:-1:flags=lanczos', path.join(gf, '%04d.png')]);
execFileSync('gifski', ['--quiet', '--fps', '12', '--width', '540', '--quality', '80', '-o', gif, ...fs.readdirSync(gf).sort().map(f => path.join(gf, f))]);
fs.rmSync(gf, { recursive: true, force: true }); fs.rmSync(frames, { recursive: true, force: true });
for (const f of [mp4, gif]) console.log(path.basename(f), (fs.statSync(f).size / 1e6).toFixed(2), 'MB');

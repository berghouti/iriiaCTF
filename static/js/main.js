async function submitFlag(slug) {
  const input = document.getElementById('flag-input');
  const msg   = document.getElementById('flag-msg');
  const flag  = input.value.trim();
  if (!flag) { showMsg(msg,'Enter your flag first.',false); return; }

  const res  = await fetch(`/submit/${slug}`, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({flag})
  });
  const data = await res.json();

  if (data.ok) {
    showMsg(msg, data.msg, true);
    document.querySelector('.flag-form').style.borderColor='var(--accent2)';
    const btn = document.getElementById('submit-btn');
    if (btn) { btn.textContent='✓ SOLVED'; btn.disabled=true; }
    if (data.points) updateNavScore(data.points);
    launchConfetti();
  } else {
    showMsg(msg, data.msg, false);
    input.classList.add('shake');
    setTimeout(()=>input.classList.remove('shake'), 500);
  }
}

function showMsg(el, text, ok) {
  el.textContent = text;
  el.className = 'flag-msg ' + (ok ? 'ok' : 'err');
}

function updateNavScore(pts) {
  const el = document.getElementById('nav-score');
  if (!el) return;
  const cur = parseInt(el.textContent)||0;
  el.textContent = cur + pts;
}

function toggleHint() {
  const box = document.getElementById('hint-box');
  if (!box) return;
  box.classList.toggle('show');
  const btn = document.getElementById('hint-btn');
  if (btn) btn.textContent = box.classList.contains('show') ? '▲ Hide Hint' : '▼ Show Hint';
}

document.addEventListener('DOMContentLoaded', () => {
  const inp = document.getElementById('flag-input');
  if (inp) {
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter') submitFlag(inp.dataset.slug);
    });
  }
  // auto-dismiss flashes
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(()=>{ el.style.opacity='0'; el.style.transition='opacity .5s';
      setTimeout(()=>el.remove(),500); }, 3500);
  });
  // terminal typing
  document.querySelectorAll('.type-line').forEach((el,i) => {
    const text = el.dataset.text||'';
    el.textContent='';
    setTimeout(()=>typeText(el,text), i*600);
  });
});

function typeText(el, text, i=0) {
  if (i<text.length) {
    el.textContent += text[i];
    setTimeout(()=>typeText(el,text,i+1), 30+Math.random()*20);
  }
}

function launchConfetti() {
  const colors=['#00d4ff','#00ff9d','#ffd700','#ff4d6d'];
  for(let i=0;i<70;i++){
    const el=document.createElement('div');
    el.style.cssText=`position:fixed;top:50%;left:50%;width:8px;height:8px;
      background:${colors[i%4]};pointer-events:none;z-index:9999;
      border-radius:${Math.random()>.5?'50%':'0'};`;
    document.body.appendChild(el);
    const angle=Math.random()*Math.PI*2, dist=100+Math.random()*300;
    el.animate([
      {transform:'translate(-50%,-50%) scale(1)',opacity:1},
      {transform:`translate(calc(-50% + ${Math.cos(angle)*dist}px),calc(-50% + ${Math.sin(angle)*dist}px)) scale(0)`,opacity:0}
    ],{duration:700+Math.random()*400,easing:'ease-out'}).onfinish=()=>el.remove();
  }
}

const style=document.createElement('style');
style.textContent=`.shake{animation:shake .4s ease;}@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}`;
document.head.appendChild(style);
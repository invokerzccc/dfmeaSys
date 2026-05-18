/**
 * DFMEA System — Core Utilities
 * 3 palettes x Light/Dark/Auto, fixed theme FAB
 */

// ---- API Wrapper ----
var API = {
  get: async function (url) { var r = await fetch(url); if (!r.ok) throw new Error(await r.text()); return r.json(); },
  post: async function (url, data) { var r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); if (!r.ok) throw new Error(await r.text()); return r.json(); },
  put: async function (url, data) { var r = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }); if (!r.ok) throw new Error(await r.text()); return r.json(); },
  del: async function (url) { var r = await fetch(url, { method: 'DELETE' }); if (!r.ok) throw new Error(await r.text()); return r.json(); },
};

// ---- Toast ----
function showToast(message, type, undoCallback) {
  type = type || 'info';
  var container = document.querySelector('.toast-container');
  if (!container) { container = document.createElement('div'); container.className = 'toast-container'; document.body.appendChild(container); }
  var toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  toast.innerHTML = '<span>' + message + '</span>';
  if (undoCallback) {
    var undo = document.createElement('span');
    undo.className = 'toast-undo';
    undo.textContent = '撤销';
    undo.onclick = function () { toast.remove(); undoCallback(); };
    toast.appendChild(undo);
  }
  container.appendChild(toast);
  setTimeout(function () { if (toast.parentNode) toast.remove(); }, undoCallback ? 5000 : 3000);
}

// ---- Date Formatting ----
function formatDate(dateStr) {
  if (!dateStr) return '';
  var d = new Date(dateStr);
  var pad = function (n) { return String(n).padStart(2, '0'); };
  return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
}

// ---- Debounce ----
function debounce(fn, ms) {
  ms = ms || 300;
  var timer;
  return function () {
    var ctx = this, args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
  };
}

// ---- RPN Calculation ----
function calcRPN(S, O, D) { return (S || 1) * (O || 1) * (D || 1); }

// ---- AP Matrix (AIAG-VDA 2019) ----
function calcAP(S, O, D) {
  var rules = [
    [9,10, 9,10, 1,10,'H'], [9,10, 7,8, 1,10,'H'], [9,10, 4,6, 1,9,'H'], [9,10, 4,6, 10,10,'M'],
    [9,10, 2,3, 1,7,'H'], [9,10, 2,3, 8,9,'M'], [9,10, 2,3, 10,10,'L'],
    [9,10, 1,1, 1,2,'H'], [9,10, 1,1, 3,5,'M'], [9,10, 1,1, 6,10,'L'],
    [7,8, 9,10, 1,10,'H'], [7,8, 7,8, 1,8,'H'], [7,8, 7,8, 9,10,'M'],
    [7,8, 4,6, 1,5,'H'], [7,8, 4,6, 6,10,'M'], [7,8, 2,3, 1,3,'H'], [7,8, 2,3, 4,8,'M'], [7,8, 2,3, 9,10,'L'],
    [7,8, 1,1, 1,5,'M'], [7,8, 1,1, 6,10,'L'], [4,6, 9,10, 1,10,'H'], [4,6, 7,8, 1,7,'H'], [4,6, 7,8, 8,10,'M'],
    [4,6, 4,6, 1,3,'H'], [4,6, 4,6, 4,10,'M'], [4,6, 2,3, 1,1,'H'], [4,6, 2,3, 2,7,'M'], [4,6, 2,3, 8,10,'L'],
    [4,6, 1,1, 1,4,'M'], [4,6, 1,1, 5,10,'L'], [2,3, 9,10, 1,10,'H'], [2,3, 7,8, 1,5,'H'], [2,3, 7,8, 6,10,'M'],
    [2,3, 4,6, 1,2,'H'], [2,3, 4,6, 3,8,'M'], [2,3, 4,6, 9,10,'L'], [2,3, 2,3, 1,1,'H'], [2,3, 2,3, 2,5,'M'], [2,3, 2,3, 6,10,'L'],
    [2,3, 1,1, 1,2,'M'], [2,3, 1,1, 3,10,'L'], [1,1, 9,10, 1,10,'H'], [1,1, 7,8, 1,5,'H'], [1,1, 7,8, 6,10,'M'],
    [1,1, 4,6, 1,2,'H'], [1,1, 4,6, 3,8,'M'], [1,1, 4,6, 9,10,'L'], [1,1, 2,3, 1,1,'H'], [1,1, 2,3, 2,5,'M'], [1,1, 2,3, 6,10,'L'],
    [1,1, 1,1, 1,2,'M'], [1,1, 1,1, 3,10,'L'],
  ];
  for (var i = 0; i < rules.length; i++) {
    var r = rules[i];
    if (S >= r[0] && S <= r[1] && O >= r[2] && O <= r[3] && D >= r[4] && D <= r[5]) return r[6];
  }
  return 'L';
}

// ---- RPN Level ----
function rpnLevel(rpn) {
  if (rpn >= 200) return 'H';
  if (rpn >= 100) return 'M';
  return 'L';
}

// ---- Theme (Sage light/dark only) ----
(function initTheme() {
  var mode = localStorage.getItem('dfmea-mode');
  if (mode === 'light' || mode === 'dark') document.documentElement.setAttribute('data-theme', mode);
  if (!document.getElementById('theme-fab')) {
    var fab = document.createElement('button');
    fab.id = 'theme-fab';
    fab.className = 'theme-fab';
    fab.title = '切换浅色/深色模式';
    fab.innerHTML = '&#9788;';
    fab.onclick = function () { toggleTheme(); };
    document.body.appendChild(fab);
  }
  updateThemeIcon();
})();

function toggleTheme() {
  var cur = document.documentElement.getAttribute('data-theme');
  var next = (cur === 'dark') ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('dfmea-mode', next);
  updateThemeIcon();
}

function updateThemeIcon() {
  var fab = document.getElementById('theme-fab');
  if (!fab) return;
  var cur = document.documentElement.getAttribute('data-theme');
  fab.innerHTML = (cur === 'dark') ? '&#9789;' : '&#9788;';
}

// ---- Confirm Dialog ----
function confirmDlg(message) {
  return new Promise(function (resolve) {
    var overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML =
      '<div class="modal" style="min-width:320px;max-width:440px">' +
        '<p style="margin-bottom:1.2rem;line-height:1.6">' + message + '</p>' +
        '<div class="modal-actions">' +
          '<button class="btn btn-ghost modal-cancel">取消</button>' +
          '<button class="btn btn-danger modal-confirm">确认删除</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);
    overlay.querySelector('.modal-cancel').onclick = function () { overlay.remove(); resolve(false); };
    overlay.querySelector('.modal-confirm').onclick = function () { overlay.remove(); resolve(true); };
  });
}

// ---- Column Resize ----
function initColumnResize(table) {
  if (!table || table.dataset.resizeReady) return;
  table.dataset.resizeReady = '1';
  var ths = table.querySelectorAll('th');
  ths.forEach(function (th) {
    var handle = document.createElement('div');
    handle.className = 'col-resize';
    th.appendChild(handle);
    var startX, startW, col;
    handle.addEventListener('mousedown', function (e) {
      e.preventDefault();
      col = th; startX = e.clientX; startW = col.offsetWidth;
      handle.classList.add('active'); table.classList.add('resizing');
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
    function onMove(e) { var w = Math.max(40, startW + (e.clientX - startX)); col.style.width = w + 'px'; col.style.minWidth = w + 'px'; }
    function onUp() { handle.classList.remove('active'); table.classList.remove('resizing'); document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); }
  });
}

// ---- Modal Resize (4 edges + 4 corners) ----
function initModalResize(modal) {
  if (modal.querySelector('.modal-resize-handle')) return;
  var dirs = ['n','s','e','w','ne','nw','se','sw'];
  dirs.forEach(function (dir) {
    var h = document.createElement('div');
    h.className = 'modal-resize-handle modal-resize-' + dir;
    h.setAttribute('data-dir', dir);
    modal.appendChild(h);
    h.addEventListener('mousedown', function (e) {
      e.preventDefault(); e.stopPropagation();
      var rect = modal.getBoundingClientRect();
      var startX = e.clientX, startY = e.clientY;
      var startW = rect.width, startH = rect.height;
      var startL = rect.left, startT = rect.top;
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
      function onMove(ev) {
        var dx = ev.clientX - startX, dy = ev.clientY - startY;
        var w = startW, h = startH;
        if (dir.indexOf('e') >= 0) w = Math.max(360, startW + dx);
        if (dir.indexOf('w') >= 0) w = Math.max(360, startW - dx);
        if (dir.indexOf('s') >= 0) h = Math.max(200, startH + dy);
        if (dir.indexOf('n') >= 0) h = Math.max(200, startH - dy);
        modal.style.width = w + 'px';
        modal.style.maxWidth = w + 'px';
        modal.style.minHeight = h + 'px';
        modal.style.height = h + 'px';
      }
      function onUp() {
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }
    });
  });
}

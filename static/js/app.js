/**
 * DFMEA 个人记录系统 — 全局工具函数
 */

// --- API 封装 ---
const API = {
    async get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    async put(url, data) {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
    async del(url) {
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
    },
};

// --- Toast 通知 ---
function showToast(message, type = 'info', undoCallback = null) {
    const container = document.querySelector('.toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    if (undoCallback) {
        const undo = document.createElement('span');
        undo.className = 'toast-undo';
        undo.textContent = '撤销';
        undo.onclick = () => { toast.remove(); undoCallback(); };
        toast.appendChild(undo);
    }
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, undoCallback ? 5000 : 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// --- 日期格式化 ---
function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// --- Debounce ---
function debounce(fn, ms = 300) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// --- RPN 计算 ---
function calcRPN(S, O, D) {
    return (S || 1) * (O || 1) * (D || 1);
}

// --- AP 判定（AIAG-VDA 查表）---
function calcAP(S, O, D) {
    const rules = [
        [9,10, 9,10, 1,10,'H'], [9,10, 7,8, 1,10,'H'],
        [9,10, 4,6, 1,9,'H'], [9,10, 4,6, 10,10,'M'],
        [9,10, 2,3, 1,7,'H'], [9,10, 2,3, 8,9,'M'], [9,10, 2,3, 10,10,'L'],
        [9,10, 1,1, 1,2,'H'], [9,10, 1,1, 3,5,'M'], [9,10, 1,1, 6,10,'L'],
        [7,8, 9,10, 1,10,'H'], [7,8, 7,8, 1,8,'H'], [7,8, 7,8, 9,10,'M'],
        [7,8, 4,6, 1,5,'H'], [7,8, 4,6, 6,10,'M'],
        [7,8, 2,3, 1,3,'H'], [7,8, 2,3, 4,8,'M'], [7,8, 2,3, 9,10,'L'],
        [7,8, 1,1, 1,5,'M'], [7,8, 1,1, 6,10,'L'],
        [4,6, 9,10, 1,10,'H'], [4,6, 7,8, 1,7,'H'], [4,6, 7,8, 8,10,'M'],
        [4,6, 4,6, 1,3,'H'], [4,6, 4,6, 4,10,'M'],
        [4,6, 2,3, 1,1,'H'], [4,6, 2,3, 2,7,'M'], [4,6, 2,3, 8,10,'L'],
        [4,6, 1,1, 1,4,'M'], [4,6, 1,1, 5,10,'L'],
        [2,3, 9,10, 1,10,'H'], [2,3, 7,8, 1,5,'H'], [2,3, 7,8, 6,10,'M'],
        [2,3, 4,6, 1,2,'H'], [2,3, 4,6, 3,8,'M'], [2,3, 4,6, 9,10,'L'],
        [2,3, 2,3, 1,1,'H'], [2,3, 2,3, 2,5,'M'], [2,3, 2,3, 6,10,'L'],
        [2,3, 1,1, 1,2,'M'], [2,3, 1,1, 3,10,'L'],
        [1,1, 9,10, 1,10,'H'], [1,1, 7,8, 1,5,'H'], [1,1, 7,8, 6,10,'M'],
        [1,1, 4,6, 1,2,'H'], [1,1, 4,6, 3,8,'M'], [1,1, 4,6, 9,10,'L'],
        [1,1, 2,3, 1,1,'H'], [1,1, 2,3, 2,5,'M'], [1,1, 2,3, 6,10,'L'],
        [1,1, 1,1, 1,2,'M'], [1,1, 1,1, 3,10,'L'],
    ];
    for (const [s1,s2,o1,o2,d1,d2,ap] of rules) {
        if (S >= s1 && S <= s2 && O >= o1 && O <= o2 && D >= d1 && D <= d2) return ap;
    }
    return 'L';
}

// --- RPN 高亮等级 ---
function rpnLevel(rpn) {
    if (rpn >= 200) return 'H';
    if (rpn >= 100) return 'M';
    return 'L';
}

// --- Modal ---
function openModal(title, contentHtml, onSave) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal">
            <h2>${title}</h2>
            <div class="modal-body">${contentHtml}</div>
            <div class="modal-actions">
                <button class="btn btn-ghost modal-cancel">取消</button>
                <button class="btn btn-primary modal-save">保存</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelector('.modal-cancel').onclick = () => overlay.remove();
    overlay.querySelector('.modal-save').onclick = () => {
        if (onSave(overlay) !== false) overlay.remove();
    };
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    return overlay;
}

// --- 主题切换 ---
(function initTheme() {
    const saved = localStorage.getItem('dfmea-theme');
    if (saved === 'light' || saved === 'dark') {
        document.documentElement.setAttribute('data-theme', saved);
    }
})();

function cycleTheme() {
    const themes = ['auto', 'light', 'dark'];
    const current = localStorage.getItem('dfmea-theme') || 'auto';
    const next = themes[(themes.indexOf(current) + 1) % themes.length];

    if (next === 'auto') {
        document.documentElement.removeAttribute('data-theme');
        localStorage.removeItem('dfmea-theme');
    } else {
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('dfmea-theme', next);
    }
}

// --- 确认对话框 ---
function confirmDlg(message) {
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.innerHTML = `
            <div class="modal" style="min-width:320px">
                <p style="margin-bottom:1rem">${message}</p>
                <div class="modal-actions">
                    <button class="btn btn-ghost modal-cancel">取消</button>
                    <button class="btn btn-danger modal-confirm">确认删除</button>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector('.modal-cancel').onclick = () => { overlay.remove(); resolve(false); };
        overlay.querySelector('.modal-confirm').onclick = () => { overlay.remove(); resolve(true); };
    });
}

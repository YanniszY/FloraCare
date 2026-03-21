// ═══════════════════════════════════════════
//  PLANT DETAIL PAGE — plant.js
// ═══════════════════════════════════════════

const API = '';
let plantId   = null;
let plantData = null;

// ── INIT ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Получить ID из URL: /plants/3 → 3
    const parts = window.location.pathname.split('/');
    plantId = parseInt(parts[parts.length - 2]);

    if (!plantId || isNaN(plantId)) {
        window.location.href = '/';
        return;
    }

    loadPlant();
    loadHistory();
});


// ── API ───────────────────────────────────
async function apiFetch(url, options = {}) {
    const res = await fetch(API + url, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
}


// ── LOAD PLANT ────────────────────────────
async function loadPlant() {
    try {
        plantData = await apiFetch(`/plants/${plantId}`);
        renderHero(plantData);
    } catch (e) {
        showToast('Не удалось загрузить растение', 'error');
    }
}

function getStatus(p) {
    if (p.needs_watering || p.days_left <= 0) return 'overdue';
    if (p.days_left <= 3) return 'soon';
    return 'ok';
}

function renderHero(p) {
    document.title = `${p.name} — PlantCare`;

    const status = getStatus(p);
    const statusMap = {
        ok:      { text: `💧 Через ${p.days_left} дн.`,   bg: '#e8f3e8', color: '#2e7d32' },
        soon:    { text: `⏳ Через ${p.days_left} дн.`,   bg: '#fef3e0', color: '#9a6800' },
        overdue: { text: '🚨 Нужен полив сейчас!',         bg: '#fdecea', color: '#d4614a' },
    };
    const s = statusMap[status];

    // Статус-бейдж
    const badge = document.getElementById('hero-status-badge');
    badge.textContent   = s.text;
    badge.style.background = s.bg;
    badge.style.color      = s.color;

    // Название и инфо
    document.getElementById('hero-name').textContent = p.name;

    const nickname = document.getElementById('hero-nickname');
    if (p.nickname) nickname.textContent = `«${p.nickname}»`;

    const location = document.getElementById('hero-location');
    if (p.location) location.innerHTML = `📍 ${p.location}`;

    const notes = document.getElementById('hero-notes');
    if (p.notes) {
        notes.textContent = p.notes;
        notes.classList.add('visible');
    }

    // Мета
    const lastWatered = p.last_watered
        ? new Date(p.last_watered).toLocaleDateString('ru-RU', { day:'numeric', month:'long' })
        : 'неизвестно';
    const nextWatering = p.next_watering
        ? new Date(p.next_watering).toLocaleDateString('ru-RU', { day:'numeric', month:'long' })
        : '—';

    document.getElementById('hero-meta').innerHTML = `
        <div class="meta-item">
            <span class="meta-label">Последний полив</span>
            <span class="meta-value">${lastWatered}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Следующий полив</span>
            <span class="meta-value highlight">${nextWatering}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Интервал</span>
            <span class="meta-value">каждые ${p.water_interval_days} дн.</span>
        </div>
    `;

    // Сайдбар статистика
    document.getElementById('sd-interval').textContent  = p.water_interval_days;
    document.getElementById('sd-days-left').textContent = Math.max(0, p.days_left);

    // Фото
    const photoWrap = document.getElementById('hero-photo-wrap');
    if (p.photo) {
        photoWrap.innerHTML = `
            <img class="hero-photo" src="/${p.photo}" alt="${p.name}">
            <div class="hero-photo-overlay">
                <button class="btn-change-photo" onclick="uploadPhoto()">Сменить фото</button>
            </div>`;
    } else {
        document.getElementById('hero-photo-placeholder').onclick = uploadPhoto;
    }

    // Кнопка "Полить" если уже полито сегодня
    const today = new Date().toISOString().split('T')[0];
    if (p.last_watered === today) {
        const btn = document.getElementById('btn-water');
        btn.textContent = '✓ Полито сегодня';
        btn.classList.add('done');
    }
}


// ── LOAD HISTORY + CHARTS ─────────────────
async function loadHistory() {
    try {
        const history = await apiFetch(`/plants/${plantId}/history`);
        renderTimeline(history);
        renderCharts(history);

        // Кол-во поливов в сайдбар
        const waterings = history.filter(h => h.action === 'watered');
        document.getElementById('sd-total-waterings').textContent = waterings.length;
    } catch (e) {
        document.getElementById('history-timeline').innerHTML =
            '<p style="color:var(--text-light);padding:24px">История недоступна</p>';
    }
}


// ── TIMELINE ─────────────────────────────
function renderTimeline(history) {
    const el = document.getElementById('history-timeline');

    if (!history.length) {
        el.innerHTML = '<p style="color:var(--text-light);padding:12px 0">История пуста</p>';
        return;
    }

    const actionMap = {
        watered:    { icon: '💧', label: 'Полито',      cls: 'dot-watered'    },
        created:    { icon: '🌱', label: 'Добавлено',   cls: 'dot-created'    },
        deleted:    { icon: '🗑', label: 'Удалено',     cls: 'dot-deleted'    },
        renamed:    { icon: '✎', label: 'Изменено',    cls: 'dot-renamed'    },
        fertilized: { icon: '🌿', label: 'Подкормлено', cls: 'dot-fertilized' },
    };

    el.innerHTML = history.slice(0, 50).map((h, i) => {
        const a  = actionMap[h.action] || { icon: '•', label: h.action, cls: 'dot-created' };
        const dt = new Date(h.created_at);
        const time = dt.toLocaleString('ru-RU', {
            day: 'numeric', month: 'long',
            hour: '2-digit', minute: '2-digit'
        });
        return `
        <div class="timeline-item" style="animation-delay:${i * 30}ms">
            <div class="timeline-dot ${a.cls}">${a.icon}</div>
            <div class="timeline-content">
                <div class="timeline-action">${a.label}</div>
                <div class="timeline-time">${time}</div>
            </div>
        </div>`;
    }).join('');
}


// ── CHARTS ───────────────────────────────
function renderCharts(history) {
    const waterings = history
        .filter(h => h.action === 'watered')
        .map(h => new Date(h.created_at))
        .sort((a, b) => a - b);

    renderActivityChart(waterings);
    renderIntervalChart(waterings);
    renderWeekdayChart(waterings);
}

// Общие настройки Chart.js
const chartDefaults = {
    plugins: { legend: { display: false }, tooltip: {
        backgroundColor: 'rgba(28,43,30,0.9)',
        titleFont: { family: 'DM Sans', size: 12 },
        bodyFont:  { family: 'DM Sans', size: 11 },
        padding: 10, cornerRadius: 8,
    }},
    scales: {
        x: { grid: { display: false }, ticks: { font: { family: 'DM Sans', size: 11 }, color: '#8a9e8c' } },
        y: { grid: { color: 'rgba(122,158,126,0.1)' }, ticks: { font: { family: 'DM Sans', size: 11 }, color: '#8a9e8c' } }
    }
};

// График 1: Активность за 30 дней
function renderActivityChart(waterings) {
    const ctx = document.getElementById('chart-activity').getContext('2d');

    // Последние 30 дней
    const days = [];
    const counts = [];
    for (let i = 29; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const str = d.toISOString().split('T')[0];
        days.push(d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }));
        counts.push(waterings.filter(w => w.toISOString().split('T')[0] === str).length);
    }

    if (counts.every(c => c === 0)) {
        showNoData('chart-activity');
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                data: counts,
                backgroundColor: counts.map(c => c > 0 ? 'rgba(74,117,80,0.8)' : 'rgba(200,222,202,0.3)'),
                borderRadius: 4,
                borderSkipped: false,
            }]
        },
        options: {
            ...chartDefaults,
            maintainAspectRatio: false,
            scales: {
                ...chartDefaults.scales,
                y: { ...chartDefaults.scales.y, ticks: { ...chartDefaults.scales.y.ticks, stepSize: 1 } }
            }
        }
    });
}

// График 2: Интервал между поливами
function renderIntervalChart(waterings) {
    const ctx = document.getElementById('chart-interval').getContext('2d');

    if (waterings.length < 2) {
        showNoData('chart-interval', 'Нужно минимум 2 полива');
        return;
    }

    const labels   = [];
    const intervals = [];
    for (let i = 1; i < waterings.length; i++) {
        const diff = Math.round((waterings[i] - waterings[i-1]) / (1000*60*60*24));
        intervals.push(diff);
        labels.push(waterings[i].toLocaleDateString('ru-RU', { day:'numeric', month:'short' }));
    }

    // Среднее
    const avg = Math.round(intervals.reduce((a, b) => a + b, 0) / intervals.length);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    data: intervals,
                    borderColor: 'rgba(74,117,80,0.9)',
                    backgroundColor: 'rgba(74,117,80,0.08)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(74,117,80,1)',
                    pointRadius: 4,
                    tension: 0.3,
                    fill: true,
                    label: 'Дней'
                },
                {
                    data: Array(labels.length).fill(avg),
                    borderColor: 'rgba(232,168,56,0.6)',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    label: `Среднее: ${avg} дн.`
                }
            ]
        },
        options: {
            ...chartDefaults,
            maintainAspectRatio: false,
            plugins: {
                ...chartDefaults.plugins,
                legend: { display: true, labels: {
                    font: { family: 'DM Sans', size: 11 },
                    color: '#4a5e4c',
                    boxWidth: 16,
                    padding: 12,
                }}
            }
        }
    });
}

// График 3: По дням недели
function renderWeekdayChart(waterings) {
    const ctx = document.getElementById('chart-weekday').getContext('2d');

    if (!waterings.length) {
        showNoData('chart-weekday');
        return;
    }

    const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    const counts = Array(7).fill(0);
    waterings.forEach(w => {
        const d = w.getDay(); // 0=вс, 1=пн...
        const idx = d === 0 ? 6 : d - 1;
        counts[idx]++;
    });

    const max = Math.max(...counts);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                data: counts,
                backgroundColor: counts.map(c =>
                    c === max && max > 0
                        ? 'rgba(74,117,80,0.9)'
                        : 'rgba(165,214,167,0.6)'
                ),
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            ...chartDefaults,
            maintainAspectRatio: false,
            scales: {
                ...chartDefaults.scales,
                y: { ...chartDefaults.scales.y, ticks: { ...chartDefaults.scales.y.ticks, stepSize: 1 } }
            }
        }
    });
}

function showNoData(canvasId, msg = 'Пока нет данных') {
    const canvas = document.getElementById(canvasId);
    const wrap   = canvas.parentElement;
    canvas.style.display = 'none';
    wrap.innerHTML = `<div class="chart-no-data">${msg}</div>`;
}


// ── WATER PLANT ───────────────────────────
async function waterPlant() {
    const btn = document.getElementById('btn-water');
    btn.disabled = true;
    btn.innerHTML = '...';

    try {
        await apiFetch(`/plants/${plantId}/water`, { method: 'POST' });
        btn.innerHTML = '✓ Полито сегодня';
        btn.classList.add('done');
        showToast('Растение полито! 💧', 'success');

        // Обновить бейдж статуса
        const badge = document.getElementById('hero-status-badge');
        badge.textContent      = '✓ Полито сегодня';
        badge.style.background = '#e8f3e8';
        badge.style.color      = '#2e7d32';

        // Перезагрузить историю и графики
        setTimeout(() => loadHistory(), 500);
    } catch (e) {
        btn.innerHTML = '<span>💧</span> Полить';
        btn.disabled = false;
        showToast('Ошибка: ' + e.message, 'error');
    }
}


// ── DELETE PLANT ──────────────────────────
async function deletePlant() {
    if (!confirm(`Удалить "${plantData?.name}"? Это действие нельзя отменить.`)) return;

    try {
        await apiFetch(`/plants/${plantId}`, { method: 'DELETE' });
        showToast('Растение удалено', 'info');
        setTimeout(() => window.location.href = '/', 1000);
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}


// ── EDIT PLANT ────────────────────────────
function openEditModal() {
    if (!plantData) return;
    document.getElementById('e-name').value     = plantData.name     || '';
    document.getElementById('e-nickname').value = plantData.nickname || '';
    document.getElementById('e-location').value = plantData.location || '';
    document.getElementById('e-interval').value = plantData.water_interval_days || '';
    document.getElementById('e-notes').value    = plantData.notes    || '';
    openModal('modal-edit');
}

async function submitEdit(e) {
    e.preventDefault();
    const body = {
        name:                document.getElementById('e-name').value.trim(),
        nickname:            document.getElementById('e-nickname').value.trim() || null,
        location:            document.getElementById('e-location').value.trim(),
        water_interval_days: parseInt(document.getElementById('e-interval').value),
        notes:               document.getElementById('e-notes').value.trim() || null,
    };

    try {
        await apiFetch(`/plants/${plantId}`, { method: 'PUT', body: JSON.stringify(body) });
        showToast('Сохранено ✓', 'success');
        closeModal('modal-edit');
        loadPlant();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    }
}


// ── PHOTO UPLOAD ──────────────────────────
async function uploadPhoto() {
    const input = document.createElement('input');
    input.type   = 'file';
    input.accept = 'image/*';
    input.onchange = async () => {
        const file = input.files[0];
        if (!file) return;
        const form = new FormData();
        form.append('file', file);
        try {
            await fetch(`${API}/plants/${plantId}/photo`, { method: 'POST', body: form });
            showToast('Фото загружено!', 'success');
            loadPlant();
        } catch (e) {
            showToast('Ошибка загрузки фото', 'error');
        }
    };
    input.click();
}


// ── MODAL / TOAST HELPERS ─────────────────
function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}
function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    document.body.style.overflow = '';
}
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) closeModal(e.target.id);
});
document.addEventListener('keydown', e => {
    if (e.key === 'Escape')
        document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => closeModal(m.id));
});

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type] || '•'}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'all 0.3s ease';
        toast.style.opacity    = '0';
        toast.style.transform  = 'translateX(40px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

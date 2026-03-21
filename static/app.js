// ═══════════════════════════════════════════
//  PLANTCARE — app.js
//  Весь фронтенд JS в одном файле
// ═══════════════════════════════════════════

const API = '';  // FastAPI на том же хосте

// ── STATE ────────────────────────────────────
let allPlants    = [];
let currentView  = 'grid';
let filterMode   = 'all';   // 'all' | 'needs_water'
let searchQuery  = '';
let editingId    = null;

// ── INIT ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadPlants();

    // Поиск с задержкой
    const searchEl = document.getElementById('search-input');
    let searchTimer;
    searchEl.addEventListener('input', e => {
        clearTimeout(searchTimer);
        searchQuery = e.target.value.trim();
        searchTimer = setTimeout(() => renderPlants(), 300);
    });
});


// ── API HELPERS ───────────────────────────────
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


// ── DASHBOARD ─────────────────────────────────
async function loadDashboard() {
    try {
        const d = await apiFetch('/dashboard');
        document.getElementById('stat-total').textContent = d.total_plants;
        document.getElementById('stat-needs').textContent = d.needs_watering;
        document.getElementById('stat-today').textContent = d.watered_today;
        document.getElementById('needs-water-count').textContent = d.needs_watering;

        // Скрыть бейдж если 0
        const badge = document.getElementById('needs-water-count');
        badge.style.display = d.needs_watering > 0 ? 'inline-block' : 'none';
    } catch (e) {
        console.warn('Dashboard недоступен:', e.message);
    }
}


// ── LOAD PLANTS ───────────────────────────────
async function loadPlants() {
    try {
        const params = new URLSearchParams();
        if (searchQuery) params.set('search', searchQuery);
        if (filterMode === 'needs_water') params.set('needs_water', 'true');

        allPlants = await apiFetch(`/plants/?${params}`);
        renderPlants();
    } catch (e) {
        showToast('Не удалось загрузить растения', 'error');
    }
}


// ── RENDER ────────────────────────────────────
function renderPlants() {
    const container = document.getElementById('plants-container');
    const emptyEl   = document.getElementById('empty-state');

    // Фильтр по поиску (на фронте для быстроты)
    let plants = allPlants;
    if (searchQuery) {
        const q = searchQuery.toLowerCase();
        plants = plants.filter(p =>
            p.name?.toLowerCase().includes(q) ||
            p.nickname?.toLowerCase().includes(q) ||
            p.location?.toLowerCase().includes(q)
        );
    }

    const label = document.getElementById('plant-count-label');
    label.textContent = plants.length > 0 ? `${plants.length} растений` : '';

    if (plants.length === 0) {
        container.innerHTML = '';
        emptyEl.classList.remove('hidden');
        return;
    }

    emptyEl.classList.add('hidden');

    container.innerHTML = plants.map((p, i) => plantCardHTML(p, i)).join('');

    // Анимация задержки для каждой карточки
    container.querySelectorAll('.plant-card').forEach((card, i) => {
        card.style.animationDelay = `${i * 40}ms`;
    });
}

function getStatus(plant) {
    const days = plant.days_left;
    if (plant.needs_watering || days <= 0) return 'overdue';
    if (days <= 3) return 'soon';
    return 'ok';
}

function plantCardHTML(p, index) {
    const status = getStatus(p);
    const statusMap = {
        ok:      { badge: 'badge-ok',      label: `Через ${p.days_left} дн.`, icon: '🌿' },
        soon:    { badge: 'badge-soon',     label: `Через ${p.days_left} дн.`, icon: '⏳' },
        overdue: { badge: 'badge-overdue',  label: 'Нужен полив!',              icon: '💧' },
    };
    const s = statusMap[status];

    const progress = status === 'overdue' ? 100
        : Math.max(0, Math.round((1 - p.days_left / p.water_interval_days) * 100));
    const fillClass = { ok: 'fill-ok', soon: 'fill-soon', overdue: 'fill-over' }[status];

    const photoHTML = p.photo
        ? `<div class="card-photo-wrap" style="position:relative">
               <img class="card-photo" src="/${p.photo}" alt="${p.name}" loading="lazy">
               <button class="btn-delete-photo" onclick="event.stopPropagation(); deletePhoto(${p.id})">✕</button>
           </div>`
        : `<div class="card-photo-placeholder" onclick="event.stopPropagation(); uploadPhoto(${p.id})">🌿</div>`;

    const locationHTML = p.location ? `<div class="card-location">📍 ${p.location}</div>` : '';
    const nicknameHTML = p.nickname ? `<div class="card-nickname">${p.nickname}</div>` : '';
    const nextDate = p.next_watering
        ? new Date(p.next_watering).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
        : '—';

    return `
    <div class="plant-card status-${status}" data-id="${p.id}" onclick="window.location.href='/plants/${p.id}/view'">
        <div class="card-strip"></div>
        ${photoHTML}
        <div class="card-body">
            <div class="card-top">
                <div>
                    <div class="card-name">${p.name}</div>
                    ${nicknameHTML}
                </div>
                <button class="card-menu-btn" onclick="event.stopPropagation(); openEditModal(${p.id})">✎</button>
            </div>
            ${locationHTML}
            <div class="water-status">
                <span class="water-badge ${s.badge}">${s.icon} ${s.label}</span>
                <div class="water-progress">
                    <div class="progress-track">
                        <div class="progress-fill ${fillClass}" style="width:${progress}%"></div>
                    </div>
                    <div class="progress-label">след. ${nextDate}</div>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn-water-card" onclick="event.stopPropagation(); waterPlant(${p.id}, this)">
                    💧 Полить
                </button>
                <button class="btn-icon" onclick="event.stopPropagation(); openHistory(${p.id})">📋</button>
                <button class="btn-icon danger" onclick="event.stopPropagation(); deletePlant(${p.id})">✕</button>
            </div>
        </div>
    </div>`;
}


// ── WATER PLANT ───────────────────────────────
async function waterPlant(id, btn) {
    btn.disabled = true;
    btn.textContent = '...';

    try {
        await apiFetch(`/plants/${id}/water`, { method: 'POST' });

        btn.textContent = '✓ Полито';
        btn.classList.add('done');

        // Обновить карточку визуально
        const card = btn.closest('.plant-card');
        card.className = 'plant-card status-ok';
        const badge = card.querySelector('.water-badge');
        if (badge) {
            badge.className = 'water-badge badge-ok';
            badge.textContent = `🌿 Полито сегодня`;
        }
        const fill = card.querySelector('.progress-fill');
        if (fill) { fill.style.width = '0%'; fill.className = 'progress-fill fill-ok'; }

        showToast('Растение полито! 💧', 'success');

        // Обновить дашборд
        loadDashboard();

        // Через 3 сек перезагрузить данные
        setTimeout(() => loadPlants(), 3000);

    } catch (e) {
        btn.textContent = '💧 Полить';
        btn.disabled = false;
        showToast('Ошибка: ' + e.message, 'error');
    }
}


// ── WATER ALL ─────────────────────────────────
async function waterAll() {
    const btn = document.querySelector('.btn-water-all');
    btn.textContent = '...';
    btn.disabled = true;

    try {
        const res = await apiFetch('/plants/water-all', { method: 'POST' });
        showToast(`Полито растений: ${res.updated} 💧`, 'success');
        await loadPlants();
        await loadDashboard();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    } finally {
        btn.innerHTML = '<span>💧</span> Полить все';
        btn.disabled = false;
    }
}


// ── DELETE PLANT ──────────────────────────────
async function deletePlant(id) {
    const plant = allPlants.find(p => p.id === id);
    const name  = plant ? plant.name : 'растение';

    if (!confirm(`Удалить "${name}"?`)) return;

    try {
        await apiFetch(`/plants/${id}`, { method: 'DELETE' });
        showToast(`"${name}" удалено`, 'info');

        // Анимация удаления
        const card = document.querySelector(`[data-id="${id}"]`);
        if (card) {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity    = '0';
            card.style.transform  = 'scale(0.9)';
            setTimeout(() => loadPlants(), 300);
        } else {
            loadPlants();
        }
        loadDashboard();
    } catch (e) {
        showToast('Ошибка удаления: ' + e.message, 'error');
    }
}


// ── FILTER: NEEDS WATER ───────────────────────
function filterNeedsWater(e) {
    e.preventDefault();
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(n => n.classList.remove('active'));
    e.currentTarget.classList.add('active');

    if (filterMode === 'needs_water') {
        filterMode = 'all';
        document.getElementById('page-title').textContent = 'Мои растения';
        e.currentTarget.classList.remove('active');
        document.querySelector('.nav-item:first-child').classList.add('active');
    } else {
        filterMode = 'needs_water';
        document.getElementById('page-title').textContent = 'Нужен полив';
    }
    loadPlants();
}


// ── VIEW TOGGLE ───────────────────────────────
function setView(view) {
    currentView = view;
    const grid = document.getElementById('plants-container');
    const btnGrid = document.getElementById('view-grid');
    const btnList = document.getElementById('view-list');

    if (view === 'list') {
        grid.classList.add('view-list');
        btnList.classList.add('active');
        btnGrid.classList.remove('active');
    } else {
        grid.classList.remove('view-list');
        btnGrid.classList.add('active');
        btnList.classList.remove('active');
    }
}


// ── MODAL: ADD / EDIT ─────────────────────────
function openAddModal(e) {
    if (e) e.preventDefault();
    editingId = null;
    document.getElementById('modal-title').textContent    = 'Новое растение';
    document.getElementById('form-submit-btn').textContent = 'Добавить';
    document.getElementById('plant-form').reset();
    document.getElementById('edit-plant-id').value = '';
    openModal('modal-plant');
}

function openEditModal(id) {
    const plant = allPlants.find(p => p.id === id);
    if (!plant) return;

    editingId = id;
    document.getElementById('modal-title').textContent    = 'Редактировать';
    document.getElementById('form-submit-btn').textContent = 'Сохранить';
    document.getElementById('edit-plant-id').value = id;

    document.getElementById('f-name').value     = plant.name     || '';
    document.getElementById('f-nickname').value = plant.nickname || '';
    document.getElementById('f-location').value = plant.location || '';
    document.getElementById('f-interval').value = plant.water_interval_days || '';
    // notes не возвращается в списке — оставим пустым или запросим отдельно
    document.getElementById('f-notes').value = '';

    openModal('modal-plant');
}

async function submitPlant(e) {
    e.preventDefault();

    const body = {
        name:                document.getElementById('f-name').value.trim(),
        nickname:            document.getElementById('f-nickname').value.trim() || null,
        location:            document.getElementById('f-location').value.trim(),
        water_interval_days: parseInt(document.getElementById('f-interval').value),
        notes:               document.getElementById('f-notes').value.trim() || null,
    };

    const btn = document.getElementById('form-submit-btn');
    btn.disabled = true;
    btn.textContent = '...';

    try {
        if (editingId) {
            await apiFetch(`/plants/${editingId}`, {
                method: 'PUT',
                body: JSON.stringify(body)
            });
            showToast('Сохранено ✓', 'success');
        } else {
            await apiFetch('/plants/', {
                method: 'POST',
                body: JSON.stringify({ ...body, last_watered: todayStr() })
            });
            showToast('Растение добавлено 🌱', 'success');
        }

        closeModal('modal-plant');
        loadPlants();
        loadDashboard();
    } catch (err) {
        showToast('Ошибка: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = editingId ? 'Сохранить' : 'Добавить';
    }
}


// ── HISTORY ───────────────────────────────────
async function openHistory(id) {
    const plant = allPlants.find(p => p.id === id);
    document.getElementById('history-title').textContent =
        `История — ${plant?.name || 'растение'}`;

    const listEl = document.getElementById('history-list');
    listEl.innerHTML = '<div class="loading-spinner" style="margin:24px auto"></div>';
    openModal('modal-history');

    try {
        const history = await apiFetch(`/plants/${id}/history`);

        if (!history.length) {
            listEl.innerHTML = '<p style="color:var(--text-light);padding:24px;text-align:center">История пуста</p>';
            return;
        }

        const actionMap = {
            watered:    { icon: '💧', label: 'Полито',        cls: 'dot-watered' },
            created:    { icon: '🌱', label: 'Добавлено',     cls: 'dot-created' },
            deleted:    { icon: '🗑', label: 'Удалено',       cls: 'dot-deleted' },
            renamed:    { icon: '✎', label: 'Изменено',      cls: 'dot-renamed' },
            fertilized: { icon: '🌿', label: 'Подкормлено',   cls: 'dot-watered' },
        };

        listEl.innerHTML = history.map(h => {
            const a   = actionMap[h.action] || { icon: '•', label: h.action, cls: 'dot-created' };
            const dt  = new Date(h.created_at);
            const time = dt.toLocaleString('ru-RU', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' });
            return `
            <div class="history-item">
                <div class="history-dot ${a.cls}">${a.icon}</div>
                <div class="history-text">
                    <div class="history-action">${a.label}</div>
                    <div class="history-time">${time}</div>
                </div>
            </div>`;
        }).join('');
    } catch (e) {
        listEl.innerHTML = '<p style="color:var(--text-light);padding:24px;text-align:center">Не удалось загрузить</p>';
    }
}


// ── PHOTO UPLOAD ──────────────────────────────
async function uploadPhoto(id) {
    const input = document.createElement('input');
    input.type   = 'file';
    input.accept = 'image/*';
    input.onchange = async () => {
        const file = input.files[0];
        if (!file) return;

        const form = new FormData();
        form.append('file', file);

        try {
            const res = await fetch(`${API}/plants/${id}/photo`, {
                method: 'POST',
                body: form
            });
            const data = await res.json();
            showToast('Фото загружено!', 'success');
            loadPlants();
        } catch (e) {
            showToast('Ошибка загрузки фото', 'error');
        }
    };
    input.click();
}

// -- DELETE PHOTO
async function deletePhoto(id) {
    if (!confirm('Удалить фото?')) return;
    try {
        await apiFetch(`/plants/${id}/photo`, { method: 'DELETE' });
        showToast('Фото удалено', 'info');
        loadPlants();
    } catch (e) {
        showToast('Ошибка: ' + e.message, 'error');
    }
}


// ── MODAL HELPERS ─────────────────────────────
function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}
function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
    document.body.style.overflow = '';
}

// Закрыть по клику вне модала
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// Закрыть по Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay:not(.hidden)')
            .forEach(m => closeModal(m.id));
    }
});


// ── TOAST ─────────────────────────────────────
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


// ── UTILS ─────────────────────────────────────
function todayStr() {
    return new Date().toISOString().split('T')[0];
}

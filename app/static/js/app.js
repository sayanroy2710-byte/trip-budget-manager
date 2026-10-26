// Trip Budget Manager - Mobile Frontend Controller

let currentTripData = null;
let currentCategoryFilter = 'all';
let currentSplitMode = 'equal_all'; // 'equal_all', 'equal_custom', 'exact'
let selectedPaidById = null;
let categoryChartInstance = null;
let payerChartInstance = null;

// Category icon & color configuration
const CATEGORY_META = {
    'Food': { icon: '🍔', badge: 'bg-orange-500/10 text-orange-400 border-orange-500/30' },
    'Travel': { icon: '🚗', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
    'Stay': { icon: '🏨', badge: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
    'Activities': { icon: '🎟️', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
    'Shopping': { icon: '🛍️', badge: 'bg-pink-500/10 text-pink-400 border-pink-500/30' },
    'Other': { icon: '📦', badge: 'bg-slate-500/10 text-slate-300 border-slate-500/30' }
};

// ==========================================
// Initialization & Data Loading
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    // Set default date in add form to today
    const dateInput = document.getElementById('expense-date');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    loadTripData();
});

async function loadTripData(silent = false) {
    try {
        const res = await fetch(`/api/trips/${TRIP_ID}`);
        if (!res.ok) throw new Error('Failed to load trip data');
        currentTripData = await res.json();

        // Update local storage recent trips
        saveCurrentToRecents(currentTripData.trip);

        // Render UI sections
        renderHeaderAndStats();
        renderExpenses();
        renderAddExpenseFormHelpers();
        renderBalances();
        renderSettlementPlan();
        renderCharts();

        if (!silent) {
            lucide.createIcons();
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function saveCurrentToRecents(trip) {
    try {
        let recents = JSON.parse(localStorage.getItem('recent_trips') || '[]');
        recents = recents.filter(t => t.id !== trip.id);
        recents.unshift({ id: trip.id, name: trip.name, currency: trip.currency, timestamp: Date.now() });
        if (recents.length > 5) recents.pop();
        localStorage.setItem('recent_trips', JSON.stringify(recents));
    } catch (e) {
        console.error(e);
    }
}

// ==========================================
// Navigation & Tab Switching
// ==========================================
function switchTab(tabName) {
    // Hide all views
    document.querySelectorAll('.tab-view').forEach(view => view.classList.add('hidden'));
    
    // Show selected view
    const target = document.getElementById(`view-${tabName}`);
    if (target) target.classList.remove('hidden');

    // Update Mobile Nav styling
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
        tab.classList.add('text-slate-400');
        tab.classList.remove('text-blue-400');
    });
    const activeMobileTab = document.getElementById(`m-tab-${tabName}`);
    if (activeMobileTab) {
        activeMobileTab.classList.add('active');
        activeMobileTab.classList.remove('text-slate-400');
        activeMobileTab.classList.add('text-blue-400');
    }

    // Update Desktop Tabs styling
    ['expenses', 'add', 'balances', 'settle', 'stats'].forEach(t => {
        const dTab = document.getElementById(`d-tab-${t}`);
        if (dTab) {
            if (t === tabName) {
                dTab.className = "flex-1 py-2.5 px-4 rounded-xl text-center transition-all text-blue-400 bg-blue-600/10 border border-blue-500/20 flex items-center justify-center gap-2";
            } else {
                dTab.className = "flex-1 py-2.5 px-4 rounded-xl text-center transition-all text-slate-400 hover:text-white flex items-center justify-center gap-2";
            }
        }
    });

    if (tabName === 'stats') {
        setTimeout(renderCharts, 100);
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
    lucide.createIcons();
}

// ==========================================
// Render Header & Top Spending Card
// ==========================================
function renderHeaderAndStats() {
    const trip = currentTripData.trip;
    const curr = trip.currency || '₹';
    
    document.getElementById('header-trip-name').textContent = trip.name;
    document.getElementById('header-members-count').textContent = `${currentTripData.member_count} members`;
    
    document.getElementById('stat-total-spent').textContent = `${curr}${currentTripData.total_spent.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    const avg = currentTripData.member_count > 0 ? (currentTripData.total_spent / currentTripData.member_count) : 0;
    document.getElementById('stat-avg-spent').textContent = `${curr}${avg.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('stat-expense-count').textContent = `${currentTripData.expense_count} expense${currentTripData.expense_count === 1 ? '' : 's'}`;

    // Render avatar bubbles
    const avatarContainer = document.getElementById('members-avatar-stack');
    avatarContainer.innerHTML = '';
    trip.members.forEach(member => {
        const bubble = document.createElement('div');
        bubble.className = 'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ring-2 ring-slate-900 shadow';
        bubble.style.backgroundColor = member.color || '#3B82F6';
        bubble.title = member.name;
        bubble.textContent = member.name.charAt(0).toUpperCase();
        avatarContainer.appendChild(bubble);
    });

    // Settle badge indicator if debts exist
    const hasPendingSettlement = currentTripData.settlement_plan && currentTripData.settlement_plan.length > 0;
    const dBadge = document.getElementById('desktop-settle-badge');
    const mDot = document.getElementById('mobile-settle-dot');
    if (dBadge) dBadge.classList.toggle('hidden', !hasPendingSettlement);
    if (mDot) mDot.classList.toggle('hidden', !hasPendingSettlement);
}

// ==========================================
// Render Expenses List
// ==========================================
function renderExpenses() {
    const list = document.getElementById('expenses-list');
    list.innerHTML = '';

    const expenses = currentTripData.expenses || [];
    const curr = currentTripData.trip.currency || '₹';

    const filtered = currentCategoryFilter === 'all' 
        ? expenses 
        : expenses.filter(e => e.category === currentCategoryFilter);

    if (filtered.length === 0) {
        list.innerHTML = `
            <div class="glass-panel rounded-3xl p-8 text-center">
                <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400">
                    <i data-lucide="receipt-text" class="w-8 h-8"></i>
                </div>
                <h4 class="text-base font-bold text-white mb-1">No expenses recorded yet</h4>
                <p class="text-xs text-slate-400 max-w-xs mx-auto mb-4">
                    Tap the Add button below to log your hotel, transport, meals, or fun activities.
                </p>
                <button onclick="switchTab('add')" class="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs inline-flex items-center gap-2 shadow-lg shadow-blue-600/20 active:scale-95 transition-all">
                    <i data-lucide="plus" class="w-4 h-4"></i>
                    <span>Add First Expense</span>
                </button>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    filtered.forEach(exp => {
        const cat = CATEGORY_META[exp.category] || CATEGORY_META['Other'];
        const card = document.createElement('div');
        card.className = 'glass-panel rounded-2xl p-4 shadow-lg hover:border-slate-700 transition-all cursor-pointer group';
        card.id = `expense-card-${exp.id}`;
        
        // Split details html
        const splitsHtml = exp.splits.map(s => `
            <div class="flex items-center justify-between text-xs py-1 border-b border-slate-800/60 last:border-0">
                <span class="text-slate-300 font-medium">${escapeHtml(s.member_name)}</span>
                <span class="text-slate-400 font-mono">${curr}${s.amount.toFixed(2)}</span>
            </div>
        `).join('');

        card.innerHTML = `
            <div class="flex items-start justify-between gap-3" onclick="toggleExpenseDetails(${exp.id})">
                <div class="flex items-start gap-3 min-w-0">
                    <div class="w-11 h-11 rounded-2xl ${cat.badge} flex items-center justify-center text-lg shrink-0 border">
                        ${cat.icon}
                    </div>
                    <div class="min-w-0">
                        <h4 class="text-sm font-bold text-white truncate group-hover:text-blue-400 transition-colors">${escapeHtml(exp.title)}</h4>
                        <div class="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                            <span class="text-blue-400 font-semibold">${escapeHtml(exp.paid_by_name)} paid</span>
                            <span>•</span>
                            <span>${exp.date}</span>
                        </div>
                    </div>
                </div>

                <div class="text-right shrink-0">
                    <div class="text-base font-extrabold text-white">
                        ${curr}${exp.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div class="text-[11px] text-slate-400 mt-0.5">
                        ${exp.splits.length} people
                    </div>
                </div>
            </div>

            <!-- Expandable Split Breakdown -->
            <div id="expense-detail-${exp.id}" class="hidden mt-3 pt-3 border-t border-slate-800 text-xs">
                <div class="mb-2 font-semibold text-slate-400 flex items-center justify-between">
                    <span>Split Breakdown:</span>
                    <button onclick="deleteExpense(${exp.id}, event)" class="text-rose-400 hover:text-rose-300 flex items-center gap-1 font-bold p-1 rounded hover:bg-rose-500/10 transition-colors">
                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        <span>Delete</span>
                    </button>
                </div>
                <div class="bg-slate-900/80 rounded-xl p-2.5 border border-slate-800">
                    ${splitsHtml}
                </div>
                ${exp.notes ? `<p class="mt-2 text-slate-400 italic text-[11px]">Note: "${escapeHtml(exp.notes)}"</p>` : ''}
            </div>
        `;
        list.appendChild(card);
    });

    lucide.createIcons();
}

function toggleExpenseDetails(id) {
    const detail = document.getElementById(`expense-detail-${id}`);
    if (detail) {
        detail.classList.toggle('hidden');
        lucide.createIcons();
    }
}

function filterExpenses(category) {
    currentCategoryFilter = category;
    document.querySelectorAll('.cat-filter-btn').forEach(btn => {
        if (btn.dataset.cat === category) {
            btn.className = "cat-filter-btn px-3 py-1.5 rounded-xl bg-blue-600 text-white shrink-0 transition-all font-semibold";
        } else {
            btn.className = "cat-filter-btn px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white shrink-0 transition-all font-semibold";
        }
    });
    renderExpenses();
}

async function deleteExpense(expenseId, e) {
    if (e) e.stopPropagation();
    if (!confirm('Are you sure you want to delete this expense? Balances will be recalculated.')) {
        return;
    }

    try {
        const res = await fetch(`/api/trips/${TRIP_ID}/expenses/${expenseId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete expense');

        showToast('Expense removed', 'success');
        await loadTripData(true);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// Add Expense Form Helpers & Handlers
// ==========================================
function renderAddExpenseFormHelpers() {
    if (!currentTripData) return;
    const members = currentTripData.trip.members || [];

    // 1. Paid By Member Chips
    const paidByContainer = document.getElementById('form-paid-by-chips');
    paidByContainer.innerHTML = '';
    
    if (!selectedPaidById && members.length > 0) {
        selectedPaidById = members[0].id;
    }

    members.forEach(m => {
        const chip = document.createElement('button');
        chip.type = 'button';
        chip.onclick = () => selectPaidBy(m.id);
        chip.id = `paid-chip-${m.id}`;
        
        const isSelected = m.id === selectedPaidById;
        chip.className = isSelected 
            ? 'px-3.5 py-2 rounded-2xl bg-blue-600 text-white text-xs font-bold border border-blue-400 shadow flex items-center gap-2 transition-all'
            : 'px-3.5 py-2 rounded-2xl bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition-all';
        
        chip.innerHTML = `
            <span class="w-3 h-3 rounded-full shrink-0" style="background-color: ${m.color}"></span>
            <span>${escapeHtml(m.name)}</span>
        `;
        paidByContainer.appendChild(chip);
    });

    // 2. Split Checkboxes (For 'equal_custom' mode)
    const checkContainer = document.getElementById('split-checkboxes-container');
    checkContainer.innerHTML = '';
    members.forEach(m => {
        const item = document.createElement('label');
        item.className = 'flex items-center gap-3 p-2.5 rounded-xl bg-slate-900 border border-slate-800 cursor-pointer hover:border-slate-700 transition-all text-xs font-semibold';
        item.innerHTML = `
            <input type="checkbox" name="split-member-check" value="${m.id}" checked class="rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${m.color}"></span>
            <span class="text-slate-200">${escapeHtml(m.name)}</span>
        `;
        checkContainer.appendChild(item);
    });

    // 3. Exact Amount Inputs (For 'exact' mode)
    const exactContainer = document.getElementById('exact-inputs-container');
    exactContainer.innerHTML = '';
    members.forEach(m => {
        const row = document.createElement('div');
        row.className = 'flex items-center gap-3 p-2 rounded-xl bg-slate-900 border border-slate-800';
        row.innerHTML = `
            <div class="flex items-center gap-2 flex-1 min-w-0">
                <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background-color: ${m.color}"></span>
                <span class="text-xs font-bold text-slate-200 truncate">${escapeHtml(m.name)}</span>
            </div>
            <div class="relative w-28">
                <span class="absolute inset-y-0 left-0 pl-2.5 flex items-center text-xs font-bold text-slate-400">${currentTripData.trip.currency || '₹'}</span>
                <input 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    data-member-id="${m.id}" 
                    class="exact-member-input w-full pl-6 pr-2 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-xs font-semibold text-right focus:outline-none focus:ring-1 focus:ring-blue-500" 
                    placeholder="0.00"
                    oninput="recalculateExactRemaining()"
                >
            </div>
        `;
        exactContainer.appendChild(row);
    });
}

function selectPaidBy(memberId) {
    selectedPaidById = memberId;
    renderAddExpenseFormHelpers();
}

function setSplitMode(mode) {
    currentSplitMode = mode;
    
    // Toggle active buttons
    document.getElementById('btn-split-all').className = mode === 'equal_all' ? 'px-2.5 py-1 rounded-lg bg-blue-600 text-white font-semibold' : 'px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white font-semibold';
    document.getElementById('btn-split-select').className = mode === 'equal_custom' ? 'px-2.5 py-1 rounded-lg bg-blue-600 text-white font-semibold' : 'px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white font-semibold';
    document.getElementById('btn-split-exact').className = mode === 'exact' ? 'px-2.5 py-1 rounded-lg bg-blue-600 text-white font-semibold' : 'px-2.5 py-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white font-semibold';

    // Show/hide view modes
    document.getElementById('split-mode-all').classList.toggle('hidden', mode !== 'equal_all');
    document.getElementById('split-mode-select').classList.toggle('hidden', mode !== 'equal_custom');
    document.getElementById('split-mode-exact').classList.toggle('hidden', mode !== 'exact');

    if (mode === 'exact') {
        recalculateExactRemaining();
    }
}

function recalculateExactRemaining() {
    const totalAmount = parseFloat(document.getElementById('expense-amount').value) || 0;
    const inputs = document.querySelectorAll('.exact-member-input');
    let sum = 0;
    inputs.forEach(input => {
        sum += parseFloat(input.value) || 0;
    });

    const diff = totalAmount - sum;
    const indicator = document.getElementById('exact-sum-indicator');
    const curr = currentTripData.trip.currency || '₹';

    if (Math.abs(diff) < 0.05) {
        indicator.textContent = 'Balanced ✓';
        indicator.className = 'font-bold text-emerald-400';
    } else if (diff > 0) {
        indicator.textContent = `Remaining: ${curr}${diff.toFixed(2)}`;
        indicator.className = 'font-bold text-amber-400';
    } else {
        indicator.textContent = `Over by: ${curr}${Math.abs(diff).toFixed(2)}`;
        indicator.className = 'font-bold text-rose-400';
    }
}

async function handleSaveExpense(e) {
    e.preventDefault();
    const saveBtn = document.getElementById('save-expense-btn');
    const amount = parseFloat(document.getElementById('expense-amount').value);
    const title = document.getElementById('expense-title').value.trim();
    const category = document.querySelector('input[name="expense-category"]:checked')?.value || 'Food';
    const date = document.getElementById('expense-date').value;

    if (!amount || amount <= 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }
    if (!title) {
        showToast('Please enter an expense title', 'error');
        return;
    }
    if (!selectedPaidById) {
        showToast('Please select who paid', 'error');
        return;
    }

    const payload = {
        title: title,
        amount: amount,
        category: category,
        paid_by_id: selectedPaidById,
        date: date,
        split_type: currentSplitMode === 'exact' ? 'exact' : 'equal',
    };

    if (currentSplitMode === 'equal_custom') {
        const checked = Array.from(document.querySelectorAll('input[name="split-member-check"]:checked')).map(el => parseInt(el.value));
        if (checked.length === 0) {
            showToast('Please select at least one person to split with', 'error');
            return;
        }
        payload.split_member_ids = checked;
    } else if (currentSplitMode === 'exact') {
        const customSplits = [];
        let sum = 0;
        document.querySelectorAll('.exact-member-input').forEach(inp => {
            const val = parseFloat(inp.value) || 0;
            customSplits.push({
                member_id: parseInt(inp.dataset.memberId),
                amount: val
            });
            sum += val;
        });

        if (Math.abs(sum - amount) > 0.05) {
            showToast(`Custom splits (${sum.toFixed(2)}) must equal total amount (${amount.toFixed(2)})`, 'error');
            return;
        }
        payload.custom_splits = customSplits;
    }

    saveBtn.disabled = true;
    saveBtn.innerHTML = `<span>Saving...</span>`;

    try {
        const res = await fetch(`/api/trips/${TRIP_ID}/expenses`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to save expense');
        }

        showToast('Expense recorded successfully!', 'success');
        
        // Reset form fields
        document.getElementById('expense-amount').value = '';
        document.getElementById('expense-title').value = '';
        document.querySelectorAll('.exact-member-input').forEach(inp => inp.value = '');
        
        // Reload trip data and return to expenses list
        await loadTripData(true);
        switchTab('expenses');
    } catch (err) {
        showToast(err.message, 'error');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `
            <i data-lucide="check" class="w-5 h-5"></i>
            <span>Save Expense</span>
        `;
        lucide.createIcons();
    }
}

// ==========================================
// Render Balances View
// ==========================================
function renderBalances() {
    const container = document.getElementById('balances-container');
    container.innerHTML = '';

    const balances = currentTripData.balances || [];
    const curr = currentTripData.trip.currency || '₹';

    balances.forEach(b => {
        const card = document.createElement('div');
        card.className = 'glass-panel rounded-2xl p-4 shadow-lg flex items-center justify-between gap-3';
        
        let badgeHtml = '';
        if (b.status === 'creditor') {
            badgeHtml = `
                <div class="text-right">
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-extrabold text-xs sm:text-sm">
                        +${curr}${b.net_balance.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <p class="text-[10px] text-emerald-500 font-semibold mt-0.5">Gets back</p>
                </div>
            `;
        } else if (b.status === 'debtor') {
            badgeHtml = `
                <div class="text-right">
                    <span class="inline-flex items-center gap-1 px-3 py-1 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 font-extrabold text-xs sm:text-sm">
                        -${curr}${Math.abs(b.net_balance).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <p class="text-[10px] text-rose-500 font-semibold mt-0.5">Owes</p>
                </div>
            `;
        } else {
            badgeHtml = `
                <div class="text-right">
                    <span class="inline-flex items-center px-2.5 py-1 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 font-bold text-xs">
                        Settled ✓
                    </span>
                    <p class="text-[10px] text-slate-500 mt-0.5">All clear</p>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="flex items-center gap-3 min-w-0">
                <div class="w-11 h-11 rounded-2xl flex items-center justify-center text-sm font-extrabold text-white shrink-0 shadow" style="background-color: ${b.color}">
                    ${b.member_name.charAt(0).toUpperCase()}
                </div>
                <div class="min-w-0">
                    <h4 class="text-sm font-bold text-white truncate">${escapeHtml(b.member_name)}</h4>
                    <div class="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                        <span>Paid: <strong class="text-slate-300">${curr}${b.total_paid.toFixed(2)}</strong></span>
                        <span>•</span>
                        <span>Share: <strong class="text-slate-300">${curr}${b.total_share.toFixed(2)}</strong></span>
                    </div>
                </div>
            </div>

            ${badgeHtml}
        `;
        container.appendChild(card);
    });
}

// ==========================================
// Render Settlement Plan ("Who Pays Whom")
// ==========================================
function renderSettlementPlan() {
    const list = document.getElementById('settlement-steps-list');
    list.innerHTML = '';

    const plan = currentTripData.settlement_plan || [];
    const curr = currentTripData.trip.currency || '₹';

    if (plan.length === 0) {
        list.innerHTML = `
            <div class="p-6 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 text-center">
                <div class="w-12 h-12 mx-auto mb-2 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                    <i data-lucide="check-circle-2" class="w-6 h-6"></i>
                </div>
                <h4 class="text-sm font-bold text-emerald-300 mb-1">All Settled Up!</h4>
                <p class="text-xs text-slate-400">Everyone is square. No pending payments needed between members.</p>
            </div>
        `;
    } else {
        plan.forEach(step => {
            const item = document.createElement('div');
            item.className = 'glass-panel p-4 rounded-2xl flex items-center justify-between gap-3 border-slate-700/80';
            item.innerHTML = `
                <div class="flex items-center gap-2.5 min-w-0">
                    <div class="p-2 rounded-xl bg-blue-500/10 text-blue-400 shrink-0">
                        <i data-lucide="arrow-right-left" class="w-4 h-4"></i>
                    </div>
                    <div class="min-w-0">
                        <div class="text-xs sm:text-sm font-bold text-white flex items-center gap-1.5 flex-wrap">
                            <span class="text-rose-400 font-extrabold">${escapeHtml(step.from_member_name)}</span>
                            <span class="text-slate-400 font-normal">pays</span>
                            <span class="text-emerald-400 font-extrabold">${escapeHtml(step.to_member_name)}</span>
                        </div>
                        <div class="text-xs font-mono font-bold text-cyan-400 mt-0.5">
                            ${curr}${step.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                    </div>
                </div>

                <button 
                    onclick="openSettlementModal(${step.from_member_id}, '${escapeHtml(step.from_member_name)}', ${step.to_member_id}, '${escapeHtml(step.to_member_name)}', ${step.amount})" 
                    class="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shrink-0 transition-all shadow-md shadow-emerald-600/20 active:scale-95 flex items-center gap-1.5"
                >
                    <i data-lucide="check" class="w-3.5 h-3.5"></i>
                    <span>Settle</span>
                </button>
            `;
            list.appendChild(item);
        });
    }

    // Render Past Recorded Settlements
    const historySection = document.getElementById('settlements-history-section');
    const historyList = document.getElementById('settlements-history-list');
    historyList.innerHTML = '';
    const history = currentTripData.settlements_history || [];

    if (history.length > 0) {
        historySection.classList.remove('hidden');
        history.forEach(s => {
            const hItem = document.createElement('div');
            hItem.className = 'p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-2';
            hItem.innerHTML = `
                <div>
                    <span class="font-bold text-white">${escapeHtml(s.from_member_name)}</span> paid <span class="font-bold text-white">${escapeHtml(s.to_member_name)}</span>: <strong class="text-emerald-400 font-mono">${curr}${s.amount.toFixed(2)}</strong>
                    <span class="text-[10px] text-slate-500 block">${s.date} ${s.notes ? `• ${escapeHtml(s.notes)}` : ''}</span>
                </div>
                <button onclick="deleteSettlementRecord(${s.id})" title="Undo" class="text-slate-500 hover:text-rose-400 p-1.5 rounded transition-colors">
                    <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
            `;
            historyList.appendChild(hItem);
        });
    } else {
        historySection.classList.add('hidden');
    }

    lucide.createIcons();
}

function openSettlementModal(fromId, fromName, toId, toName, amount) {
    document.getElementById('settle-from-id').value = fromId;
    document.getElementById('settle-to-id').value = toId;
    document.getElementById('settle-from-name').textContent = fromName;
    document.getElementById('settle-to-name').textContent = toName;
    document.getElementById('settle-amount').value = amount;
    document.getElementById('settle-notes').value = 'Settled via Trip Budget';

    openModal('settlement-modal');
}

async function handleConfirmSettlement(e) {
    e.preventDefault();
    const fromId = parseInt(document.getElementById('settle-from-id').value);
    const toId = parseInt(document.getElementById('settle-to-id').value);
    const amount = parseFloat(document.getElementById('settle-amount').value);
    const notes = document.getElementById('settle-notes').value.trim();

    if (!amount || amount <= 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/trips/${TRIP_ID}/settlements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                from_member_id: fromId,
                to_member_id: toId,
                amount: amount,
                notes: notes
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to record settlement');
        }

        showToast('Settlement recorded!', 'success');
        closeModal('settlement-modal');
        await loadTripData(true);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function deleteSettlementRecord(settlementId) {
    if (!confirm('Undo this settlement payment record?')) return;

    try {
        const res = await fetch(`/api/trips/${TRIP_ID}/settlements/${settlementId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to undo settlement');

        showToast('Settlement record undone', 'success');
        await loadTripData(true);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// Render Charts (Analytics Tab)
// ==========================================
function renderCharts() {
    if (!currentTripData) return;

    // 1. Category Chart
    const catCanvas = document.getElementById('category-chart');
    if (catCanvas) {
        const expenses = currentTripData.expenses || [];
        const catTotals = {};

        expenses.forEach(e => {
            catTotals[e.category] = (catTotals[e.category] || 0) + e.amount;
        });

        const labels = Object.keys(catTotals);
        const data = Object.values(catTotals);

        if (categoryChartInstance) {
            categoryChartInstance.destroy();
        }

        if (labels.length > 0) {
            categoryChartInstance = new Chart(catCanvas, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#F97316', '#3B82F6', '#8B5CF6', '#10B981', '#EC4899', '#64748B'
                        ],
                        borderWidth: 2,
                        borderColor: '#0F172A'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans', size: 11 } }
                        }
                    }
                }
            });
        }
    }

    // 2. Payer Chart
    const payerCanvas = document.getElementById('payer-chart');
    if (payerCanvas) {
        const balances = currentTripData.balances || [];
        const names = balances.map(b => b.member_name);
        const paidAmounts = balances.map(b => b.total_paid);
        const colors = balances.map(b => b.color);

        if (payerChartInstance) {
            payerChartInstance.destroy();
        }

        payerChartInstance = new Chart(payerCanvas, {
            type: 'bar',
            data: {
                labels: names,
                datasets: [{
                    label: 'Amount Paid',
                    data: paidAmounts,
                    backgroundColor: colors,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans' } }, grid: { display: false } },
                    y: { ticks: { color: '#94A3B8' }, grid: { color: '#1E293B' } }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// ==========================================
// WhatsApp & Share Modal Helpers
// ==========================================
async function shareViaWhatsApp() {
    try {
        const res = await fetch(`/api/trips/${TRIP_ID}/export/whatsapp`);
        if (!res.ok) throw new Error('Failed to generate summary');
        const data = await res.json();
        
        const text = data.text;
        
        // If mobile, try opening WhatsApp directly
        const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`;
        
        // Copy to clipboard as well
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(text);
        }

        window.open(whatsappUrl, '_blank');
        showToast('WhatsApp summary opened & copied to clipboard!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function openShareModal() {
    const qrcodeWrapper = document.getElementById('qrcode-wrapper');
    qrcodeWrapper.innerHTML = '';

    const tripUrl = window.location.href;

    // Generate QR code
    new QRCode(qrcodeWrapper, {
        text: tripUrl,
        width: 180,
        height: 180,
        colorDark: '#0f172a',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.H
    });

    openModal('share-modal');
}

function copyTripLink() {
    const tripUrl = window.location.href;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(tripUrl).then(() => {
            showToast('Trip link copied to clipboard!', 'success');
        });
    } else {
        showToast('Link: ' + tripUrl, 'info');
    }
}

function triggerNativeShare() {
    const tripUrl = window.location.href;
    if (navigator.share) {
        navigator.share({
            title: currentTripData.trip.name,
            text: `Join our trip "${currentTripData.trip.name}" on Trip Budget Manager to add expenses and view dues!`,
            url: tripUrl
        }).catch(err => console.log('Share dismissed', err));
    } else {
        copyTripLink();
    }
}

// ==========================================
// Add Member to Existing Trip
// ==========================================
function openAddMemberModal() {
    document.getElementById('new-member-name').value = '';
    openModal('add-member-modal');
}

async function handleSaveNewMember(e) {
    e.preventDefault();
    const name = document.getElementById('new-member-name').value.trim();
    if (!name) return;

    try {
        const res = await fetch(`/api/trips/${TRIP_ID}/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to add member');
        }

        showToast(`${name} added to the trip!`, 'success');
        closeModal('add-member-modal');
        await loadTripData(true);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==========================================
// Common Modal Utilities
// ==========================================
function openModal(id) {
    const modal = document.getElementById(id);
    const backdrop = document.getElementById('modal-backdrop');
    if (modal) {
        modal.classList.remove('hidden');
        if (backdrop) backdrop.classList.remove('hidden');
    }
    lucide.createIcons();
}

function closeModal(id) {
    const modal = document.getElementById(id);
    const backdrop = document.getElementById('modal-backdrop');
    if (modal) modal.classList.add('hidden');
    if (backdrop) backdrop.classList.add('hidden');
}

document.getElementById('modal-backdrop')?.addEventListener('click', () => {
    document.querySelectorAll('.tab-view + div[id$="-modal"], #share-modal, #add-member-modal, #settlement-modal').forEach(m => {
        m.classList.add('hidden');
    });
    document.getElementById('modal-backdrop').classList.add('hidden');
});

function toggleExportMenu() {
    const menu = document.getElementById('export-dropdown');
    if (menu) menu.classList.toggle('hidden');
}

document.addEventListener('click', (e) => {
    const btn = document.getElementById('export-menu-btn');
    const menu = document.getElementById('export-dropdown');
    if (btn && menu && !btn.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.add('hidden');
    }
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

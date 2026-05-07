/**
 * Library Management System - Frontend UI Logic
 * Modern SaaS Dashboard Version
 */

const qs = (sel) => document.querySelector(sel);
const qsa = (sel) => [...document.querySelectorAll(sel)];

// UI Utilities
function showToast(message, type = "success") {
    const container = qs("#toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast ${type} animate-fade-in`;
    const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle');
    toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function updateSidebarActive(id) {
    qsa(".nav-item").forEach(item => {
        const href = item.getAttribute("href");
        if (href && href.startsWith("#")) {
            item.classList.toggle("active", href === `#${id}`);
        }
    });
    const pageTitle = qs(".page-title");
    if (pageTitle) {
        const activeItem = qs(`.nav-item[href="#${id}"]`);
        if (activeItem) pageTitle.textContent = activeItem.textContent.trim();
    }
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// API Wrapper
async function api(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: { "Content-Type": "application/json", ...options.headers },
    });
    const data = await res.json();
    if (!res.ok || data.status === "error") {
        const errorMsg = data.message || "An unexpected error occurred.";
        showToast(errorMsg, "error");
        throw new Error(errorMsg);
    }
    return data;
}

function setMessage(el, text, isError = false) {
    if (!el) return;
    el.textContent = text;
    el.className = `form-message ${isError ? "error" : "success"} animate-fade-in`;
}

// Component Renderers
function bookCard(book, page) {
    const isAvailable = Number(book.available_quantity) > 0;
    let actionButtons = "";
    
    if (page === "admin") {
        actionButtons = `
            <div class="flex gap-2">
                <button class="btn btn-white btn-sm" data-edit-book="${book.id}" style="flex: 1; padding: 6px 12px; font-size: 0.75rem;"><i class="fas fa-edit"></i> Edit</button>
                <button class="btn btn-danger btn-sm" data-delete-book="${book.id}" style="padding: 6px 10px; font-size: 0.75rem;"><i class="fas fa-trash"></i></button>
            </div>`;
    } else {
        if (book.is_issued) {
            actionButtons = `<button class="btn btn-white btn-sm w-full" disabled style="font-size: 0.75rem;"><i class="fas fa-check"></i> Already Issued</button>`;
        } else if (book.request_status === 'pending') {
            actionButtons = `<button class="btn btn-white btn-sm w-full" disabled style="font-size: 0.75rem;"><i class="fas fa-clock"></i> Requested</button>`;
        } else if (book.request_status === 'rejected') {
            actionButtons = `<button class="btn btn-danger btn-sm w-full" data-rejection-reason="${escapeHtml(book.rejection_reason)}" style="font-size: 0.75rem;"><i class="fas fa-times-circle"></i> Rejected</button>`;
        } else {
            actionButtons = `<button class="btn btn-brand btn-sm w-full" data-request-book="${book.id}" ${isAvailable ? "" : "disabled"} style="font-size: 0.75rem;">
                <i class="fas fa-plus"></i> ${isAvailable ? "Request Book" : "Out of Stock"}
            </button>`;
        }
    }

    return `
        <article class="card flex flex-column gap-3 fade-up" style="animation-delay: ${Math.random() * 0.2}s">
            <div class="flex justify-between align-center">
                <div class="badge" style="background: var(--slate-100); color: var(--slate-600); font-size: 0.65rem;">${escapeHtml(book.category).toUpperCase()}</div>
                <div class="badge ${isAvailable ? 'badge-success' : 'badge-danger'}" style="font-size: 0.65rem;">${isAvailable ? 'Available' : 'Issued'}</div>
            </div>
            <div style="flex: 1;">
                <h3 title="${escapeHtml(book.title)}" style="font-size: 0.9375rem; font-weight: 700; margin-bottom: 2px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 2.8em; line-height: 1.4; color: var(--slate-900);">${escapeHtml(book.title)}</h3>
                <p style="color: var(--slate-500); font-size: 0.75rem; font-weight: 500;"><i class="fas fa-pen-nib" style="font-size: 0.7rem; opacity: 0.7;"></i> ${escapeHtml(book.author)}</p>
            </div>
            <div class="flex justify-between align-center" style="border-top: 1px solid var(--slate-100); padding-top: 12px; margin-top: 4px;">
                <span style="color: var(--slate-400); font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em;"><i class="fas fa-location-dot"></i> ${escapeHtml(book.shelf)}</span>
                <span style="color: var(--slate-400); font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em;"><i class="fas fa-cubes"></i> QTY: ${book.available_quantity}</span>
            </div>
            <div style="margin-top: auto;">
                ${actionButtons}
            </div>
        </article>`;
}

function renderTable(headers, rows, emptyMsg = "No records found.") {
    if (!rows.length) return `<div class="empty-state"><i class="fas fa-folder-open"></i><p>${emptyMsg}</p></div>`;
    
    return `
        <div class="table-responsive">
            <table>
                <thead>
                    <tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr>
                </thead>
                <tbody>
                    ${rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join("")}</tr>`).join("")}
                </tbody>
            </table>
        </div>`;
}

// Data Loading
async function loadBooks(page) {
    const grid = qs("#adminBookGrid") || qs("#bookGrid");
    if (!grid) return;

    const searchEl = qs("#adminBookSearch") || qs("#bookSearch");
    const query = searchEl?.value || "";
    const data = await api(`/books?q=${encodeURIComponent(query)}`);
    
    let booksToShow = data.books;
    if (page === "student") {
        booksToShow = data.books.filter(b => !b.is_issued);
    }

    grid.innerHTML = booksToShow.length 
        ? booksToShow.map(b => bookCard(b, page)).join("") 
        : `<div class="empty-state"><i class="fas fa-search"></i><p>No books found matching "${query}"</p></div>`;

    populateIssueBooks(data.books);
    wireBookActions(data.books, page);
}

function populateIssueBooks(books) {
    const select = qs("#issueStudent") && qs("#issueBook"); // check if on admin page
    if (!select) return;

    const availableBooks = books.filter((book) => Number(book.available_quantity) > 0);
    qs("#issueBook").innerHTML = availableBooks.map((book) => 
        `<option value="${book.id}">${escapeHtml(book.title)}</option>`
    ).join("");
}

async function loadStudents() {
    const list = qs("#studentTable");
    if (!list) return;

    const data = await api("/students");
    
    const headers = ["Name", "Username", "Email", "Access/Actions"];
    const rows = data.students.map(s => [
        `<strong>${escapeHtml(s.name)}</strong>`,
        escapeHtml(s.username),
        escapeHtml(s.email),
        `<div class="d-flex gap-2">
            <span class="text-muted" style="font-family: monospace;">${s.raw_password ? '••••••••' : '—'}</span>
            <button class="icon-btn btn-sm" data-view-password="${s.id}" data-raw="${escapeHtml(s.raw_password)}"><i class="fas fa-eye"></i></button>
            <button class="icon-btn btn-sm" data-delete-student="${s.id}" style="color: var(--danger);"><i class="fas fa-trash"></i></button>
        </div>`
    ]);

    list.innerHTML = renderTable(headers, rows, "No students found.");
    
    // Populate issue dropdown if it exists
    const issueSelect = qs("#issueStudent");
    if (issueSelect) {
        issueSelect.innerHTML = data.students.map(s => 
            `<option value="${s.id}">${escapeHtml(s.name)}</option>`
        ).join("");
    }
}

async function loadTransactions(page) {
    const target = page === "admin" ? qs("#adminTransactions") : qs("#studentTransactions");
    if (!target) return;

    const data = await api("/transactions");
    const ts = data.transactions;

    if (page === "admin") {
        const headers = ["Book", "Student", "Issue Date", "Due Date", "Status", "Fine", "Action"];
        const rows = ts.map(t => [
            `<strong>${escapeHtml(t.book_title)}</strong>`,
            escapeHtml(t.student_name),
            t.issue_date,
            t.due_date,
            `<span class="badge ${t.status === 'issued' ? 'badge-warning' : 'badge-success'}">${t.status}</span>`,
            `<span class="${Number(t.fine_amount) > 0 ? 'text-danger font-bold' : ''}">₹${t.fine_amount}</span>`,
            t.status === 'issued' 
                ? `<button class="btn btn-secondary btn-sm" data-return="${t.id}">Return</button>` 
                : '<i class="fas fa-check-circle text-success"></i>'
        ]);
        target.innerHTML = renderTable(headers, rows);
    } else {
        const headers = ["Book", "Author", "Due Date", "Status", "Fine"];
        const rows = ts.map(t => [
            `<strong>${escapeHtml(t.book_title)}</strong>`,
            escapeHtml(t.author),
            t.due_date,
            `<span class="badge ${t.status === 'issued' ? 'badge-warning' : 'badge-success'}">${t.status}</span>`,
            `₹${t.fine_amount}`
        ]);
        target.innerHTML = renderTable(headers, rows);
    }
    wireTransactionActions(page);
}

async function loadReports() {
    const issuedReport = qs("#issuedReport");
    if (!issuedReport) return;

    const data = await api("/reports");
    const stats = data.stats;

    // Update KPI counters
    const updateCounter = (id, val) => {
        const el = qs(id);
        if (el) el.textContent = val;
    };

    updateCounter("#statBooks", stats.total_books);
    updateCounter("#statAvailable", stats.available_books);
    updateCounter("#statIssued", stats.issued_count);
    updateCounter("#statOverdue", stats.overdue_count);
    updateCounter("#statFine", `₹${stats.fine_total}`);

    const renderActivity = (list, target, empty, color = "var(--primary)") => {
        target.innerHTML = list.length 
            ? list.map(i => `
                <div class="insight-item mb-4">
                    <div class="insight-dot" style="background-color: ${color};"></div>
                    <div style="flex: 1;">
                        <div style="font-weight: 700; font-size: 0.85rem; margin-bottom: 2px;">${escapeHtml(i.book_title)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(i.student_name)}</div>
                        <div style="font-size: 0.65rem; color: ${color}; font-weight: 800; margin-top: 4px;">DUE ${i.due_date}</div>
                    </div>
                </div>`).join("")
            : `<div class="p-4 text-center text-muted text-xs">${empty}</div>`;
    };

    renderActivity(data.overdue, qs("#overdueReport"), "No overdue items.", "var(--danger)");
    renderActivity(data.issued, issuedReport, "No active issues.", "var(--primary)");
}

async function loadRequests() {
    const target = qs("#adminRequests");
    if (!target) return;

    const data = await api("/admin/requests");
    const reqs = data.requests;

    const headers = ["Student", "Book", "Time", "Action"];
    const rows = reqs.map(r => [
        escapeHtml(r.student_name),
        `<strong>${escapeHtml(r.book_title)}</strong>`,
        r.request_time,
        `<div class="d-flex gap-2">
            <button class="btn btn-primary btn-sm" data-approve="${r.id}">Approve</button>
            <button class="btn btn-danger btn-sm" data-reject="${r.id}">Reject</button>
        </div>`
    ]);

    target.innerHTML = renderTable(headers, rows, "No pending requests.");
    
    // Update notification bell
    const badge = qs("#bellBadge");
    if (badge) {
        badge.textContent = reqs.length;
        badge.style.display = reqs.length > 0 ? "inline-flex" : "none";
    }

    const notifList = qs("#notificationList");
    if (notifList) {
        notifList.innerHTML = reqs.length 
            ? reqs.map(r => `<div class="mb-2"><strong>${escapeHtml(r.student_name)}</strong> requested <em>${escapeHtml(r.book_title)}</em></div>`).join("")
            : "No new requests";
    }
    wireRequestActions();
}

async function loadStudentStats() {
    const statsContainer = qs("#studentIssued");
    if (!statsContainer) return;

    const data = await api("/api/student/stats");
    const s = data.stats;

    const update = (id, val) => { if (qs(id)) qs(id).textContent = val; };
    update("#studentIssued", s.issued_books_count);
    update("#studentFine", `₹${s.total_fine}`);
    update("#studentAvailable", s.available_books);
    update("#studentSubjects", s.total_subjects);
}

// Action Handlers
function wireBookActions(books, page) {
    qsa("[data-edit-book]").forEach(btn => {
        btn.addEventListener("click", () => {
            const b = books.find(x => x.id == btn.dataset.editBook);
            if (!b) return;
            qs("#bookFormTitle").textContent = "Edit Book";
            qs("#bookId").value = b.id;
            qs("#bookTitle").value = b.title;
            qs("#bookAuthor").value = b.author;
            qs("#bookCategory").value = b.category;
            qs("#bookQuantity").value = b.total_quantity;
            qs("#bookShelf").value = b.shelf;
            qs("#bookFormModal").classList.add("show");
        });
    });

    qsa("[data-delete-book]").forEach(btn => {
        btn.addEventListener("click", async () => {
            if (!confirm("Permanently delete this book?")) return;
            await api(`/books/${btn.dataset.deleteBook}`, { method: "DELETE" });
            showToast("Book deleted successfully");
            loadBooks(page);
        });
    });

    qsa("[data-request-book]").forEach(btn => {
        btn.addEventListener("click", async () => {
            btn.disabled = true;
            const res = await api("/request-book", {
                method: "POST",
                body: JSON.stringify({ book_id: Number(btn.dataset.requestBook) })
            });
            showToast(res.message);
            await refreshStudent();
        });
    });
    
    qsa("[data-rejection-reason]").forEach(btn => {
        btn.addEventListener("click", () => {
            alert(`Rejection Reason: ${btn.dataset.rejectionReason}`);
        });
    });
}

function wireTransactionActions(page) {
    qsa("[data-return]").forEach(btn => {
        btn.addEventListener("click", async () => {
            const res = await api("/return", {
                method: "POST",
                body: JSON.stringify({ transaction_id: Number(btn.dataset.return) })
            });
            showToast(`Returned! Fine calculated: ₹${res.fine}`);
            page === "admin" ? refreshAdmin() : refreshStudent();
        });
    });
}

function wireRequestActions() {
    qsa("[data-approve]").forEach(btn => {
        btn.addEventListener("click", async () => {
            const res = await api("/approve-request", {
                method: "POST",
                body: JSON.stringify({ request_id: Number(btn.dataset.approve) })
            });
            showToast(res.message);
            refreshAdmin();
        });
    });

    qsa("[data-reject]").forEach(btn => {
        btn.addEventListener("click", async () => {
            const reason = prompt("Enter rejection reason:", "Out of stock");
            if (reason === null) return;
            const res = await api("/reject-request", {
                method: "POST",
                body: JSON.stringify({ request_id: Number(btn.dataset.reject), reason })
            });
            showToast(res.message);
            refreshAdmin();
        });
    });
}

// Global Refreshers
async function refreshAdmin() {
    await loadBooks("admin");
    await loadStudents();
    await loadTransactions("admin");
    await loadReports();
    await loadRequests();
}

async function refreshStudent() {
    await loadBooks("student");
    await loadTransactions("student");
    await loadStudentStats();
}

// Initialization
document.addEventListener("DOMContentLoaded", () => {
    const page = document.body.dataset.page;

    // Sidebar & Navigation
    qsa(".nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            const href = item.getAttribute("href");
            if (href && href.startsWith("#")) {
                updateSidebarActive(href.substring(1));
            }
        });
    });

    // Forms
    qs("#loginForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const res = await api("/login", {
            method: "POST",
            body: JSON.stringify({
                role: qs("#role").value,
                username: qs("#username").value,
                password: qs("#password").value
            })
        });
        showToast(res.message);
        setTimeout(() => window.location.href = res.redirect, 500);
    });

    qs("#bookForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const id = qs("#bookId").value;
        const payload = {
            title: qs("#bookTitle").value,
            author: qs("#bookAuthor").value,
            category: qs("#bookCategory").value,
            total_quantity: Number(qs("#bookQuantity").value),
            shelf: qs("#bookShelf").value
        };
        await api(id ? `/books/${id}` : "/books", {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(payload)
        });
        showToast(id ? "Book updated" : "Book added");
        qs("#bookFormModal").classList.remove("show");
        refreshAdmin();
    });

    qs("#issueForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const res = await api("/get", {
            method: "POST",
            body: JSON.stringify({
                user_id: Number(qs("#issueStudent").value),
                book_id: Number(qs("#issueBook").value)
            })
        });
        showToast(res.message);
        refreshAdmin();
    });

    // Profile & Settings
    qs("#openSettings")?.addEventListener("click", () => qs("#settingsModal").classList.add("show"));
    qs("#closeSettings")?.addEventListener("click", () => qs("#settingsModal").classList.remove("show"));
    
    qs("#profileForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        await api("/api/admin/update-profile", {
            method: "POST",
            body: JSON.stringify({
                name: qs("#profileName").value,
                username: qs("#profileUsername").value
            })
        });
        showToast("Profile updated");
        setTimeout(() => location.reload(), 1000);
    });

    // Search
    const search = qs("#adminBookSearch") || qs("#bookSearch");
    if (search) {
        search.addEventListener("input", (e) => {
            const debounce = (fn, ms) => {
                let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
            };
            const debouncedLoad = debounce(() => loadBooks(page), 300);
            debouncedLoad();
        });
    }

    // Role Buttons
    qsa("[data-login-role]").forEach(btn => {
        btn.addEventListener("click", () => {
            qsa("[data-login-role]").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            qs("#role").value = btn.dataset.loginRole;
        });
    });

    // Notifications
    qs("#bellIcon")?.addEventListener("click", (e) => {
        e.stopPropagation();
        const dropdown = qs("#notificationDropdown");
        dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
    });

    document.addEventListener("click", () => {
        const dropdown = qs("#notificationDropdown");
        if (dropdown) dropdown.style.display = "none";
    });

    // Forgot Password Flow
    const forgotLink = qs("#forgotPasswordLink");
    const backToLogin = qs("#backToLogin");
    const loginForm = qs("#loginForm");
    const forgotShell = qs("#forgotPasswordShell");
    const roleToggle = qs("#roleToggle");

    forgotLink?.addEventListener("click", () => {
        loginForm.hidden = true;
        if (roleToggle) roleToggle.style.display = "none";
        forgotShell.hidden = false;
        qs("#resetRole").value = qs("#role").value;
        qs("#forgotPasswordForm").hidden = false;
        qs("#verifyOtpForm").hidden = true;
        qs("#resetPasswordForm").hidden = true;
    });

    backToLogin?.addEventListener("click", () => {
        forgotShell.hidden = true;
        loginForm.hidden = false;
        if (roleToggle) roleToggle.style.display = "flex";
    });

    qs("#forgotPasswordForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const res = await api("/forgot-password", {
            method: "POST",
            body: JSON.stringify({
                role: qs("#resetRole").value,
                identifier: qs("#resetIdentifier").value
            })
        });
        showToast(res.message);
        qs("#forgotPasswordForm").hidden = true;
        qs("#verifyOtpForm").hidden = false;
    });

    qs("#verifyOtpForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const code = qs("#verifyCode").value;
        const res = await api("/verify-otp", {
            method: "POST",
            body: JSON.stringify({
                role: qs("#resetRole").value,
                identifier: qs("#resetIdentifier").value,
                code: code
            })
        });
        showToast(res.message);
        window.currentResetCode = code; // temporary store for the next step
        qs("#verifyOtpForm").hidden = true;
        qs("#resetPasswordForm").hidden = false;
    });

    qs("#resetPasswordForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pass = qs("#newPassword").value;
        const confirm = qs("#confirmPassword").value;
        if (pass !== confirm) return showToast("Passwords do not match", "error");

        const res = await api("/reset-password", {
            method: "POST",
            body: JSON.stringify({
                role: qs("#resetRole").value,
                identifier: qs("#resetIdentifier").value,
                code: window.currentResetCode,
                new_password: pass,
                confirm_password: confirm
            })
        });
        showToast(res.message);
        backToLogin.click();
    });

    // Password Toggles
    const setupToggle = (btnId, inputId) => {
        const btn = qs(btnId);
        const input = qs(inputId);
        if (!btn || !input) return;
        btn.addEventListener("click", () => {
            const isPass = input.type === "password";
            input.type = isPass ? "text" : "password";
            btn.textContent = isPass ? "Hide" : "Show";
        });
    };
    setupToggle("#togglePassword", "#password");

    // Initial Load
    if (page === "admin") refreshAdmin();
    if (page === "student") refreshStudent();
});

// Expose returnBook for inline onclicks if needed (though we use data attributes now)
window.returnBook = async (id) => {
    const res = await api("/return", {
        method: "POST",
        body: JSON.stringify({ transaction_id: id })
    });
    showToast(`Returned! Fine: ₹${res.fine}`);
    refreshAdmin();
};

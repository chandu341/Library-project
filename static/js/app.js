const DEFAULT_COVER = "https://images.unsplash.com/photo-1519682337058-a94d519337bc?auto=format&fit=crop&w=900&q=80";

const qs = (selector) => document.querySelector(selector);
const qsa = (selector) => [...document.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({ success: false, message: "Invalid server response." }));
  if (!response.ok || !data.success) {
    throw new Error(data.message || "Request failed.");
  }
  return data;
}

function setMessage(element, message, isError = false) {
  if (!element) return;
  element.textContent = message;
  element.classList.toggle("error", isError);
}

function debounce(fn, delay = 250) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function initRevealDelays() {
  qsa(".reveal-card").forEach((item, index) => {
    item.style.setProperty("--reveal-delay", `${Math.min(index % 5, 4) * 90}ms`);
  });
}

function initReveals() {
  const items = qsa(".reveal");
  if (!items.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });

  items.forEach((item) => observer.observe(item));
}

function initMenu() {
  const toggle = qs("[data-menu-toggle]");
  const links = qs("[data-nav-links]");
  if (!toggle || !links) return;

  toggle.addEventListener("click", () => links.classList.toggle("open"));
  qsa("[data-nav-links] a").forEach((link) => {
    link.addEventListener("click", () => links.classList.remove("open"));
  });
}

function initNavbarState() {
  const navbar = qs(".navbar");
  if (!navbar) return;

  const sync = () => navbar.classList.toggle("scrolled", window.scrollY > 12);
  sync();
  window.addEventListener("scroll", sync, { passive: true });
}

function animateCounter(element, value) {
  if (!element) return;
  const target = Number(value || 0);
  const duration = 700;
  const start = performance.now();

  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    element.textContent = Math.floor(target * progress);
    if (progress < 1) requestAnimationFrame(tick);
  };

  requestAnimationFrame(tick);
}

function initLogin() {
  const form = qs("#loginForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = qs("#loginMessage");
    setMessage(message, "Checking details...");

    try {
      const data = await api("/login", {
        method: "POST",
        body: JSON.stringify({
          role: qs("#role").value,
          username: qs("#username").value,
          password: qs("#password").value,
        }),
      });
      setMessage(message, data.message);
      window.location.href = data.redirect;
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });
}

function togglePasswordButton(button, input) {
  if (!button || !input) return;

  button.addEventListener("click", () => {
    const isHidden = input.type === "password";
    input.type = isHidden ? "text" : "password";
    button.textContent = isHidden ? "Hide" : "Show";
  });
}

function initHomepageLoginReveal() {
  const panel = qs("#login-card");
  const shell = qs("#loginFormShell");
  const resetShell = qs("#forgotPasswordShell");
  const roleInput = qs("#role");
  const resetRoleInput = qs("#resetRole");
  const selectedRoleLabel = qs("#selectedRoleLabel");
  const resetRoleLabel = qs("#resetRoleLabel");
  const submitLogin = qs("#submitLogin");
  const roleButtons = qs("#roleButtons");
  const changeRole = qs("#changeRole");
  const forgotPasswordLink = qs("#forgotPasswordLink");
  const backToLogin = qs("#backToLogin");
  const togglePassword = qs("#togglePassword");
  const toggleNewPassword = qs("#toggleNewPassword");
  const password = qs("#password");
  const newPassword = qs("#newPassword");
  const triggers = qsa("[data-login-role]");

  if (!panel || !shell || !roleInput) return;

  const roleTitle = (role) => (role === "student" ? "Student Login" : "Admin Login");
  const resetTitle = (role) => (role === "student" ? "Student Password Reset" : "Admin Password Reset");
  const selectedRole = () => roleInput.value || "admin";

  const openLogin = (event, forcedRole) => {
    if (event) event.preventDefault();
    const role = forcedRole || event?.currentTarget?.dataset.loginRole || "admin";
    roleInput.value = role;
    if (resetRoleInput) resetRoleInput.value = role;
    if (selectedRoleLabel) selectedRoleLabel.textContent = roleTitle(role);
    if (resetRoleLabel) resetRoleLabel.textContent = resetTitle(role);
    if (submitLogin) submitLogin.textContent = roleTitle(role);
    if (roleButtons) roleButtons.hidden = true;
    shell.hidden = false;
    if (resetShell) resetShell.hidden = true;
    panel.classList.add("form-open");
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => qs("#username")?.focus(), 260);
  };

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", (event) => openLogin(event, trigger.dataset.loginRole));
  });

  if (changeRole) {
    changeRole.addEventListener("click", () => {
      shell.hidden = true;
      if (resetShell) resetShell.hidden = true;
      if (roleButtons) roleButtons.hidden = false;
      panel.classList.remove("form-open");
      setMessage(qs("#loginMessage"), "");
    });
  }

  if (forgotPasswordLink && resetShell) {
    forgotPasswordLink.addEventListener("click", () => {
      const role = selectedRole();
      if (resetRoleInput) resetRoleInput.value = role;
      if (resetRoleLabel) resetRoleLabel.textContent = resetTitle(role);
      shell.hidden = true;
      resetShell.hidden = false;
      setMessage(qs("#forgotMessage"), "");
      setMessage(qs("#resetMessage"), "");
      setTimeout(() => qs("#resetIdentifier")?.focus(), 180);
    });
  }

  if (backToLogin && resetShell) {
    backToLogin.addEventListener("click", () => {
      resetShell.hidden = true;
      shell.hidden = false;
    });
  }

  togglePasswordButton(togglePassword, password);
  togglePasswordButton(toggleNewPassword, newPassword);
}

function initForgotPassword() {
  const forgotForm = qs("#forgotPasswordForm");
  const resetForm = qs("#resetPasswordForm");
  if (!forgotForm || !resetForm) return;

  forgotForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = qs("#forgotMessage");
    setMessage(message, "Sending email code...");

    try {
      const data = await api("/forgot-password", {
        method: "POST",
        body: JSON.stringify({
          role: qs("#resetRole").value,
          identifier: qs("#resetIdentifier").value,
        }),
      });
      setMessage(message, data.message);
      resetForm.hidden = false;
      setTimeout(() => qs("#resetCode")?.focus(), 180);
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });

  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = qs("#resetMessage");
    setMessage(message, "Updating password...");

    try {
      const data = await api("/reset-password", {
        method: "POST",
        body: JSON.stringify({
          role: qs("#resetRole").value,
          identifier: qs("#resetIdentifier").value,
          code: qs("#resetCode").value,
          new_password: qs("#newPassword").value,
        }),
      });
      setMessage(message, data.message);
      qs("#resetPasswordForm").reset();
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });
}

function bookCard(book, page) {
  const isAvailable = Number(book.available_quantity) > 0;
  const actionButtons = page === "admin"
    ? `<button class="btn ghost" data-edit-book="${book.id}">Edit</button>
       <button class="btn danger" data-delete-book="${book.id}">Delete</button>`
    : `<button class="btn primary" data-issue-self="${book.id}" ${isAvailable ? "" : "disabled"}>Issue</button>`;

  return `
    <article class="book-card reveal visible">
      <img class="book-cover" src="${escapeHtml(book.cover_url || DEFAULT_COVER)}" alt="${escapeHtml(book.title)}">
      <div class="book-body">
        <h3>${escapeHtml(book.title)}</h3>
        <div class="book-meta">
          <div>${escapeHtml(book.author)}</div>
          <div>${escapeHtml(book.category)} - Shelf ${escapeHtml(book.shelf)}</div>
          <div>${escapeHtml(book.available_quantity)}/${escapeHtml(book.total_quantity)} available</div>
        </div>
        <span class="status-pill ${isAvailable ? "" : "empty"}">${isAvailable ? "Available" : "Unavailable"}</span>
        <div class="card-actions">${actionButtons}</div>
      </div>
    </article>`;
}

function reportItem(primary, secondary) {
  return `<div class="report-item"><strong>${escapeHtml(primary)}</strong><span>${escapeHtml(secondary)}</span></div>`;
}

function emptyState(label) {
  return `<div class="report-item"><span>${escapeHtml(label)}</span></div>`;
}

async function loadBooks(page) {
  const grid = qs("#bookGrid");
  if (!grid) return [];

  const query = qs("#bookSearch")?.value || "";
  const data = await api(`/books?q=${encodeURIComponent(query)}`);
  grid.innerHTML = data.books.length ? data.books.map((book) => bookCard(book, page)).join("") : emptyState("No books found.");

  const availableCount = data.books.filter((book) => Number(book.available_quantity) > 0).length;
  animateCounter(qs("#studentAvailable"), availableCount);
  populateIssueBooks(data.books);
  wireBookActions(data.books, page);
  return data.books;
}

function populateIssueBooks(books) {
  const select = qs("#issueBook");
  if (!select) return;

  const availableBooks = books.filter((book) => Number(book.available_quantity) > 0);
  select.innerHTML = availableBooks.map((book) => `<option value="${book.id}">${escapeHtml(book.title)}</option>`).join("");
}

async function loadStudents() {
  const select = qs("#issueStudent");
  if (!select) return;

  const data = await api("/students");
  select.innerHTML = data.students.map((student) => `<option value="${student.id}">${escapeHtml(student.name)}</option>`).join("");
}

function wireBookActions(books, page) {
  if (page === "admin") {
    qsa("[data-edit-book]").forEach((button) => {
      button.addEventListener("click", () => {
        const book = books.find((item) => item.id === Number(button.dataset.editBook));
        if (!book) return;

        qs("#bookFormTitle").textContent = "Edit Book";
        qs("#bookId").value = book.id;
        qs("#bookTitle").value = book.title;
        qs("#bookAuthor").value = book.author;
        qs("#bookCategory").value = book.category;
        qs("#bookQuantity").value = book.total_quantity;
        qs("#bookShelf").value = book.shelf;
        qs("#bookCover").value = book.cover_url || "";
        qs("#bookForm").scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });

    qsa("[data-delete-book]").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!confirm("Delete this book?")) return;
        try {
          await api(`/books/${button.dataset.deleteBook}`, { method: "DELETE" });
          await refreshAdmin();
        } catch (error) {
          alert(error.message);
        }
      });
    });
  }

  if (page === "student") {
    qsa("[data-issue-self]").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await api("/issue", {
            method: "POST",
            body: JSON.stringify({ book_id: Number(button.dataset.issueSelf) }),
          });
          await refreshStudent();
        } catch (error) {
          alert(error.message);
        }
      });
    });
  }
}

function transactionTable(transactions, includeStudent = true) {
  if (!transactions.length) return emptyState("No active records.");

  return `
    <table>
      <thead>
        <tr>
          <th>Book</th>
          ${includeStudent ? "<th>Student</th>" : ""}
          <th>Issue Date</th>
          <th>Due Date</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${transactions.map((item) => `
          <tr>
            <td>${escapeHtml(item.book_title)}</td>
            ${includeStudent ? `<td>${escapeHtml(item.student_name)}</td>` : ""}
            <td>${escapeHtml(item.issue_date)}</td>
            <td>${escapeHtml(item.due_date)}</td>
            <td>${escapeHtml(item.status)}</td>
            <td><button class="btn ghost" data-return="${item.id}">Return</button></td>
          </tr>
        `).join("")}
      </tbody>
    </table>`;
}

async function loadTransactions(page) {
  const target = page === "admin" ? qs("#adminTransactions") : qs("#studentTransactions");
  if (!target) return [];

  const data = await api("/transactions?status=issued");
  target.innerHTML = transactionTable(data.transactions, page === "admin");

  qsa("[data-return]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const result = await api("/return", {
          method: "POST",
          body: JSON.stringify({ transaction_id: Number(button.dataset.return) }),
        });
        alert(`Returned successfully. Fine: Rs.${result.fine}`);
        if (page === "admin") {
          await refreshAdmin();
        } else {
          await refreshStudent();
        }
      } catch (error) {
        alert(error.message);
      }
    });
  });

  return data.transactions;
}

async function loadReports() {
  if (!qs("#issuedReport")) return;

  const data = await api("/reports");
  const stats = data.stats || {};
  animateCounter(qs("#statIssued"), stats.issued || 0);
  animateCounter(qs("#statReturned"), stats.returned || 0);
  animateCounter(qs("#statOverdue"), stats.overdue || 0);
  qs("#statFine").textContent = `Rs.${Number(stats.fine_total || 0)}`;

  qs("#issuedReport").innerHTML = data.issued.length
    ? data.issued.map((item) => reportItem(item.book_title, `${item.student_name} - Due ${item.due_date}`)).join("")
    : emptyState("No issued books.");
  qs("#returnedReport").innerHTML = data.returned.length
    ? data.returned.map((item) => reportItem(item.book_title, `${item.student_name} - Fine Rs.${item.fine_amount}`)).join("")
    : emptyState("No returned books.");
  qs("#overdueReport").innerHTML = data.overdue.length
    ? data.overdue.map((item) => reportItem(item.book_title, `${item.student_name} - Fine Rs.${item.current_fine}`)).join("")
    : emptyState("No overdue books.");
}

function initBookForm() {
  const form = qs("#bookForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = qs("#bookId").value;
    const payload = {
      title: qs("#bookTitle").value,
      author: qs("#bookAuthor").value,
      category: qs("#bookCategory").value,
      total_quantity: Number(qs("#bookQuantity").value),
      shelf: qs("#bookShelf").value,
      cover_url: qs("#bookCover").value,
    };

    try {
      await api(id ? `/books/${id}` : "/books", {
        method: id ? "PUT" : "POST",
        body: JSON.stringify(payload),
      });
      setMessage(qs("#bookMessage"), id ? "Book updated." : "Book added.");
      resetBookForm();
      await refreshAdmin();
    } catch (error) {
      setMessage(qs("#bookMessage"), error.message, true);
    }
  });

  qs("#resetBookForm")?.addEventListener("click", resetBookForm);
}

function resetBookForm() {
  qs("#bookForm")?.reset();
  if (qs("#bookId")) qs("#bookId").value = "";
  if (qs("#bookFormTitle")) qs("#bookFormTitle").textContent = "Add Book";
}

function initIssueForm() {
  const form = qs("#issueForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await api("/issue", {
        method: "POST",
        body: JSON.stringify({
          user_id: Number(qs("#issueStudent").value),
          book_id: Number(qs("#issueBook").value),
        }),
      });
      setMessage(qs("#issueMessage"), `${data.message} Due date: ${data.due_date}`);
      await refreshAdmin();
    } catch (error) {
      setMessage(qs("#issueMessage"), error.message, true);
    }
  });
}

async function refreshAdmin() {
  await loadBooks("admin");
  await loadStudents();
  await loadTransactions("admin");
  await loadReports();
}

async function refreshStudent() {
  await loadBooks("student");
  const transactions = await loadTransactions("student");
  animateCounter(qs("#studentIssued"), transactions.length);

  const today = new Date();
  const fine = transactions.reduce((sum, item) => {
    const due = new Date(item.due_date);
    const daysLate = Math.max(Math.floor((today - due) / 86400000), 0);
    return sum + daysLate * 5;
  }, 0);

  if (qs("#studentFine")) qs("#studentFine").textContent = `Rs.${fine}`;
}

function initSearch(page) {
  const search = qs("#bookSearch");
  if (!search) return;
  search.addEventListener("input", debounce(() => loadBooks(page), 250));
}

document.addEventListener("DOMContentLoaded", async () => {
  initRevealDelays();
  initReveals();
  initMenu();
  initNavbarState();
  initHomepageLoginReveal();
  initForgotPassword();
  initLogin();

  const page = document.body.dataset.page;
  if (page === "admin") {
    initBookForm();
    initIssueForm();
    initSearch("admin");
    qs("#refreshAdmin")?.addEventListener("click", refreshAdmin);
    try {
      await refreshAdmin();
    } catch (error) {
      alert(error.message);
    }
  }

  if (page === "student") {
    initSearch("student");
    qs("#refreshStudent")?.addEventListener("click", refreshStudent);
    try {
      await refreshStudent();
    } catch (error) {
      alert(error.message);
    }
  }
});

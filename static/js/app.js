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

  const sync = () => {
    navbar.classList.toggle("scrolled", window.scrollY > 12);
    
    // Highlight active nav link
    const sections = qsa("section[id]");
    let current = "";
    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      if (window.scrollY >= sectionTop - 120) {
        current = section.getAttribute("id");
      }
    });

    qsa(".nav-links a").forEach((a) => {
      a.classList.toggle("active", a.getAttribute("href") === `#${current}`);
    });
  };
  
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

function initLandingStats() {
  qsa("[data-landing-counter]").forEach((el) => {
    animateCounter(el, el.dataset.landingCounter);
  });

  qsa("[data-percent]").forEach((el) => {
    setTimeout(() => {
      el.style.width = el.dataset.percent + "%";
    }, 400);
  });
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
  const username = qs("#username");
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

  const clearLoginFields = () => {
    if (username) username.value = "";
    if (password) password.value = "";
  };

  const openLogin = (event, forcedRole) => {
    if (event) event.preventDefault();
    const role = forcedRole || event?.currentTarget?.dataset.loginRole || "admin";
    clearLoginFields();
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

    // Toggle forgot links: Hide for students, Show for admins
    const forgotLinks = qs("#forgotLinks");
    if (forgotLinks) {
      forgotLinks.style.display = (role === "student") ? "none" : "flex";
    }
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
      qs("#forgotPasswordForm").hidden = false;
      qs("#verifyOtpForm").hidden = true;
      qs("#resetPasswordForm").hidden = true;
      if (qs("#resetIdentifier")) qs("#resetIdentifier").value = "";
      setMessage(qs("#forgotMessage"), "");
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
  const verifyForm = qs("#verifyOtpForm");
  const resetForm = qs("#resetPasswordForm");
  
  if (!forgotForm || !verifyForm || !resetForm) return;

  let currentCode = "";



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
      forgotForm.hidden = true;
      verifyForm.hidden = false;
      setTimeout(() => qs("#verifyCode")?.focus(), 180);
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });

  verifyForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = qs("#verifyMessage");
    setMessage(message, "Verifying code...");
    const code = qs("#verifyCode").value;

    try {
      const data = await api("/verify-otp", {
        method: "POST",
        body: JSON.stringify({
          role: qs("#resetRole").value,
          identifier: qs("#resetIdentifier").value,
          code: code,
        }),
      });
      setMessage(message, data.message);
      currentCode = code;
      verifyForm.hidden = true;
      resetForm.hidden = false;
      setTimeout(() => qs("#newPassword")?.focus(), 180);
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });

  resetForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = qs("#resetMessage");
    const pass = qs("#newPassword").value;
    const confirm = qs("#confirmPassword").value;

    if (pass !== confirm) {
      return setMessage(message, "Passwords do not match.", true);
    }

    setMessage(message, "Updating password...");

    try {
      const data = await api("/reset-password", {
        method: "POST",
        body: JSON.stringify({
          role: qs("#resetRole").value,
          identifier: qs("#resetIdentifier").value,
          code: currentCode,
          new_password: pass,
          confirm_password: confirm
        }),
      });
      setMessage(message, data.message);
      resetForm.reset();
      setTimeout(() => {
        qs("#backToLogin")?.click();
      }, 2000);
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });

  if (toggleConfirmPassword && confirmPassword) {
    togglePasswordButton(toggleConfirmPassword, confirmPassword);
  }
}

function bookCard(book, page) {
  const isAvailable = Number(book.available_quantity) > 0;
  let actionButtons = "";
  if (page === "admin") {
    actionButtons = `<button class="btn ghost" data-edit-book="${book.id}">Edit</button>
                     <button class="btn danger" data-delete-book="${book.id}">Delete</button>`;
  } else {
    if (book.is_issued) {
      actionButtons = `<button class="btn ghost" disabled>Already Issued</button>`;
    } else if (book.request_status === 'pending') {
      actionButtons = `<button class="btn ghost" disabled>Requested</button>`;
    } else if (book.request_status === 'rejected') {
      actionButtons = `<button class="btn danger-ghost" data-rejection-reason="${escapeHtml(book.rejection_reason || 'Out of stock')}" style="color: #ef4444; border-color: #ef4444; width: 100%;">Rejected</button>`;
    } else {
      actionButtons = `<button class="btn primary" data-request-book="${book.id}" ${isAvailable ? "" : "disabled"}>Request Book</button>`;
    }
  }

  return `
    <article class="book-card reveal visible">
      <div class="book-cover">
        <span class="book-cover-title">${escapeHtml(book.title)}</span>
      </div>
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
  const grid = qs("#adminBookGrid") || qs("#bookGrid");
  if (!grid) return [];

  const searchEl = qs("#adminBookSearch") || qs("#bookSearch");
  const query = searchEl?.value || "";
  const data = await api(`/books?q=${encodeURIComponent(query)}`);
  
  if (page === "student") {
    // Show all books in the catalog except those I already have issued
    const catalogBooks = data.books.filter(b => !b.is_issued);
    
    qs("#bookGrid").innerHTML = catalogBooks.length 
      ? catalogBooks.map(b => bookCard(b, page)).join("") 
      : emptyState("No books found in the library.");
  } else {
    grid.innerHTML = data.books.length ? data.books.map((book) => bookCard(book, page)).join("") : emptyState("No books found.");
  }

  if (qs("#studentTotalBooks")) {
    // Student total books is handled by loadStudentStats for accuracy
  }
  if (qs("#statBooks")) {
    // Admin total books is handled by loadReports for accuracy (stock total)
  }
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
  const list = qs("#studentTable");
  if (!select && !list) return;

  const data = await api("/students");
  if (select) {
    select.innerHTML = data.students.length
      ? data.students.map((student) => `<option value="${student.id}">${escapeHtml(student.name)}</option>`).join("")
      : `<option value="">No students found</option>`;
  }
  if (list) {
    list.innerHTML = studentTable(data.students);
  }
  if (qs("#statStudents")) animateCounter(qs("#statStudents"), data.students.length);
}

function studentTable(students) {
  if (!students.length) return emptyState("No student accounts yet.");

  return `
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Username</th>
          <th>Email</th>
          <th>Password</th>
        </tr>
      </thead>
      <tbody>
        ${students.map((student) => `
          <tr>
            <td>${escapeHtml(student.name)}</td>
            <td>${escapeHtml(student.username)}</td>
            <td>${escapeHtml(student.email)}</td>
            <td>
              <div class="password-cell">
                <span class="masked-pass" id="pass-${student.id}" data-hidden="true">${student.raw_password ? "••••••••" : "—"}</span>
                <button class="eye-btn" data-view-password="${student.id}" data-raw="${escapeHtml(student.raw_password || "")}" title="Toggle Visibility">👁️</button>
                <button class="eye-btn" data-reset-password="${student.id}" title="Update Password" style="margin-left: 0.25rem; font-size: 1rem; opacity: 0.7;">✏️</button>
                <button class="eye-btn" data-delete-student="${student.id}" title="Delete Student" style="margin-left: 0.25rem; font-size: 1rem; opacity: 0.7; color: var(--danger);">🗑️</button>
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>`;
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
    qsa("[data-request-book]").forEach((button) => {
      button.addEventListener("click", async () => {
        const originalText = button.textContent;
        try {
          button.disabled = true;
          button.textContent = "Processing...";
          
          const result = await api("/request-book", {
            method: "POST",
            body: JSON.stringify({ book_id: Number(button.dataset.requestBook) }),
          });
          
          if (result.success) {
            button.textContent = "Requested";
            button.className = "btn ghost full";
            alert(result.message);
            await refreshStudent(); // Sync entire UI
          } else {
            button.disabled = false;
            button.textContent = originalText;
            alert(result.message);
          }
        } catch (error) {
          button.disabled = false;
          button.textContent = originalText;
          alert(error.message);
        }
      });
    });

    qsa("[data-rejection-reason]").forEach((button) => {
      button.addEventListener("click", () => {
        alert(`Rejection Reason: ${button.dataset.rejectionReason}`);
      });
    });

    qsa("[data-dismiss-request]").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!confirm("Dismiss this rejected request? You will be able to request this book again.")) return;
        try {
          const res = await api(`/api/student/requests/${button.dataset.dismissRequest}/dismiss`, { method: "POST" });
          alert(res.message);
          await refreshStudent();
        } catch (err) { alert(err.message); }
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
          <th>Issue Time</th>
          <th>Due Time</th>
          <th>Return Time</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${transactions.map((item) => {
          const isReturned = item.status === 'returned';
          const isOverdue = item.status === 'overdue';
          const statusClass = isReturned ? 'success' : (isOverdue ? 'danger' : 'primary');
          
          return `
          <tr>
            <td>${escapeHtml(item.book_title)}</td>
            ${includeStudent ? `<td>${escapeHtml(item.student_name)}</td>` : ""}
            <td>${escapeHtml(item.issue_date)}</td>
            <td>${escapeHtml(item.due_date)}</td>
            <td>${escapeHtml(item.return_date || "—")}</td>
            <td><span class="status-pill ${statusClass}">${escapeHtml(item.status.toUpperCase())}</span></td>
            <td>
              ${!isReturned ? `<button class="btn ghost" data-return="${item.id}">Return</button>` : `<span class="muted">Completed</span>`}
            </td>
          </tr>`;
        }).join("")}
      </tbody>
    </table>`;
}

async function loadTransactions(page) {
  const target = page === "admin" ? qs("#adminTransactions") : qs("#studentTransactions");
  if (!target) return [];

  const data = await api("/transactions");
  const transactions = page === "student" 
    ? data.transactions.filter(t => t.status === 'issued' || t.status === 'overdue')
    : data.transactions;
    
  target.innerHTML = transactionTable(transactions, page === "admin");

  wireReturnActions(page);
}

function wireReturnActions(page) {
  qsa("[data-return]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        const result = await api("/return", {
          method: "POST",
          body: JSON.stringify({ transaction_id: Number(button.dataset.return) }),
        });
        alert(`Returned successfully. Fine: ₹${result.fine}`);
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
}

async function loadReports() {
  if (!qs("#issuedReport")) return;

  const data = await api("/reports");
  const stats = data.stats;

  const issuedEl = qs("#statIssued");
  const booksEl = qs("#statBooks");
  const availableEl = qs("#statAvailable");
  const subjectsEl = qs("#statSubjects");
  
  if (issuedEl) animateCounter(issuedEl, stats.issued_count || 0);
  if (booksEl) animateCounter(booksEl, stats.total_books || 0);
  if (availableEl) animateCounter(availableEl, stats.available_books || 0);
  if (subjectsEl) animateCounter(subjectsEl, stats.total_subjects || 0);
  
  const fineEl = qs("#statFine");
  if (fineEl) fineEl.textContent = `₹${Number(stats.fine_total || 0)}`;

  qs("#issuedReport").innerHTML = data.issued.length
    ? data.issued.map((item) => reportItem(item.book_title, `${item.student_name} - Due ${item.due_date}`)).join("")
    : emptyState("No active issues.");
  qs("#returnedReport").innerHTML = data.returned.length
    ? data.returned.map((item) => reportItem(item.book_title, `${item.student_name} - Fine ₹${item.fine_amount}`)).join("")
    : emptyState("No returned books.");
  qs("#overdueReport").innerHTML = data.overdue.length
    ? data.overdue.map((item) => reportItem(item.book_title, `${item.student_name} - Fine ₹${item.current_fine}`)).join("")
    : emptyState("No overdue books.");
}

async function loadRequests() {
  const target = qs("#adminRequests");
  if (!target) return;

  try {
    const data = await api("/admin/requests");
    target.innerHTML = requestTable(data.requests);
    
    const count = data.requests.length;
    const title = qs("#requests-section h2");
    if (title) {
      title.innerHTML = `Book Requests ${count > 0 ? `<span class="badge danger animate-pulse">${count}</span>` : ""}`;
    }

    const bellBadge = qs("#bellBadge");
    const notifList = qs("#notificationList");
    if (bellBadge && notifList) {
      bellBadge.textContent = count;
      bellBadge.style.display = count > 0 ? "inline-block" : "none";
      if (count > 0) {
        notifList.innerHTML = data.requests.map(r => `<div><strong>${escapeHtml(r.student_name)}</strong> requested <em>${escapeHtml(r.book_title)}</em></div>`).join("");
      } else {
        notifList.innerHTML = "<div>No new requests</div>";
      }
    }

    wireRequestActions();
  } catch (error) {
    target.innerHTML = emptyState(error.message);
  }
}

function requestTable(requests) {
  if (!requests.length) return emptyState("No pending requests.");

  return `
    <table>
      <thead>
        <tr>
          <th>Student</th>
          <th>Book</th>
          <th>Requested At</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        ${requests.map((req) => `
          <tr>
            <td>${escapeHtml(req.student_name)}</td>
            <td>${escapeHtml(req.book_title)}</td>
            <td>${escapeHtml(req.request_time)}</td>
            <td>
              <div class="card-actions">
                ${req.status === 'pending' ? `
                  <button class="btn primary" data-approve="${req.id}">Approve</button>
                  <button class="btn danger" data-reject="${req.id}">Reject</button>
                ` : `
                  <span class="status-pill ${req.status}">${req.status.toUpperCase()}</span>
                  <button class="btn ghost btn-sm" data-reset="${req.id}" title="Allow student to re-request">Reset</button>
                `}
              </div>
            </td>
          </tr>
        `).join("")}
      </tbody>
    </table>`;
}

function wireRequestActions() {
  qsa("[data-approve]").forEach(btn => {
    btn.addEventListener("click", async () => {
      try {
        const res = await api("/approve-request", {
          method: "POST",
          body: JSON.stringify({ request_id: Number(btn.dataset.approve) })
        });
        alert(res.message);
        await refreshAdmin();
      } catch (err) { alert(err.message); }
    });
  });
  
  qsa("[data-reject]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const reason = prompt("Enter rejection reason:", "Out of stock");
      if (reason === null) return; // User cancelled
      try {
        const res = await api("/reject-request", {
          method: "POST",
          body: JSON.stringify({ 
            request_id: Number(btn.dataset.reject),
            reason: reason
          })
        });
        alert(res.message);
        await refreshAdmin();
      } catch (err) { alert(err.message); }
    });
  });

  qsa("[data-reset]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (!confirm("Reset this rejected request? Student will be able to request this book again.")) return;
      try {
        const res = await api(`/api/admin/requests/${btn.dataset.reset}/reset`, {
          method: "POST"
        });
        alert(res.message);
        await refreshAdmin();
      } catch (err) { alert(err.message); }
    });
  });
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
      const data = await api("/get", {
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

function initStudentForm() {
  const form = qs("#studentForm");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      name: qs("#studentName").value,
      username: qs("#studentUsername").value,
      email: qs("#studentEmail").value,
      password: qs("#studentPassword").value,
    };

    try {
      const data = await api("/students", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setMessage(qs("#studentMessage"), "Student added successfully.");
      form.reset();
      await loadStudents();
    } catch (error) {
      setMessage(qs("#studentMessage"), error.message, true);
    }
  });
}

async function refreshAdmin() {
  await loadBooks("admin");
  await loadStudents();
  await loadTransactions("admin");
  await loadRequests();
  await loadReports();
}

async function loadStudentStats() {
  try {
    console.log("Fetching student stats...");
    const data = await api("/api/student/stats");
    const stats = data.stats;
    console.log("Stats received:", stats);

    if (qs("#studentIssued")) {
      animateCounter(qs("#studentIssued"), stats.issued_books_count);
    }
    if (qs("#studentAvailable")) {
      animateCounter(qs("#studentAvailable"), stats.available_books);
    }
    if (qs("#studentSubjects")) {
      animateCounter(qs("#studentSubjects"), stats.total_subjects);
    }
    if (qs("#studentTotalBooks")) {
      animateCounter(qs("#studentTotalBooks"), stats.total_books);
    }
    if (qs("#studentFine")) {
      qs("#studentFine").textContent = `₹${stats.total_fine}`;
    }
    return true;
  } catch (err) {
    console.error("Failed to load student stats:", err);
    return false;
  }
}

async function refreshStudent() {
  try {
    console.log("1. Loading books...");
    await loadBooks("student");
    
    console.log("2. Loading transactions...");
    await loadTransactions("student");
    
    console.log("3. Loading stats...");
    await loadStudentStats();
    
    console.log("Dashboard refresh complete.");
  } catch (err) {
    console.error("Refresh failed:", err);
    alert("Refresh error: " + err.message);
  }
}

function initSearch(page) {
  const search = qs("#adminBookSearch") || qs("#bookSearch");
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
  initLandingStats();

  const page = document.body.dataset.page;
  if (page === "admin") {
    initBookForm();
    initStudentForm();
    initIssueForm();
    initSearch("admin");
    qs("#refreshAdmin")?.addEventListener("click", refreshAdmin);
    qs("#refreshStudents")?.addEventListener("click", loadStudents);
    initAdminProfile();
    initNotifications();
    initPasswordToggles();
    try {
      await refreshAdmin();
    } catch (error) {
      alert(error.message);
    }
  }

  if (page === "student") {
    initSearch("student");
    qs("#refreshStudent")?.addEventListener("click", refreshStudent);
    
    // Wire rejection reason alerts for the unified catalog
    document.addEventListener("click", (e) => {
      const rejectBtn = e.target.closest("[data-rejection-reason]");
      if (rejectBtn) {
        alert(`Rejection Reason: ${rejectBtn.dataset.rejectionReason}`);
      }
    });

    try {
      await refreshStudent();
    } catch (error) {
      alert(error.message);
    }
  }
});

function initAdminProfile() {
  const form = qs("#profileForm");
  const modal = qs("#settingsModal");
  const openBtn = qs("#openSettings");
  const closeBtn = qs("#closeSettings");

  if (!form || !modal) return;

  openBtn?.addEventListener("click", () => {
    modal.classList.add("show");
  });

  const closeModal = () => {
    modal.classList.remove("show");
    setMessage(qs("#profileMessage"), "");
  };

  closeBtn?.addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = qs("#profileMessage");
    setMessage(message, "Updating...");

    try {
      await api("/api/admin/update-profile", {
        method: "POST",
        body: JSON.stringify({
          name: qs("#profileName").value,
          username: qs("#profileUsername").value,
        }),
      });
      setMessage(message, "Profile updated successfully!");
      setTimeout(closeModal, 1500);
    } catch (error) {
      setMessage(message, error.message, true);
    }
  });
}

function initPasswordToggles() {
  document.addEventListener("click", async (e) => {
    const toggleBtn = e.target.closest("[data-toggle]");
    if (toggleBtn) {
      const input = qs(toggleBtn.dataset.toggle);
      if (input) {
        const isPass = input.type === "password";
        input.type = isPass ? "text" : "password";
        toggleBtn.textContent = isPass ? "🙈" : "👁️";
      }
      return;
    }

    const resetBtn = e.target.closest("[data-reset-password]");
    if (resetBtn) {
      const studentId = resetBtn.dataset.resetPassword;
      const newPass = prompt("Enter new password for this student:");
      if (!newPass) return;
      if (newPass.length < 6) return alert("Password must be at least 6 characters.");

      try {
        await api("/api/admin/reset-student-password", {
          method: "POST",
          body: JSON.stringify({ user_id: Number(studentId), password: newPass })
        });
        alert("Password updated successfully.");
        await loadStudents(); // Refresh to get new raw_password
      } catch (err) {
        alert(err.message);
      }
      return;
    }

    const viewBtn = e.target.closest("[data-view-password]");
    if (viewBtn) {
      const studentId = viewBtn.dataset.viewPassword;
      const rawPass = viewBtn.dataset.raw;
      const span = qs(`#pass-${studentId}`);
      if (span) {
        const isHidden = span.dataset.hidden === "true";
        if (isHidden) {
          span.textContent = rawPass || "Not Set";
          span.dataset.hidden = "false";
          viewBtn.textContent = "🙈";
        } else {
          span.textContent = rawPass ? "••••••••" : "—";
          span.dataset.hidden = "true";
          viewBtn.textContent = "👁️";
        }
      }
    }

    const deleteBtn = e.target.closest("[data-delete-student]");
    if (deleteBtn) {
      const studentId = deleteBtn.dataset.deleteStudent;
      if (!confirm("Are you sure you want to delete this student permanently? All their transaction history will also be removed.")) return;

      try {
        await api(`/students/${studentId}`, { method: "DELETE" });
        alert("Student deleted successfully.");
        await loadStudents();
      } catch (err) {
        alert(err.message);
      }
    }
  });
}

function initNotifications() {
  const bellBtn = qs("#bellIcon");
  const dropdown = qs("#notificationDropdown");
  if (!bellBtn || !dropdown) return;

  bellBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
  });

  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target) && e.target !== bellBtn) {
      dropdown.style.display = "none";
    }
  });
}

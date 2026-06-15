const API_BASE = "http://127.0.0.1:8001";

const $ = (selector) => document.querySelector(selector);

// ---- Auth ----
const AUTH_KEY = "ops_digital_employee_auth";

function getAuth() {
  try { return JSON.parse(localStorage.getItem(AUTH_KEY) || "null"); } catch { return null; }
}

function setAuth(data) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(data));
}

function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
}

function requireAuth() {
  const auth = getAuth();
  const modal = $("#loginModal");
  if (!auth || !auth.token) {
    if (modal) {
      modal.classList.add("open");
      return false;
    }
    location.href = "./index.html";
    return false;
  }

  // Role-based access: viewer can only use self-service
  const page = document.body.dataset.page;
  const adminPages = ["dashboard", "tickets", "users", "knowledge", "rpa"];
  if (adminPages.includes(page) && auth.user?.role === "viewer") {
    if (modal) {
      modal.classList.add("open");
      const errorEl = $("#loginError");
      if (errorEl) {
        errorEl.textContent = "viewer 无权限访问后台，请使用 admin 或 operator 账号";
        errorEl.style.display = "";
      }
      return false;
    }
    location.href = "./self-service.html";
    return false;
  }

  // Show user info
  const info = $("#userInfo");
  const display = $("#displayUser");
  if (info) info.style.display = "";
  if (display) display.textContent = `👤 ${auth.user?.username || "已登录"}`;
  return true;
}

async function doLogin() {
  const username = $("#loginUsername").value.trim();
  const password = $("#loginPassword").value.trim();
  const errorEl = $("#loginError");
  const btn = $("#loginBtn");
  if (!username || !password) return;

  btn.disabled = true;
  btn.textContent = "登录中...";
  if (errorEl) errorEl.style.display = "none";

  try {
    const result = await fetch(`${API_BASE}/users/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await result.json();
    if (!result.ok) {
      throw new Error(data.detail || "登录失败");
    }
    setAuth(data);
    const modal = $("#loginModal");
    if (modal) modal.classList.remove("open");
    // Refresh the page to load authenticated content
    location.reload();
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = err.message;
      errorEl.style.display = "";
    }
  } finally {
    btn.disabled = false;
    btn.textContent = "登 录";
  }
}

function doLogout() {
  clearAuth();
  location.reload();
}

// ---- End Auth ----

function bind(selector, event, handler) {
  const element = $(selector);
  if (element) {
    element.addEventListener(event, (nativeEvent) => {
      nativeEvent.preventDefault();
      handler().catch((error) => showError(error));
    });
  }
}

function showJson(selector, data) {
  const target = $(selector);
  if (target) {
    target.textContent = JSON.stringify(data, null, 2);
  }
}

function showTicketData(data) {
  const el = $("#ticketResult");
  if (!el) return;
  if (!data || data.error) {
    el.textContent = data ? JSON.stringify(data, null, 2) : "暂无数据";
    return;
  }
  const statusMap = { open: "待处理", in_progress: "处理中", resolved: "已解决", closed: "已关闭" };
  const priorityMap = { low: "低", normal: "普通", high: "高", urgent: "紧急" };
  const lines = [
    `工单 #${data.id}  —  ${statusMap[data.status] || data.status}`,
    "",
    `问题        ${data.question || "-"}`,
    `报障人      ${data.user || "-"}  (${data.contact || "-"})`,
    `类别        ${data.category || "-"}`,
    `优先级      ${priorityMap[data.priority] || data.priority}`,
    `处理人      ${data.resolver || "-"}`,
    `处理结果    ${data.answer || "-"}`,
    `回访状态    ${data.callback_status || "-"}`,
    `回访记录    ${data.callback_note || "-"}`,
    `创建时间    ${data.created_at || "-"}`,
    `更新时间    ${data.updated_at || "-"}`,
    data.resolved_at ? `解决时间    ${data.resolved_at}` : "",
  ].filter(Boolean).join("\n");
  el.textContent = lines;
}

function showError(error) {
  const message = { error: error.message || String(error) };
  const page = document.body.dataset.page;
  if (page === "tickets") {
    showTicketData(message);
    return;
  }
  const target =
    page === "tickets"
      ? "#ticketResult"
      : page === "users"
        ? "#userResult"
        : page === "knowledge"
          ? "#faqResult"
          : page === "rpa"
            ? "#rpaResult"
            : "#answer";
  showJson(target, message);
}

async function api(path, options = {}) {
  const auth = getAuth();
  const headers = { "Content-Type": "application/json" };
  if (auth && auth.token) {
    headers["Authorization"] = `Bearer ${auth.token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : response.statusText);
  }
  return data;
}

function pill(value) {
  return `<span class="pill ${value || ""}">${value || "-"}</span>`;
}

function setSystemStatus(message) {
  const target = $("#systemStatus");
  if (target) target.textContent = message;
}

async function refreshSystemStatus() {
  try {
    const rag = await api("/ai/status");
    setSystemStatus(`后端已连接 | FAQ ${rag.faq_count} | ${rag.mode}`);
  } catch (error) {
    setSystemStatus(`后端未连接：${error.message}`);
  }
}

function ticketQueryString() {
  const params = new URLSearchParams();
  const status = $("#ticketStatus")?.value;
  const keyword = $("#ticketKeyword")?.value.trim();
  if (status) params.set("status", status);
  if (keyword) params.set("keyword", keyword);
  const query = params.toString();
  return query ? `?${query}` : "";
}

function userQueryString() {
  const params = new URLSearchParams();
  const keyword = $("#userKeyword")?.value.trim();
  const role = $("#userRoleFilter")?.value;
  const status = $("#userStatusFilter")?.value;
  if (keyword) params.set("keyword", keyword);
  if (role) params.set("role", role);
  if (status) params.set("status", status);
  const query = params.toString();
  return query ? `?${query}` : "";
}

async function initDashboard() {
  const [health, rag, users, tickets, faqs] = await Promise.all([
    api("/health"),
    api("/ai/status"),
    api("/users"),
    api("/tickets"),
    api("/admin/faqs"),
  ]);
  $("#dashboardHealth").textContent = `后端：${health.status}\n服务：${health.service}`;
  $("#dashboardRag").textContent = `模式：${rag.mode}\n知识条目：${rag.faq_count}\n向量库：${rag.vector_store}`;
  $("#dashboardCounts").textContent = `账号数：${users.length}\n工单数：${tickets.length}\nFAQ 数：${faqs.length}`;
}

function addChatMessage(text, isUser, meta) {
  const container = $("#chatMessages");
  if (!container) return;
  const div = document.createElement("div");
  div.className = `chat-msg ${isUser ? "user" : "bot"}`;
  div.innerHTML = `
    <div class="msg-avatar">${isUser ? "👤" : "🤖"}</div>
    <div class="msg-content">
      <div class="msg-text">${text}</div>
      ${meta ? `<div class="msg-meta">${meta}</div>` : ""}
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

async function sendChatMessage() {
  const input = $("#chatInput");
  const sendBtn = $("#chatSend");
  if (!input || !sendBtn) return;

  const message = input.value.trim();
  if (!message) return;

  // Show user message
  addChatMessage(escapeHtml(message), true);
  input.value = "";

  // Disable input
  input.disabled = true;
  sendBtn.disabled = true;
  sendBtn.textContent = "思考中...";

  // Show typing indicator
  const typingId = "typing-indicator";
  const container = $("#chatMessages");
  const typingDiv = document.createElement("div");
  typingDiv.className = "chat-msg bot";
  typingDiv.id = typingId;
  typingDiv.innerHTML = '<div class="msg-avatar">🤖</div><div class="msg-content"><div class="msg-text">正在思考...</div></div>';
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;

  try {
    const result = await api("/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });

    // Remove typing indicator
    const typing = $("#" + typingId);
    if (typing) typing.remove();

    let content = result.content || "暂无回复";
    let meta = "";

    if (result.intent === "knowledge") {
      meta = `知识库匹配度 ${(result.confidence * 100).toFixed(0)}%`;
    } else if (result.intent === "unknown") {
      meta = `📋 已创建工单 #${result.ticket_id}`;
    }

    addChatMessage(content, false, meta);
  } catch (error) {
    const typing = $("#" + typingId);
    if (typing) typing.remove();
    addChatMessage(`出错了：${error.message}`, false, "⚠️ 错误");
  } finally {
    input.disabled = false;
    sendBtn.disabled = false;
    sendBtn.textContent = "发送";
    input.focus();
  }
}

// ---- Self-service auth & my tickets ----

function initSelfServiceAuth() {
  const loginBtn = $("#selfLoginBtn");
  const logoutBtn = $("#selfLogoutBtn");
  const userSpan = $("#selfLoginUser");
  const modal = $("#selfLoginModal");
  const submitBtn = $("#selfLoginSubmit");

  // Show current auth state
  updateSelfServiceAuthUI();

  // Login button → show modal
  if (loginBtn) loginBtn.addEventListener("click", () => {
    if (modal) modal.classList.add("open");
  });

  // Logout button
  if (logoutBtn) logoutBtn.addEventListener("click", () => {
    clearAuth();
    updateSelfServiceAuthUI();
    $("#myTicketsSection").style.display = "none";
    $("#myTicketsTable").innerHTML = '<tr><td colspan="5" class="empty">登录后可查看您的工单</td></tr>';
  });

  // Submit login
  if (submitBtn) submitBtn.addEventListener("click", async () => {
    const username = $("#selfLoginUsername").value.trim();
    const password = $("#selfLoginPassword").value.trim();
    const errorEl = $("#selfLoginError");
    if (!username || !password) return;
    submitBtn.disabled = true;
    submitBtn.textContent = "登录中...";
    try {
      const r = await fetch(`${API_BASE}/users/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || "登录失败");
      setAuth(data);
      if (modal) modal.classList.remove("open");
      $("#selfLoginUsername").value = "";
      $("#selfLoginPassword").value = "";
      if (errorEl) errorEl.style.display = "none";
      updateSelfServiceAuthUI();
      await loadMyTickets();
    } catch (e) {
      if (errorEl) { errorEl.textContent = e.message; errorEl.style.display = ""; }
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "登 录";
    }
  });

  // Enter key in password field
  const pwField = $("#selfLoginPassword");
  if (pwField) pwField.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && submitBtn) submitBtn.click();
  });

  // Close modal on overlay click
  if (modal) modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });

  // Refresh tickets button
  const refreshBtn = $("#refreshMyTickets");
  if (refreshBtn) refreshBtn.addEventListener("click", loadMyTickets);

  // Show tickets section if logged in
  const auth = getAuth();
  if (auth && auth.token) {
    loadMyTickets();
  }
}

function updateSelfServiceAuthUI() {
  const auth = getAuth();
  const loginBtn = $("#selfLoginBtn");
  const logoutBtn = $("#selfLogoutBtn");
  const userSpan = $("#selfLoginUser");

  if (auth && auth.token) {
    if (loginBtn) loginBtn.style.display = "none";
    if (logoutBtn) logoutBtn.style.display = "";
    if (userSpan) { userSpan.style.display = ""; userSpan.textContent = `👤 ${auth.user?.username || "已登录"}`; }
  } else {
    if (loginBtn) loginBtn.style.display = "";
    if (logoutBtn) logoutBtn.style.display = "none";
    if (userSpan) userSpan.style.display = "none";
  }
}

async function loadMyTickets() {
  const auth = getAuth();
  if (!auth || !auth.token) return;

  const section = $("#myTicketsSection");
  const table = $("#myTicketsTable");
  if (!section || !table) return;

  section.style.display = "";
  try {
    const username = auth.user?.username || "anonymous";
    const tickets = await api(`/tickets?user=${encodeURIComponent(username)}`);
    const statusMap = { open: "待处理", in_progress: "处理中", resolved: "已解决", closed: "已关闭" };
    table.innerHTML = tickets.length
      ? tickets.map(t => `
        <tr>
          <td>${t.id}</td>
          <td>${escapeHtml(t.question).substring(0, 60)}${t.question.length > 60 ? '...' : ''}</td>
          <td>${statusMap[t.status] || t.status}</td>
          <td>${escapeHtml(t.answer || '-').substring(0, 40)}</td>
          <td>${t.created_at || '-'}</td>
        </tr>`).join("")
      : '<tr><td colspan="5" class="empty">暂无工单</td></tr>';
  } catch (e) {
    table.innerHTML = `<tr><td colspan="5" class="empty">加载失败：${e.message}</td></tr>`;
  }
}

async function loadTickets() {
  const tickets = await api(`/admin/tickets${ticketQueryString()}`);
  const table = $("#ticketsTable");
  if (!table) return tickets;
  table.innerHTML = tickets.length
    ? tickets.map(renderTicketRow).join("")
    : `<tr><td colspan="7" class="empty">暂无工单</td></tr>`;
  return tickets;
}

function renderTicketRow(ticket) {
  const selectedId = $("#resolveId").value.trim();
  const isSelected = selectedId && String(ticket.id) === selectedId;
  return `
    <tr class="${isSelected ? 'selected-row' : ''}">
      <td>${ticket.id}</td>
      <td>${escapeHtml(ticket.question)}<br /><small>${escapeHtml(ticket.answer || "待处理")}</small></td>
      <td>${escapeHtml(ticket.user)}<br /><small>${escapeHtml(ticket.contact || "-")}</small></td>
      <td>${escapeHtml(ticket.category)}<br />${pill(ticket.priority)}</td>
      <td>${pill(ticket.status)}</td>
      <td>${pill(ticket.callback_status)}<br /><small>${escapeHtml(ticket.callback_note || "-")}</small></td>
      <td>
        <button class="ghost ${isSelected ? 'active' : ''}" onclick="pickTicket(${ticket.id})">${isSelected ? '已选中' : '选择'}</button>
      </td>
    </tr>
  `;
}

async function selectTicket(id) {
  const currentId = $("#resolveId").value.trim();
  // Clicking the same ticket again -> deselect
  if (currentId && String(id) === currentId) {
    $("#resolveId").value = "";
    $("#resolveNote").value = "";
    $("#callbackNote").value = "";
    $("#ticketResult").textContent = "请选择或输入工单 ID。";
    await loadTickets();
    return;
  }

  const ticket = await api(`/tickets/${id}`);
  $("#resolveId").value = ticket.id;
  $("#resolveNote").value = ticket.answer || "已核验身份，按标准运维流程处理并完成回访。";
  $("#callbackNote").value = ticket.callback_note || "已电话回访，报障人确认问题解决。";
  showTicketData(ticket);
  await loadTickets();
}

async function createDemoTicket() {
  const result = await api("/tickets", {
    method: "POST",
    body: JSON.stringify({
      question: "堡垒机登录后看不到目标主机",
      user: "ops01",
      contact: "13300000002",
      category: "account",
      priority: "high",
    }),
  });
  showTicketData(result);
  $("#resolveId").value = result.id;
  await loadTickets();
}

async function resolveTicket() {
  const btn = $("#resolveTicket");
  const id = $("#resolveId").value.trim();
  if (!id) throw new Error("请先输入工单ID或者选择工单");

  const addToKb = $("#toggleKb").classList.contains("active");
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "正在提交...";

  try {
    const result = await api(`/admin/tickets/${id}/resolve`, {
      method: "PATCH",
      body: JSON.stringify({
        resolution_note: $("#resolveNote").value.trim(),
        resolver: $("#resolver").value.trim() || "admin",
        add_to_kb: addToKb,
        kb_answer: addToKb ? $("#kbAnswer").value.trim() : "",
        callback_status: "contacted",
        callback_note: $("#callbackNote").value.trim(),
      }),
    });
    showTicketData(result);
    await loadTickets();
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = originalText;
    }, 1000);
  }
}

async function markTicketInProgress() {
  const btn = $("#markInProgress");
  const id = $("#resolveId").value.trim();
  if (!id) throw new Error("请先输入工单ID或者选择工单");

  const isMarked = btn.classList.contains("active");
  const newStatus = isMarked ? "open" : "in_progress";

  btn.disabled = true;
  const originalText = btn.textContent;
  btn.textContent = "处理中...";

  try {
    const result = await api(`/tickets/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus, resolver: $("#resolver").value.trim() || "admin" }),
    });
    showTicketData(result);
    // Toggle button state
    btn.classList.toggle("active");
    btn.classList.toggle("ghost");
    await loadTickets();
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = isMarked ? "标记处理中" : "已标记";
    }, 1000);
  }
}

async function closeTicket() {
  const id = $("#resolveId").value.trim();
  if (!id) return;
  $("#closeTicketId").textContent = `#${id}`;
  $("#closeModal").classList.add("open");
}

function setupCloseModal() {
  // Cancel -> close modal
  $("#modalCancel").addEventListener("click", () => {
    $("#closeModal").classList.remove("open");
  });
  // Click overlay -> close modal
  $("#closeModal").addEventListener("click", (e) => {
    if (e.target === $("#closeModal")) {
      $("#closeModal").classList.remove("open");
    }
  });
  // Confirm -> close ticket
  $("#modalConfirm").addEventListener("click", async () => {
    const id = $("#resolveId").value.trim();
    if (!id) return;
    const btn = $("#modalConfirm");
    btn.disabled = true;
    btn.textContent = "关闭中...";
    try {
      const result = await api(`/tickets/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: "closed" }),
      });
      showTicketData(result);
      await loadTickets();
      $("#closeModal").classList.remove("open");
    } finally {
      btn.disabled = false;
      btn.textContent = "确定关闭";
    }
  });
}

function collectUserPayload(includePassword = true) {
  const payload = {
    username: $("#username").value.trim(),
    role: $("#role").value,
    full_name: $("#fullName").value.trim(),
    department: $("#department").value.trim(),
    phone: $("#phone").value.trim(),
    email: $("#email").value.trim(),
    status: $("#userStatus").value,
  };
  const password = $("#password").value.trim();
  if (includePassword || password) payload.password = password;
  return payload;
}

async function loadUsers() {
  const users = await api(`/users${userQueryString()}`);
  const table = $("#usersTable");
  if (!table) return users;
  table.innerHTML = users.length
    ? users.map(renderUserRow).join("")
    : `<tr><td colspan="6" class="empty">暂无账号</td></tr>`;
  return users;
}

function renderUserRow(user) {
  const statusAction =
    user.status === "active"
      ? `<button class="danger" onclick="toggleUserStatus(${user.id}, 'frozen')">冻结</button>`
      : `<button class="secondary" onclick="toggleUserStatus(${user.id}, 'active')">解冻</button>`;
  return `
    <tr>
      <td>${user.id}</td>
      <td>${escapeHtml(user.username)}<br /><small>${escapeHtml(user.email || "-")}</small></td>
      <td>${escapeHtml(user.full_name || "-")}<br /><small>${escapeHtml(user.department || "-")} | ${escapeHtml(user.phone || "-")}</small></td>
      <td>${pill(user.role)}</td>
      <td>${pill(user.status)}</td>
      <td>
        <div class="actions">
          <button class="ghost" onclick="editUserById(${user.id})">编辑</button>
          ${statusAction}
          <button class="danger" onclick="showUserDeleteModal(${user.id}, '${escapeHtml(user.username)}')">删除</button>
        </div>
      </td>
    </tr>
  `;
}

async function createUser() {
  const username = $("#username").value.trim();
  const password = $("#password").value.trim();
  if (!username || !password) {
    showJson("#userResult", { error: "用户名和密码不能为空" });
    return;
  }
  const result = await api("/users", {
    method: "POST",
    body: JSON.stringify(collectUserPayload(true)),
  });
  showJson("#userResult", result);
  await loadUsers();
}

async function updateUser() {
  const id = $("#userId").value.trim();
  if (!id) {
    showJson("#userResult", { error: "请先点击列表中的【编辑】按钮选择要修改的账号" });
    return;
  }
  const result = await api(`/users/${id}`, {
    method: "PUT",
    body: JSON.stringify(collectUserPayload(false)),
  });
  showJson("#userResult", result);
  await loadUsers();
}

async function editUser(id) {
  const user = await api(`/users/${id}`);
  $("#userId").value = user.id;
  $("#username").value = user.username;
  $("#password").value = "";
  $("#role").value = user.role;
  $("#fullName").value = user.full_name || "";
  $("#department").value = user.department || "";
  $("#phone").value = user.phone || "";
  $("#email").value = user.email || "";
  $("#userStatus").value = user.status;
  showJson("#userResult", user);
}

async function setUserStatus(id, status) {
  const result = await api(`/users/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  showJson("#userResult", result);
  await loadUsers();
}

async function removeUser(id) {
  if (!confirm(`确定删除账号 #${id} 吗？`)) return;
  await api(`/users/${id}`, { method: "DELETE" });
  showJson("#userResult", { deleted: id });
  await loadUsers();
}

function clearUserForm() {
  $("#userId").value = "";
  $("#username").value = "";
  $("#password").value = "";
  $("#role").value = "operator";
  $("#fullName").value = "";
  $("#department").value = "";
  $("#phone").value = "";
  $("#email").value = "";
  $("#userStatus").value = "active";
  showJson("#userResult", { info: "表单已清空" });
}

async function loadFaqs() {
  const faqs = await api("/admin/faqs");
  const table = $("#faqTable");
  if (!table) return faqs;
  table.innerHTML = faqs.length
    ? faqs.map(renderFaqRow).join("")
    : `<tr><td colspan="5" class="empty">暂无 FAQ</td></tr>`;
  return faqs;
}

function renderFaqRow(faq) {
  return `
    <tr>
      <td>${faq.id}</td>
      <td>${escapeHtml(faq.question)}</td>
      <td>${escapeHtml(faq.answer)}</td>
      <td>${faq.tags.map((tag) => pill(escapeHtml(tag))).join(" ")}</td>
      <td>
        <div class="actions">
          <button class="ghost" onclick="editFaqById(${faq.id})">编辑</button>
          <button class="danger" onclick="showFaqDeleteModal(${faq.id})">删除</button>
        </div>
      </td>
    </tr>
  `;
}

function collectFaqPayload() {
  return {
    question: $("#faqQuestion").value.trim(),
    answer: $("#faqAnswer").value.trim(),
    tags: $("#faqTags").value
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
  };
}

async function createFaq() {
  const result = await api("/admin/faqs", {
    method: "POST",
    body: JSON.stringify(collectFaqPayload()),
  });
  showJson("#faqResult", result);
  await Promise.all([loadFaqs(), refreshSystemStatus()]);
}

async function updateFaq() {
  const id = $("#faqId").value.trim();
  if (!id) throw new Error("请先点击列表中的编辑，或填写 FAQ ID");
  const result = await api(`/admin/faqs/${id}`, {
    method: "PATCH",
    body: JSON.stringify(collectFaqPayload()),
  });
  showJson("#faqResult", result);
  await Promise.all([loadFaqs(), refreshSystemStatus()]);
}

async function editFaq(id) {
  const faqs = await api("/admin/faqs");
  const faq = faqs.find((item) => item.id === id);
  if (!faq) throw new Error("FAQ 不存在");
  $("#faqId").value = faq.id;
  $("#faqQuestion").value = faq.question;
  $("#faqAnswer").value = faq.answer;
  $("#faqTags").value = faq.tags.join(",");
  showJson("#faqResult", faq);
}

async function removeFaq(id) {
  if (!confirm(`确定删除 FAQ #${id} 吗？`)) return;
  await api(`/admin/faqs/${id}`, { method: "DELETE" });
  showJson("#faqResult", { deleted: id });
  await Promise.all([loadFaqs(), refreshSystemStatus()]);
}

function clearFaqForm() {
  $("#faqId").value = "";
  $("#faqQuestion").value = "堡垒机无法登录怎么处理？";
  $("#faqAnswer").value = "检查账号状态、MFA 绑定状态和客户端网络连通性，必要时转二线处理。";
  $("#faqTags").value = "堡垒机,账号,网络";
}

async function resetPassword() {
  const result = await api("/reset-password", {
    method: "POST",
    body: JSON.stringify({
      username: $("#resetUsername").value.trim(),
      new_password: $("#resetPasswordValue").value.trim(),
      requested_by: "admin",
    }),
  });
  showJson("#rpaResult", result);
  await loadRpaHistory();
}

async function createAccountRpa() {
  const username = $("#rpaCreateUsername").value.trim();
  const result = await api("/create-account", {
    method: "POST",
    body: JSON.stringify({
      username,
      password: $("#rpaCreatePassword").value.trim(),
      role: "operator",
      full_name: $("#rpaCreateName").value.trim(),
      department: $("#rpaCreateDepartment").value.trim(),
      phone: "13300000005",
      email: `${username}@example.com`,
      requested_by: "admin",
    }),
  });
  showJson("#rpaResult", result);
  await loadRpaHistory();
}

async function freezeAccountRpa() {
  const result = await api("/freeze-account", {
    method: "POST",
    body: JSON.stringify({
      username: $("#freezeUsername").value.trim(),
      requested_by: "admin",
      reason: $("#freezeReason").value.trim(),
    }),
  });
  showJson("#rpaResult", result);
  await loadRpaHistory();
}

async function unfreezeAccountRpa() {
  const result = await api("/unfreeze-account", {
    method: "POST",
    body: JSON.stringify({
      username: $("#unfreezeUsername").value.trim(),
      requested_by: "admin",
      reason: $("#unfreezeReason").value.trim(),
    }),
  });
  showJson("#rpaResult", result);
  await loadRpaHistory();
}

async function aiRpaExecute() {
  const btn = $("#aiRpaExecute");
  const resultEl = $("#rpaResult");
  if (!btn || !resultEl) return;

  const command = $("#aiRpaCommand").value.trim();
  if (!command) return;

  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "AI 分析中...";
  resultEl.textContent = "AI 正在分析指令...";

  try {
    const result = await api("/ai/rpa", {
      method: "POST",
      body: JSON.stringify({ command }),
    });

    const lines = [`操作：${result.action}`, `状态：${result.success ? "✅ 成功" : "❌ 失败"}`, `结果：${result.message}`];
    if (result.steps && result.steps.length) {
      lines.push("");
      lines.push("执行步骤：");
      result.steps.forEach((s, i) => lines.push(`  ${i + 1}. ${s}`));
    }
    resultEl.textContent = lines.join("\n");
    await loadRpaHistory();
  } catch (error) {
    resultEl.textContent = `执行失败：${error.message}`;
  } finally {
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = originalText;
    }, 1500);
  }
}

async function loadRpaHistory() {
  const table = $("#rpaHistoryTable");
  if (!table) return;
  try {
    const jobs = await api("/rpa-jobs");
    table.innerHTML = jobs.length
      ? jobs.map((j) => {
          const actionMap = {
            "reset-password": "重置密码",
            "create-account": "创建账号",
            "freeze-account": "冻结账号",
            "unfreeze-account": "解冻账号",
          };
          return `<tr>
            <td><small>${escapeHtml(j.created_at)}</small></td>
            <td>${escapeHtml(actionMap[j.action] || j.action)}</td>
            <td>${pill(j.status)}</td>
            <td><small>${escapeHtml(j.result)}</small></td>
          </tr>`;
        }).join("")
      : '<tr><td colspan="4" class="empty">暂无执行记录</td></tr>';
  } catch {
    // silently ignore
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

async function initPage() {
  const page = document.body.dataset.page;

  // Require login for all admin pages (except self-service which is public)
  const adminPages = ["dashboard", "tickets", "users", "knowledge", "rpa"];
  if (adminPages.includes(page)) {
    // Bind login/logout
    const loginBtn = $("#loginBtn");
    const logoutBtn = $("#logoutBtn");
    if (loginBtn) loginBtn.addEventListener("click", doLogin);
    if (logoutBtn) logoutBtn.addEventListener("click", doLogout);
    // Allow Enter key to submit login
    const pwField = $("#loginPassword");
    if (pwField) pwField.addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });
    // Check auth
    if (!requireAuth()) return;
  }

  await refreshSystemStatus();

  if (page === "dashboard") {
    await initDashboard();
  }

  if (page === "self-service") {
    // Chat: send on button click or Enter key
    $("#chatSend").addEventListener("click", sendChatMessage);
    $("#chatInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });

    // Self-service login
    initSelfServiceAuth();
  }

  if (page === "tickets") {
    bind("#loadTickets", "click", loadTickets);
    bind("#newTicketDemo", "click", createDemoTicket);
    bind("#resolveTicket", "click", resolveTicket);
    bind("#markInProgress", "click", markTicketInProgress);
    $("#toggleKb").addEventListener("click", () => {
      $("#toggleKb").classList.toggle("active");
    });
    $("#closeTicketBtn").addEventListener("click", closeTicket);
    setupCloseModal();
    await loadTickets();
  }

  if (page === "users") {
    bind("#loadUsers", "click", loadUsers);
    bind("#createUser", "click", createUser);
    bind("#updateUser", "click", updateUser);
    bind("#clearUserForm", "click", async () => clearUserForm());

    // User delete modal
    $("#userDeleteCancel").addEventListener("click", () => {
      $("#userDeleteModal").classList.remove("open");
    });
    $("#userDeleteModal").addEventListener("click", (e) => {
      if (e.target === $("#userDeleteModal")) {
        $("#userDeleteModal").classList.remove("open");
      }
    });
    $("#userDeleteConfirm").addEventListener("click", async () => {
      const id = window._userDeleteId;
      if (!id) return;
      await api(`/users/${id}`, { method: "DELETE" });
      $("#userDeleteModal").classList.remove("open");
      window._userDeleteId = null;
      showJson("#userResult", { deleted: id });
      await loadUsers();
    });

    await loadUsers();
  }

  if (page === "knowledge") {
    bind("#loadFaqs", "click", loadFaqs);
    bind("#createFaq", "click", createFaq);
    bind("#updateFaq", "click", updateFaq);
    bind("#clearFaqForm", "click", async () => clearFaqForm());

    // FAQ delete modal
    $("#faqDeleteCancel").addEventListener("click", () => {
      $("#faqDeleteModal").classList.remove("open");
    });
    $("#faqDeleteModal").addEventListener("click", (e) => {
      if (e.target === $("#faqDeleteModal")) {
        $("#faqDeleteModal").classList.remove("open");
      }
    });
    $("#faqDeleteConfirm").addEventListener("click", async () => {
      const id = window._faqDeleteId;
      if (!id) return;
      await api(`/admin/faqs/${id}`, { method: "DELETE" });
      $("#faqDeleteModal").classList.remove("open");
      window._faqDeleteId = null;
      await Promise.all([loadFaqs(), refreshSystemStatus()]);
    });

    await loadFaqs();
  }

  if (page === "rpa") {
    bind("#aiRpaExecute", "click", aiRpaExecute);
    await loadRpaHistory();
  }
}

window.pickTicket = (id) => selectTicket(id).catch(showError);
window.editUserById = (id) => editUser(id).catch(showError);
window.toggleUserStatus = (id, status) => setUserStatus(id, status).catch(showError);
window.showUserDeleteModal = (id, name) => {
  $("#userDeleteName").textContent = `${name} (#${id})`;
  $("#userDeleteModal").classList.add("open");
  window._userDeleteId = id;
};
window.editFaqById = (id) => editFaq(id).catch(showError);
window.showFaqDeleteModal = (id) => {
  $("#faqDeleteId").textContent = `#${id}`;
  $("#faqDeleteModal").classList.add("open");
  window._faqDeleteId = id;
};

initPage().catch(showError);

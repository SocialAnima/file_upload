(function () {
    const { basePath, maxUploadMb } = window.APP_CONFIG;

    const adminToggleBtn = document.getElementById("adminToggleBtn");
    const adminPanel = document.getElementById("adminPanel");
    const logoutBtn = document.getElementById("logoutBtn");
    const loginModal = document.getElementById("loginModal");
    const loginForm = document.getElementById("loginForm");
    const loginPassword = document.getElementById("loginPassword");
    const loginError = document.getElementById("loginError");
    const cancelLoginBtn = document.getElementById("cancelLoginBtn");
    const loginBackdrop = document.getElementById("loginBackdrop");
    const uploadZone = document.getElementById("uploadZone");
    const fileInput = document.getElementById("fileInput");
    const selectFileBtn = document.getElementById("selectFileBtn");
    const uploadStatus = document.getElementById("uploadStatus");
    const changePasswordForm = document.getElementById("changePasswordForm");
    const passwordStatus = document.getElementById("passwordStatus");
    const fileTableBody = document.getElementById("fileTableBody");
    const fileCount = document.getElementById("fileCount");
    const emptyState = document.getElementById("emptyState");

    let isAdmin = false;

    function apiUrl(path) {
        return `${basePath}${path}`;
    }

    function formatSize(bytes) {
        const size = Number(bytes);
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(2)} MB`;
    }

    function formatTime(isoString) {
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) return isoString;
        return date.toLocaleString("zh-CN");
    }

    function showMessage(element, message, type) {
        element.textContent = message;
        element.classList.remove("hidden", "success", "error");
        element.classList.add(type === "error" ? "error" : "success");
    }

    function hideMessage(element) {
        element.classList.add("hidden");
        element.textContent = "";
    }

    function setAdminMode(enabled) {
        isAdmin = enabled;
        adminPanel.classList.toggle("hidden", !enabled);
        document.querySelectorAll(".delete-btn").forEach((btn) => {
            btn.classList.toggle("hidden", !enabled);
        });
        adminToggleBtn.textContent = enabled ? "管理中" : "管理";
    }

    async function request(path, options = {}) {
        const response = await fetch(apiUrl(path), {
            headers: {
                "Accept": "application/json",
                ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
                ...(options.headers || {}),
            },
            ...options,
        });

        let data = {};
        try {
            data = await response.json();
        } catch (_error) {
            data = {};
        }

        if (!response.ok) {
            throw new Error(data.error || "请求失败");
        }
        return data;
    }

    function renderFiles(files) {
        if (fileCount) {
            fileCount.textContent = `${files.length} 个文件`;
        }

        if (!fileTableBody) {
            if (files.length === 0 && emptyState) {
                emptyState.classList.remove("hidden");
            }
            return;
        }

        fileTableBody.innerHTML = "";

        if (files.length === 0) {
            if (emptyState) emptyState.classList.remove("hidden");
            return;
        }

        if (emptyState) emptyState.classList.add("hidden");

        files.forEach((file) => {
            const row = document.createElement("tr");
            row.dataset.id = file.id;
            row.innerHTML = `
                <td class="file-name">${escapeHtml(file.original_name)}</td>
                <td class="file-size">${formatSize(file.size)}</td>
                <td class="file-time">${formatTime(file.uploaded_at)}</td>
                <td class="actions">
                    <a class="btn btn-link" href="${apiUrl(`/download/${file.id}`)}">下载</a>
                    <button class="btn btn-danger delete-btn ${isAdmin ? "" : "hidden"}" type="button" data-id="${file.id}">删除</button>
                </td>
            `;
            fileTableBody.appendChild(row);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatExistingRows() {
        document.querySelectorAll(".file-size[data-size]").forEach((cell) => {
            cell.textContent = formatSize(cell.dataset.size);
        });
        document.querySelectorAll(".file-time").forEach((cell) => {
            cell.textContent = formatTime(cell.textContent);
        });
    }

    async function refreshFiles() {
        if (!isAdmin) return;
        const data = await request("/api/admin/files");
        renderFiles(data.files || []);
    }

    function openLoginModal() {
        loginModal.classList.remove("hidden");
        loginPassword.value = "";
        hideMessage(loginError);
        loginPassword.focus();
    }

    function closeLoginModal() {
        loginModal.classList.add("hidden");
    }

    async function checkAdminStatus() {
        try {
            const data = await request("/api/admin/status");
            setAdminMode(Boolean(data.logged_in));
        } catch (_error) {
            setAdminMode(false);
        }
    }

    adminToggleBtn.addEventListener("click", () => {
        if (isAdmin) {
            adminPanel.classList.toggle("hidden");
            return;
        }
        openLoginModal();
    });

    cancelLoginBtn.addEventListener("click", closeLoginModal);
    loginBackdrop.addEventListener("click", closeLoginModal);

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        hideMessage(loginError);
        try {
            await request("/api/admin/login", {
                method: "POST",
                body: JSON.stringify({ password: loginPassword.value }),
            });
            closeLoginModal();
            setAdminMode(true);
            await refreshFiles();
        } catch (error) {
            showMessage(loginError, error.message, "error");
        }
    });

    logoutBtn.addEventListener("click", async () => {
        try {
            await request("/api/admin/logout", { method: "POST" });
        } finally {
            setAdminMode(false);
        }
    });

    selectFileBtn.addEventListener("click", () => fileInput.click());

    uploadZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadZone.classList.add("dragover");
    });

    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("dragover");
    });

    uploadZone.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadZone.classList.remove("dragover");
        if (event.dataTransfer.files.length > 0) {
            uploadFile(event.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            uploadFile(fileInput.files[0]);
            fileInput.value = "";
        }
    });

    async function uploadFile(file) {
        hideMessage(uploadStatus);
        const maxBytes = maxUploadMb * 1024 * 1024;
        if (file.size > maxBytes) {
            showMessage(uploadStatus, `文件超过 ${maxUploadMb}MB 限制`, "error");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            showMessage(uploadStatus, "正在上传...", "success");
            await request("/api/admin/upload", {
                method: "POST",
                body: formData,
            });
            showMessage(uploadStatus, "上传成功", "success");
            await refreshFiles();
        } catch (error) {
            showMessage(uploadStatus, error.message, "error");
        }
    }

    document.addEventListener("click", async (event) => {
        const button = event.target.closest(".delete-btn");
        if (!button) return;

        const fileId = button.dataset.id;
        if (!fileId) return;
        if (!confirm("确定删除该文件吗？")) return;

        try {
            await request(`/api/admin/files/${fileId}`, { method: "DELETE" });
            await refreshFiles();
        } catch (error) {
            alert(error.message);
        }
    });

    changePasswordForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        hideMessage(passwordStatus);
        const oldPassword = document.getElementById("oldPassword").value;
        const newPassword = document.getElementById("newPassword").value;

        try {
            const data = await request("/api/admin/change-password", {
                method: "POST",
                body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
            });
            showMessage(passwordStatus, data.message, "success");
            changePasswordForm.reset();
        } catch (error) {
            showMessage(passwordStatus, error.message, "error");
        }
    });

    formatExistingRows();
    checkAdminStatus();
})();

/* API Access Manager — Client-side JS */

// --- API Helpers ---
async function api(url, data = null) {
    const opts = data ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    } : {};
    const res = await fetch(url, opts);
    return res.json();
}

function showToast(message) {
    const toast = document.getElementById("toast");
    if (toast) {
        toast.textContent = message;
        toast.style.display = "block";
        setTimeout(() => toast.style.display = "none", 3000);
    }
}

// --- Step Toggle ---
async function toggleStep(stepId, checkbox) {
    const completed = !checkbox.classList.contains("checked");
    await api(`/api/step/${stepId}/toggle`, { completed });

    if (completed) {
        checkbox.classList.add("checked");
        checkbox.closest(".step-item").classList.add("completed");
    } else {
        checkbox.classList.remove("checked");
        checkbox.closest(".step-item").classList.remove("completed");
    }

    // Update progress bar
    updateProgress();
    showToast(completed ? "Step completed!" : "Step unchecked");
}

function updateProgress() {
    const steps = document.querySelectorAll(".step-item");
    const completed = document.querySelectorAll(".step-item.completed");
    const total = steps.length;
    const done = completed.length;
    const pct = total ? Math.round((done / total) * 100) : 0;

    const bar = document.querySelector(".progress-bar-large .fill");
    const text = document.querySelector(".progress-pct");
    const count = document.querySelector(".progress-count");

    if (bar) bar.style.width = pct + "%";
    if (text) text.textContent = pct + "%";
    if (count) count.textContent = `${done}/${total} steps`;
}

// --- Status Change ---
async function changeStatus(platformId, newStatus) {
    await api(`/api/platform/${platformId}/status`, { status: newStatus });
    showToast(`Status updated to ${newStatus.replace("_", " ")}`);
    setTimeout(() => location.reload(), 500);
}

// --- Platform Update ---
async function updatePlatform(platformId, field, value) {
    await api(`/api/platform/${platformId}/update`, { [field]: value });
    showToast(`${field} updated`);
}

// --- Key Management ---
async function addKey(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        platform_id: parseInt(form.platform_id.value),
        key_name: form.key_name.value,
        key_type: form.key_type.value,
        env_var_name: form.env_var_name.value,
        rotation_days: parseInt(form.rotation_days.value) || 90,
        notes: form.notes.value,
    };
    await api("/api/keys", data);
    showToast("API key added!");
    closeModal("addKeyModal");
    setTimeout(() => location.reload(), 500);
}

async function rotateKey(keyId) {
    if (!confirm("Mark this key as rotated? This resets the countdown timer.")) return;
    await api(`/api/keys/${keyId}/rotate`);
    showToast("Key rotated — countdown reset!");
    setTimeout(() => location.reload(), 500);
}

async function deleteKeyConfirm(keyId) {
    if (!confirm("Remove this key from tracking? This does NOT delete the actual API key.")) return;
    await api(`/api/keys/${keyId}/delete`);
    showToast("Key removed from tracking");
    setTimeout(() => location.reload(), 500);
}

// --- Reminders ---
async function addReminder(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        platform_id: parseInt(form.platform_id.value),
        reminder_type: form.reminder_type.value,
        title: form.title.value,
        description: form.description.value,
        due_date: form.due_date.value,
    };
    const result = await api("/api/reminders", data);
    showToast(result.message || "Reminder created!");
    closeModal("addReminderModal");
    setTimeout(() => location.reload(), 500);
}

async function completeReminder(reminderId) {
    await api(`/api/reminders/${reminderId}/complete`);
    showToast("Reminder completed!");
    setTimeout(() => location.reload(), 500);
}

// --- Quick Add Reminder from Guide ---
function quickAddReminder(platformId, platformName, type) {
    const titles = {
        "follow_up": `Follow up on ${platformName} API application`,
        "rotation": `Rotate ${platformName} API keys`,
        "review": `Review ${platformName} API usage/compliance`,
    };

    const defaults = {
        "follow_up": 3,
        "rotation": 7,
        "review": 30,
    };

    const dueDate = new Date();
    dueDate.setDate(dueDate.getDate() + (defaults[type] || 7));

    // Fill in the reminder modal
    const modal = document.getElementById("addReminderModal");
    if (modal) {
        modal.querySelector("[name=platform_id]").value = platformId;
        modal.querySelector("[name=reminder_type]").value = type;
        modal.querySelector("[name=title]").value = titles[type] || "";
        modal.querySelector("[name=due_date]").value = dueDate.toISOString().split("T")[0];
        openModal("addReminderModal");
    }
}

// --- Modal ---
function openModal(id) {
    document.getElementById(id)?.classList.add("active");
}

function closeModal(id) {
    document.getElementById(id)?.classList.remove("active");
}

// Close modal on overlay click
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.classList.remove("active");
    }
});

// Close modal on Escape
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal-overlay.active").forEach(m => m.classList.remove("active"));
    }
});

// --- Tabs ---
function switchTab(tabName) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(t => t.style.display = "none");

    document.querySelector(`.tab[data-tab="${tabName}"]`)?.classList.add("active");
    document.getElementById(`tab-${tabName}`)?.style.removeProperty("display");
}

// --- Key countdown live updates ---
function updateCountdowns() {
    document.querySelectorAll("[data-expires]").forEach(el => {
        const expires = new Date(el.dataset.expires);
        const issued = new Date(el.dataset.issued || el.dataset.expires);
        const now = new Date();
        const totalDays = Math.max((expires - issued) / 86400000, 1);
        const remaining = Math.max(Math.ceil((expires - now) / 86400000), 0);
        const pct = Math.min((remaining / totalDays) * 100, 100);

        const bar = el.querySelector(".fill");
        const text = el.querySelector(".countdown-text");

        let cls = "healthy";
        if (remaining <= 7) cls = "critical";
        else if (remaining <= 30) cls = "warning";

        if (bar) {
            bar.style.width = pct + "%";
            bar.className = `fill ${cls}`;
        }
        if (text) {
            text.className = `countdown-text ${cls}`;
            if (remaining === 0) text.textContent = "EXPIRED";
            else if (remaining === 1) text.textContent = "1 day left";
            else text.textContent = `${remaining} days left`;
        }
    });
}

// --- Seed platforms ---
async function seedPlatforms() {
    await api("/api/seed");
    showToast("All platforms seeded!");
    setTimeout(() => location.reload(), 500);
}

// --- Add key from guide suggestion ---
function addKeyFromGuide(platformId, keyName, keyType, envVar, rotationDays) {
    const modal = document.getElementById("addKeyModal");
    if (modal) {
        modal.querySelector("[name=platform_id]").value = platformId;
        modal.querySelector("[name=key_name]").value = keyName;
        modal.querySelector("[name=key_type]").value = keyType;
        modal.querySelector("[name=env_var_name]").value = envVar;
        modal.querySelector("[name=rotation_days]").value = rotationDays;
        openModal("addKeyModal");
    }
}

// --- Init ---
document.addEventListener("DOMContentLoaded", () => {
    updateCountdowns();
    // Update countdowns every minute
    setInterval(updateCountdowns, 60000);
});

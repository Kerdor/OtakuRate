async function sendJson(url, method, body) {
    const response = await fetch(url, {method, headers: {"Content-Type": "application/json"}, body: body === undefined ? undefined : JSON.stringify(body)});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Не удалось сохранить данные.");
    return data;
}
const favoritesForm = document.querySelector("#favorites-form");
favoritesForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.querySelector("#favorites-message");
    try {
        const raw = document.querySelector("#favorite-ids").value.trim();
        const ids = raw ? raw.split(",").map(value => Number(value.trim())) : [];
        if (ids.some(value => !Number.isInteger(value) || value < 1)) throw new Error("Введи корректные ID через запятую.");
        await sendJson("/profile/favorites", "PUT", ids);
        message.textContent = "Любимые тайтлы сохранены. Обнови страницу, чтобы увидеть изменения.";
    } catch (error) { message.textContent = error.message; }
});
document.querySelector("#profile-settings-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = document.querySelector("#settings-message");
    try {
        await sendJson("/profile/settings", "PUT", {
            display_name: document.querySelector("#display-name").value,
            profile_visibility: document.querySelector("#profile-visibility").value,
            library_visibility: document.querySelector("#library-visibility").value,
            ratings_visibility: document.querySelector("#ratings-visibility").value
        });
        message.textContent = "Настройки сохранены.";
    } catch (error) { message.textContent = error.message; }
});
const settings = window.PROFILE_RATING_SETTINGS || {};
function renderCriteria() {
    const type = document.querySelector("#rating-media").value;
    const criteria = (settings[type] || {}).criteria || {};
    const container = document.querySelector("#rating-criteria");
    container.replaceChildren();
    Object.entries(criteria).forEach(([key, value]) => {
        const row = document.createElement("div");
        row.className = "rating-setting-row";
        const label = document.createElement("label");
        label.textContent = value.name;
        const weight = document.createElement("input");
        weight.type = "number"; weight.min = "0.1"; weight.max = "100"; weight.step = "0.1";
        weight.value = value.weight; weight.dataset.key = key; weight.dataset.field = "weight";
        const enabledLabel = document.createElement("label");
        const enabled = document.createElement("input");
        enabled.type = "checkbox"; enabled.checked = value.enabled; enabled.dataset.key = key; enabled.dataset.field = "enabled";
        enabledLabel.append(enabled, document.createTextNode(" Учитывать"));
        row.append(label, weight, enabledLabel); container.append(row);
    });
}
document.querySelector("#rating-media").addEventListener("change", renderCriteria);
document.querySelector("#save-rating-settings").addEventListener("click", async () => {
    const message = document.querySelector("#rating-message");
    const type = document.querySelector("#rating-media").value;
    const criteria = {};
    document.querySelectorAll("#rating-criteria [data-key]").forEach(input => {
        const key = input.dataset.key;
        criteria[key] ||= {weight: 1, enabled: true};
        if (input.dataset.field === "weight") criteria[key].weight = Number(input.value);
        else criteria[key].enabled = input.checked;
    });
    try {
        const result = await sendJson("/profile/rating-settings", "PUT", {media_type: type, criteria});
        message.textContent = "Создана версия профиля " + result.version + ".";
        settings[type].version = result.version;
        Object.entries(criteria).forEach(([key, value]) => { settings[type].criteria[key].weight = value.weight; settings[type].criteria[key].enabled = value.enabled; });
    } catch (error) { message.textContent = error.message; }
});
document.querySelector("#logout-link").addEventListener("click", async (event) => {
    event.preventDefault();
    try { await sendJson("/auth/logout", "POST", {}); window.location.href = "/"; }
    catch (error) { window.location.href = "/"; }
});
renderCriteria();

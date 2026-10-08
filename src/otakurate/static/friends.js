async function request(url, method="GET") {
    const response = await fetch(url, {method, headers: {"Content-Type": "application/json"}});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Ошибка запроса");
    return data;
}
const message = document.querySelector("#social-message");
const searchButton = document.querySelector("#user-search-button");
if (searchButton) searchButton.addEventListener("click", async () => {
    const root = document.querySelector("#user-search-results");
    root.replaceChildren();
    try {
        const users = await request("/users/search?query=" + encodeURIComponent(document.querySelector("#user-search").value));
        users.forEach(user => {
            const row = document.createElement("div"); row.className = "social-row";
            const link = document.createElement("a"); link.href = "/users/" + user.id; link.textContent = "@" + user.username;
            const button = document.createElement("button"); button.textContent = "Добавить";
            button.addEventListener("click", async () => { try { await request("/friends/requests/" + user.id, "POST"); message.textContent = "Запрос отправлен."; } catch (error) { message.textContent = error.message; } });
            row.append(link, button); root.append(row);
        });
        if (!users.length) root.textContent = "Пользователи не найдены.";
    } catch (error) { message.textContent = error.message; }
});
document.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;
    try {
        if (button.dataset.action === "accept") await request("/friends/requests/" + button.dataset.id + "/accept", "POST");
        else if (button.dataset.action === "reject") await request("/friends/requests/" + button.dataset.id + "/reject", "POST");
        else if (button.dataset.action === "remove") await request("/friends/" + button.dataset.id, "DELETE");
        location.reload();
    } catch (error) { message.textContent = error.message; }
});

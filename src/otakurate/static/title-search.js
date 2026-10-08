const form = document.getElementById("title-search-form");
const input = document.getElementById("title-search-input");
const results = document.getElementById("title-search-results");

let timer;

async function searchTitles() {
    const query = input.value.trim();
    if (!query) {
        results.innerHTML = "";
        return;
    }

    results.innerHTML = '<p class="muted">Поиск…</p>';

    try {
        const response = await fetch("/titles/search?query=" + encodeURIComponent(query));
        if (!response.ok) {
            throw new Error("Search failed");
        }

        const titles = await response.json();
        if (!titles.length) {
            results.innerHTML = '<p class="muted">Ничего не найдено.</p>';
            return;
        }

        results.innerHTML = titles.map((title) => (
            '<a class="search-result" href="/title/' + title.id + '">
            '
            + '<strong>' + escapeHtml(title.title) + '</strong>'
            + '<span>' + (title.media_type === "anime" ? "Аниме" : "Манга") + '</span>'
            + '</a>'
        )).join("");
    } catch {
        results.innerHTML = '<p class="muted">Не удалось выполнить поиск.</p>';
    }
}

function escapeHtml(value) {
    return value.replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    })[char]);
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    searchTitles();
});

input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(searchTitles, 200);
});

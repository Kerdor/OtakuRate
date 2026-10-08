const data = window.TITLE_DATA;
const list = document.querySelector('#library-list');
const button = document.querySelector('#library-add-button');
const status = document.querySelector('#library-status');

async function loadLists() {
    const params = new URLSearchParams({
        user_id: data.user_id,
        media_type: data.media_type,
    });
    const response = await fetch(`/lists?${params}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Не удалось загрузить списки');

    list.innerHTML = '';
    result.forEach((item) => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        list.appendChild(option);
    });
    if (!result.length) {
        button.disabled = true;
        status.textContent = 'У пользователя пока нет списков.';
    }
}

button.addEventListener('click', async () => {
    if (!list.value) return;
    button.disabled = true;
    status.textContent = 'Добавление...';
    try {
        const response = await fetch('/library', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: Number(data.user_id),
                title_id: data.id,
                list_id: Number(list.value),
            }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Не удалось добавить тайтл');
        status.textContent = 'Добавлено в библиотеку.';
    } catch (error) {
        status.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});

loadLists().catch((error) => {
    status.textContent = error.message;
});

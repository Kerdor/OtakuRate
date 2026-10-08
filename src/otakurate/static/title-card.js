const data = window.TITLE_DATA;
const list = document.querySelector('#library-list');
const button = document.querySelector('#library-add-button');
const status = document.querySelector('#library-status');
const currentInput = document.querySelector('#library-progress-current');
const totalInput = document.querySelector('#library-progress-total');

async function loadLibrary() {
    const params = new URLSearchParams({user_id: data.user_id, title_id: data.id});
    const [listsResponse, entryResponse] = await Promise.all([
        fetch(`/lists?user_id=${encodeURIComponent(data.user_id)}&media_type=${encodeURIComponent(data.media_type)}`),
        fetch(`/library/entry?${params}`),
    ]);

    const lists = await listsResponse.json();
    if (!listsResponse.ok) throw new Error(lists.detail || 'Не удалось загрузить списки');

    list.innerHTML = '';
    lists.forEach((item) => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        list.appendChild(option);
    });

    if (entryResponse.ok) {
        const entry = await entryResponse.json();
        list.value = String(entry.list_id);
        currentInput.value = entry.progress_current ?? '';
        totalInput.value = entry.progress_total ?? '';
        button.textContent = 'Сохранить изменения';
    } else {
        button.textContent = 'Добавить в список';
    }

    if (!lists.length) {
        button.disabled = true;
        status.textContent = 'У пользователя пока нет списков.';
    }
}

button.addEventListener('click', async () => {
    if (!list.value) return;
    button.disabled = true;
    status.textContent = 'Сохранение...';

    try {
        const payload = {
            user_id: Number(data.user_id),
            title_id: data.id,
            list_id: Number(list.value),
            progress_current: currentInput.value === '' ? null : Number(currentInput.value),
            progress_total: totalInput.value === '' ? null : Number(totalInput.value),
        };

        let response = await fetch('/library', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            response = await fetch('/library/entry', {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
        }

        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Не удалось сохранить библиотеку');
        status.textContent = 'Библиотека сохранена.';
    } catch (error) {
        status.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});

loadLibrary().catch((error) => {
    status.textContent = error.message;
});

const form = document.querySelector('#new-title-form');
const status = document.querySelector('#new-title-status');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const title = document.querySelector('#new-title-name').value.trim();
    const mediaType = document.querySelector('input[name="media-type"]:checked').value;

    status.textContent = 'Создание...';

    try {
        const response = await fetch('/titles', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title, media_type: mediaType}),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Не удалось создать тайтл');

        const userId = new URLSearchParams(window.location.search).get('user_id');
        const suffix = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
        window.location.href = `/title/${result.id}${suffix}`;
    } catch (error) {
        status.textContent = error.message;
    }
});

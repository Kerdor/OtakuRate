const data = window.RATING_DATA;
const list = document.querySelector('#criteria-list');
const overall = document.querySelector('#overall-rating');
const saveDraft = document.querySelector('#save-draft');
const saveStatus = document.querySelector('#save-status');
const params = new URLSearchParams(window.location.search);
const userId = params.get('user_id');
const titleId = params.get('title_id');

document.querySelector('#title').textContent = data.title;
document.querySelector('#media-type').textContent = data.media_type === 'anime' ? 'АНИМЕ' : 'МАНГА / МАНХВА';

const values = Object.fromEntries(Object.keys(data.criteria).map((key) => [key, 5]));

function calculateOverall() {
    let total = 0;
    let weights = 0;
    for (const [key, criterion] of Object.entries(data.criteria)) {
        if (!document.querySelector(`#criterion-${key}`).checked) continue;
        total += values[key] * criterion.weight;
        weights += criterion.weight;
    }
    overall.textContent = weights ? Math.round(total / weights) : '—';
}

function render() {
    list.innerHTML = '';
    for (const [key, criterion] of Object.entries(data.criteria)) {
        const card = document.createElement('article');
        card.className = 'criterion-card';
        card.innerHTML = `
            <div class="criterion-top">
                <div><h2>${criterion.name}</h2><p>${criterion.description}</p></div>
                <strong class="criterion-value" id="value-${key}">5</strong>
            </div>
            <input id="criterion-${key}" type="checkbox" checked hidden>
            <input class="rating-slider" data-key="${key}" type="range" min="1" max="10" step="1" value="5" aria-label="${criterion.name}">
            <div class="slider-scale"><span>1</span><span>10</span></div>
            <p class="score-description" id="score-${key}">${criterion.scores[4]}</p>
            <div class="criterion-meta">Вес: ${criterion.weight.toFixed(1)} · Влияние: <span id="impact-${key}">0.0</span></div>
        `;
        list.appendChild(card);
    }
    list.querySelectorAll('.rating-slider').forEach((slider) => {
        slider.addEventListener('input', () => {
            const key = slider.dataset.key;
            const value = Number(slider.value);
            values[key] = value;
            document.querySelector(`#value-${key}`).textContent = value;
            document.querySelector(`#score-${key}`).textContent = data.criteria[key].scores[value - 1];
            calculateImpact(key);
            calculateOverall();
            saveStatus.textContent = 'Есть несохранённые изменения';
        });
    });
}

function calculateImpact(changedKey) {
    const enabled = Object.keys(data.criteria);
    const totalWeight = enabled.reduce((sum, key) => sum + data.criteria[key].weight, 0);
    const impact = (values[changedKey] * data.criteria[changedKey].weight) / totalWeight;
    document.querySelector(`#impact-${changedKey}`).textContent = impact.toFixed(1);
}

saveDraft.addEventListener('click', async () => {
    if (!userId || !titleId) {
        localStorage.setItem(`otakurate-rating-\${data.media_type}-\${data.title}`, JSON.stringify(values));
        saveStatus.textContent = 'Черновик сохранён в браузере';
        return;
    }
    saveDraft.disabled = true;
    saveStatus.textContent = 'Сохранение...';
    try {
        const response = await fetch('/api/ratings', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: Number(userId),
                title_id: Number(titleId),
                media_type: data.media_type,
                criteria_values: values,
            }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Не удалось сохранить оценку');
        saveStatus.textContent = `Сохранено: итоговая оценка \${result.overall_rating}`;
    } catch (error) {
        saveStatus.textContent = error.message;
    } finally {
        saveDraft.disabled = false;
    }
});

render();
Object.keys(data.criteria).forEach(calculateImpact);
calculateOverall();
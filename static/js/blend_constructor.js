// JavaScript для конструктора авторских сборов

let selectedBase = null;
let selectedBaseType = null;
let selectedBaseTea = null;
let selectedIngredients = [];
const MAX_INGREDIENTS = 5;

// Функция для экранирования HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация (будет выполнена в конце файла после объединения обработчиков)

// Выбор типа основы
async function selectBaseType(typeId, typeName) {
    selectedBaseType = {
        id: typeId,
        name: typeName,
    };
    selectedBaseTea = null; // Сбрасываем выбранный чай
    
    // Визуальное выделение
    document.querySelectorAll('.base-option').forEach(opt => {
        opt.classList.remove('selected');
        if (parseInt(opt.dataset.typeId) === typeId) {
            opt.classList.add('selected');
        }
    });
    
    // Обновляем отображение выбранного типа
    const selectedBaseTypeEl = document.getElementById('selectedBaseType');
    selectedBaseTypeEl.innerHTML = `<span class="base-name">Тип: ${typeName}</span>`;
    
    // Показываем секцию выбора конкретного чая
    const teaSelection = document.getElementById('teaSelection');
    const teaOptions = document.getElementById('teaOptions');
    teaSelection.style.display = 'block';
    teaOptions.innerHTML = '<div class="loading-teas">Загрузка чаев...</div>';
    
    // Загружаем чаи этого типа
    try {
        const response = await fetch(`/api/teas/by-type/${typeId}`);
        const data = await response.json();
        
        if (data.teas && data.teas.length > 0) {
            teaOptions.innerHTML = `
                <div class="tea-option" onclick="selectBaseTea(null, null)" data-tea-id="">
                    <div class="tea-option-name">Использовать просто тип чая</div>
                    <div class="tea-option-info">Без конкретного чая</div>
                </div>
                ${data.teas.map(tea => `
                    <div class="tea-option" onclick="selectBaseTea(${tea.id}, '${escapeHtml(tea.name)}', ${tea.price_per_100g})" data-tea-id="${tea.id}">
                        <div class="tea-option-name">${escapeHtml(tea.name)}</div>
                        <div class="tea-option-info">
                            ${tea.country ? tea.country : ''}${tea.region ? ', ' + tea.region : ''}
                            ${tea.price_per_100g ? ' • ' + Math.round(tea.price_per_100g) + ' ₽/100г' : ''}
                        </div>
                    </div>
                `).join('')}
            `;
        } else {
            teaOptions.innerHTML = '<div class="no-teas">Чаи этого типа не найдены. Будет использован только тип чая.</div>';
            // Автоматически устанавливаем только тип
            selectBaseTea(null, null);
        }
    } catch (error) {
        console.error('Ошибка загрузки чаев:', error);
        teaOptions.innerHTML = '<div class="error-teas">Ошибка загрузки чаев. Будет использован только тип чая.</div>';
        selectBaseTea(null, null);
    }
    
    // Обновляем основу
    updateSelectedBase();
}

// Выбор конкретного чая
function selectBaseTea(teaId, teaName, teaPrice) {
    selectedBaseTea = teaId ? {
        id: teaId,
        name: teaName,
        price_per_100g: teaPrice,
    } : null;
    
    // Визуальное выделение
    document.querySelectorAll('.tea-option').forEach(opt => {
        opt.classList.remove('selected');
        if (opt.dataset.teaId === (teaId ? teaId.toString() : '')) {
            opt.classList.add('selected');
        }
    });
    
    // Обновляем отображение выбранного чая
    const selectedTeaEl = document.getElementById('selectedTea');
    if (selectedBaseTea) {
        selectedTeaEl.innerHTML = `<span class="tea-name">Выбран: ${escapeHtml(selectedBaseTea.name)}</span>`;
    } else {
        selectedTeaEl.innerHTML = '<span class="selected-label">Используется только тип чая</span>';
    }
    
    // Обновляем основу
    updateSelectedBase();
}

// Обновление выбранной основы (комбинирует тип и чай)
function updateSelectedBase() {
    if (!selectedBaseType) {
        selectedBase = null;
        updateBlendDisplay();
        return;
    }
    
    // Определяем название и цену
    let baseName = selectedBaseType.name;
    let basePrice = 300; // Базовая цена типа чая
    
    if (selectedBaseTea) {
        baseName = selectedBaseTea.name;
        basePrice = selectedBaseTea.price_per_100g;
    }
    
    selectedBase = {
        type_id: selectedBaseType.id,
        type_name: selectedBaseType.name,
        tea_id: selectedBaseTea ? selectedBaseTea.id : null,
        tea_name: selectedBaseTea ? selectedBaseTea.name : null,
        name: baseName,
        price_per_100g: basePrice,
        weight: 50, // Начальный вес основы в граммах
    };
    
    updateBlendDisplay();
}

// Показ категории ингредиентов
function showCategory(categoryName) {
    // Обновляем табы
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.category === categoryName) {
            btn.classList.add('active');
        }
    });
    
    // Показываем нужную категорию
    document.querySelectorAll('.ingredient-category').forEach(cat => {
        cat.classList.remove('active');
    });
    
    const categoryEl = document.getElementById(`category-${categoryName}`);
    if (categoryEl) {
        categoryEl.classList.add('active');
    }
}

// Добавление ингредиента
function addIngredient(id, name, price100g, price20g) {
    // Проверяем лимит
    if (selectedIngredients.length >= MAX_INGREDIENTS) {
        alert('Можно добавить максимум ' + MAX_INGREDIENTS + ' ингредиентов');
        return;
    }
    
    // Проверяем, не добавлен ли уже
    if (selectedIngredients.find(ing => ing.id === id)) {
        alert('Этот ингредиент уже добавлен');
        return;
    }
    
    // Добавляем ингредиент с начальным весом 10г
    selectedIngredients.push({
        id: id,
        name: name,
        price_per_100g: price100g,
        price_per_20g: price20g || price100g * 0.2,
        weight: 10, // Начальный вес в граммах
    });
    
    updateBlendDisplay();
}

// Удаление ингредиента
function removeIngredient(id) {
    selectedIngredients = selectedIngredients.filter(ing => ing.id !== id);
    updateBlendDisplay();
}

// Изменение веса ингредиента
function changeIngredientWeight(id, newWeight) {
    const ingredient = selectedIngredients.find(ing => ing.id === id);
    if (!ingredient) return;
    
    const weight = Math.max(0, Math.min(1000, Math.round(parseFloat(newWeight)))); // Максимум 1000г
    ingredient.weight = weight;
    
    updateBlendDisplayValues();
}

// Изменение веса основы
function changeBaseWeight(newWeight) {
    if (!selectedBase) return;
    
    const weight = Math.max(0, Math.min(1000, Math.round(parseFloat(newWeight)))); // Максимум 1000г
    selectedBase.weight = weight;
    
    updateBlendDisplayValues();
}

// Обновление отображения состава (полное пересоздание)
function updateBlendDisplay() {
    const compositionEl = document.getElementById('blendComposition');
    const nameSection = document.getElementById('blendNameSection');
    const summary = document.getElementById('blendSummary');
    const actions = document.getElementById('blendActions');
    
    if (!selectedBase && selectedIngredients.length === 0) {
        // Пустое состояние
        compositionEl.innerHTML = `
            <div class="empty-state">
                <p>🌿</p>
                <p>Выберите основу и добавьте ингредиенты, чтобы начать создавать свой сбор</p>
            </div>
        `;
        nameSection.style.display = 'none';
        summary.style.display = 'none';
        actions.style.display = 'none';
        return;
    }
    
    // Строим состав
    let html = '';
    
    if (selectedBase) {
        const totalWeight = getTotalWeight();
        html += `
            <div class="blend-component-item">
                <div class="component-header">
                    <span class="component-name">${selectedBase.name} (основа)</span>
                    <button class="component-remove" onclick="removeBase()" title="Удалить">×</button>
                </div>
                <div class="weight-control">
                    <input type="number" class="weight-input" id="baseWeightInput" 
                        value="${selectedBase.weight}" 
                        min="0" max="1000" step="1"
                        onchange="changeBaseWeight(this.value)">
                    <span class="weight-unit">г</span>
                    <input type="range" class="component-slider" id="baseSlider" min="0" max="200" 
                        value="${selectedBase.weight}" 
                        step="1">
                </div>
                <div class="component-percentage">
                    <span class="percentage-info" id="basePercentageInfo">0% от общего веса</span>
                </div>
            </div>
        `;
    }
    
    selectedIngredients.forEach(ingredient => {
        html += `
            <div class="blend-component-item">
                <div class="component-header">
                    <span class="component-name">${ingredient.name}</span>
                    <button class="component-remove" onclick="removeIngredient(${ingredient.id})" title="Удалить">×</button>
                </div>
                <div class="weight-control">
                    <input type="number" class="weight-input" id="ingredientWeightInput${ingredient.id}" 
                        value="${ingredient.weight}" 
                        min="0" max="1000" step="1"
                        onchange="changeIngredientWeight(${ingredient.id}, this.value)">
                    <span class="weight-unit">г</span>
                    <input type="range" class="component-slider" id="ingredientSlider${ingredient.id}" min="0" max="200" 
                        value="${ingredient.weight}" 
                        step="1">
                </div>
                <div class="component-percentage">
                    <span class="percentage-info" id="ingredientInfo${ingredient.id}">0% от общего веса • ${ingredient.price_per_100g.toFixed(0)} ₽/100г</span>
                </div>
            </div>
        `;
    });
    
    compositionEl.innerHTML = html;
    
    // Добавляем обработчики событий для ползунков
    if (selectedBase) {
        const baseSlider = document.getElementById('baseSlider');
        const baseWeightInput = document.getElementById('baseWeightInput');
        if (baseSlider) {
            baseSlider.addEventListener('input', function() {
                const weight = parseFloat(this.value);
                selectedBase.weight = weight;
                if (baseWeightInput) baseWeightInput.value = weight;
                updateBlendDisplayValues();
            });
        }
        if (baseWeightInput) {
            baseWeightInput.addEventListener('change', function() {
                changeBaseWeight(this.value);
            });
        }
    }
    
    selectedIngredients.forEach(ingredient => {
        const slider = document.getElementById(`ingredientSlider${ingredient.id}`);
        const weightInput = document.getElementById(`ingredientWeightInput${ingredient.id}`);
        if (slider) {
            slider.addEventListener('input', function() {
                const weight = parseFloat(this.value);
                ingredient.weight = weight;
                if (weightInput) weightInput.value = weight;
                updateBlendDisplayValues();
            });
        }
        if (weightInput) {
            weightInput.addEventListener('change', function() {
                changeIngredientWeight(ingredient.id, this.value);
            });
        }
    });
    
    // Показываем секции
    nameSection.style.display = 'block';
    summary.style.display = 'block';
    actions.style.display = 'block';
    
    // Обновляем итоги
    updateSummary();
}

// Получение общего веса
function getTotalWeight() {
    let total = 0;
    if (selectedBase) {
        total += selectedBase.weight;
    }
    selectedIngredients.forEach(ing => {
        total += ing.weight;
    });
    return total;
}

// Получение процента основы
function getBasePercentage() {
    if (!selectedBase) return 0;
    const total = getTotalWeight();
    if (total === 0) return 0;
    return Math.round((selectedBase.weight / total) * 100);
}

// Получение процента ингредиента
function getIngredientPercentage(ingredient) {
    const total = getTotalWeight();
    if (total === 0) return 0;
    return Math.round((ingredient.weight / total) * 100);
}

// Обновление только значений (без пересоздания HTML)
function updateBlendDisplayValues() {
    // Обновляем ползунок и поле ввода основы
    if (selectedBase) {
        const baseSlider = document.getElementById('baseSlider');
        const baseWeightInput = document.getElementById('baseWeightInput');
        const basePercentageInfo = document.querySelector('#blendComposition .blend-component-item:first-child .percentage-info');
        
        if (baseSlider) {
            baseSlider.value = selectedBase.weight;
        }
        if (baseWeightInput) {
            baseWeightInput.value = selectedBase.weight;
        }
        if (basePercentageInfo) {
            const totalWeight = getTotalWeight();
            const percentage = totalWeight > 0 ? Math.round((selectedBase.weight / totalWeight) * 100) : 0;
            basePercentageInfo.textContent = `${percentage}% от общего веса (${totalWeight}г)`;
        }
    }
    
    // Обновляем ползунки и поля ввода ингредиентов
    const totalWeight = getTotalWeight();
    selectedIngredients.forEach((ingredient, index) => {
        const slider = document.getElementById(`ingredientSlider${ingredient.id}`);
        const weightInput = document.getElementById(`ingredientWeightInput${ingredient.id}`);
        const itemIndex = selectedBase ? index + 2 : index + 1;
        const percentageInfo = document.querySelector(`#blendComposition .blend-component-item:nth-child(${itemIndex}) .percentage-info`);
        
        if (slider) {
            slider.value = ingredient.weight;
        }
        if (weightInput) {
            weightInput.value = ingredient.weight;
        }
        if (percentageInfo) {
            const percentage = totalWeight > 0 ? Math.round((ingredient.weight / totalWeight) * 100) : 0;
            percentageInfo.textContent = `${percentage}% от общего веса • ${ingredient.price_per_100g.toFixed(0)} ₽/100г`;
        }
    });
    
    // Обновляем итоги
    updateSummary();
}

// Удаление основы
function removeBase() {
    selectedBase = null;
    selectedBaseType = null;
    selectedBaseTea = null;
    document.querySelectorAll('.base-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    document.querySelectorAll('.tea-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    document.getElementById('selectedBaseType').innerHTML = '<span class="selected-label">Тип основы не выбран</span>';
    document.getElementById('selectedTea').innerHTML = '<span class="selected-label">Или используйте просто тип чая</span>';
    document.getElementById('teaSelection').style.display = 'none';
    
    updateBlendDisplay();
}

// Обновление итоговой информации
function updateSummary() {
    const totalWeight = getTotalWeight();
    const totalWeightEl = document.getElementById('totalWeight');
    
    if (totalWeightEl) {
        totalWeightEl.textContent = `${totalWeight} г`;
    }
    
    if (!selectedBase && selectedIngredients.length === 0) {
        const price100gEl = document.getElementById('price100g');
        const price20gEl = document.getElementById('price20g');
        const totalPriceEl = document.getElementById('totalPrice');
        if (price100gEl) price100gEl.textContent = '0 ₽';
        if (price20gEl) price20gEl.textContent = '0 ₽';
        if (totalPriceEl) totalPriceEl.textContent = '0 ₽';
        return;
    }
    
    // Рассчитываем цену на основе весов
    let totalPrice = 0;
    
    // Цена основы
    if (selectedBase) {
        const basePricePer100g = selectedBase.price_per_100g || 300;
        totalPrice += (basePricePer100g * selectedBase.weight) / 100;
    }
    
    // Цена ингредиентов
    selectedIngredients.forEach(ingredient => {
        totalPrice += (ingredient.price_per_100g * ingredient.weight) / 100;
    });
    
    // Общая стоимость
    const totalPriceEl = document.getElementById('totalPrice');
    if (totalPriceEl) totalPriceEl.textContent = `${Math.round(totalPrice)} ₽`;
    
    // Цена за 100г и 20г (средняя цена)
    const pricePer100g = totalWeight > 0 ? (totalPrice / totalWeight) * 100 : 0;
    const price20g = pricePer100g * 0.2;
    
    const price100gEl = document.getElementById('price100g');
    const price20gEl = document.getElementById('price20g');
    if (price100gEl) price100gEl.textContent = `${Math.round(pricePer100g)} ₽`;
    if (price20gEl) price20gEl.textContent = `${Math.round(price20g)} ₽`;
}

// Сохранение сбора
async function saveBlend() {
    if (!selectedBase) {
        alert('Выберите основу чая');
        return;
    }
    
    const blendName = document.getElementById('blendName').value.trim();
    if (!blendName) {
        alert('Введите название сбора');
        return;
    }
    
    const totalWeight = getTotalWeight();
    if (totalWeight === 0) {
        alert('Добавьте хотя бы один компонент с весом больше 0');
        return;
    }
    
    // Проверяем ингредиенты
    if (selectedIngredients.length === 0) {
        alert('Добавьте хотя бы один ингредиент');
        return;
    }
    
    // Подготавливаем данные для отправки
    const ingredients = selectedIngredients.map(ing => ({
        id: ing.id,
        weight: ing.weight,
    }));
    
    const data = {
        name: blendName,
        base_tea_type_id: selectedBase.type_id,
        base_tea_id: selectedBase.tea_id || null,
        base_weight: selectedBase.weight,
        ingredients: ingredients,
    };
    
    try {
        // Показываем индикатор загрузки
        const saveButton = document.querySelector('.blend-actions .btn-primary');
        const originalText = saveButton.textContent;
        saveButton.disabled = true;
        saveButton.textContent = 'Сохранение...';
        
        // Отправляем запрос
        const response = await fetch('/api/blends/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Важно: отправляем cookies
            body: JSON.stringify(data),
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`Сбор "${blendName}" успешно сохранен!`);
            // Можно перенаправить на страницу сбора или очистить форму
            // resetBlend();
        } else {
            // Проверяем, не авторизован ли пользователь
            if (response.status === 401) {
                // Сохраняем данные сбора в sessionStorage
                sessionStorage.setItem('pendingBlend', JSON.stringify(data));
                alert('Для сохранения сборов необходимо войти в аккаунт. После входа сбор будет сохранен автоматически.');
                window.location.href = '/login?next=/blend-constructor&restore=true';
                return;
            }
            
            // Обработка ошибок
            let errorMessage = 'Неизвестная ошибка';
            if (result.detail) {
                if (typeof result.detail === 'string') {
                    errorMessage = result.detail;
                } else if (Array.isArray(result.detail)) {
                    errorMessage = result.detail.map(err => err.msg || err).join(', ');
                } else {
                    errorMessage = JSON.stringify(result.detail);
                }
            } else if (result.message) {
                errorMessage = result.message;
            }
            alert(`Ошибка при сохранении: ${errorMessage}`);
        }
    } catch (error) {
        console.error('Ошибка при сохранении сбора:', error);
        alert('Произошла ошибка при сохранении сбора. Попробуйте еще раз.');
    } finally {
        // Восстанавливаем кнопку
        const saveButton = document.querySelector('.blend-actions .btn-primary');
        if (saveButton) {
            saveButton.disabled = false;
            saveButton.textContent = 'Сохранить рецепт';
        }
    }
}

// Сброс сбора
function resetBlend() {
    if (!confirm('Вы уверены, что хотите начать заново? Все данные будут потеряны.')) {
        return;
    }
    
    selectedBase = null;
    selectedBaseType = null;
    selectedBaseTea = null;
    selectedIngredients = [];
    document.getElementById('blendName').value = '';
    document.querySelectorAll('.base-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    document.querySelectorAll('.tea-option').forEach(opt => {
        opt.classList.remove('selected');
    });
    document.getElementById('selectedBaseType').innerHTML = '<span class="selected-label">Тип основы не выбран</span>';
    document.getElementById('selectedTea').innerHTML = '<span class="selected-label">Или используйте просто тип чая</span>';
    document.getElementById('teaSelection').style.display = 'none';
    
    updateBlendDisplay();
}

// Восстановление сбора после входа
async function restorePendingBlend() {
    const pendingBlend = sessionStorage.getItem('pendingBlend');
    if (!pendingBlend) return;
    
    try {
        const data = JSON.parse(pendingBlend);
        
        // Проверяем, что страница загружена
        if (!document.getElementById('blendName')) {
            console.log('Страница еще не загружена, ждем...');
            setTimeout(restorePendingBlend, 100);
            return;
        }
        
        // Отправляем запрос на сохранение напрямую (без восстановления UI состояния)
        const response = await fetch('/api/blends/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data),
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`Сбор "${data.name}" успешно сохранен!`);
            // Удаляем из sessionStorage только после успешного сохранения
            sessionStorage.removeItem('pendingBlend');
        } else {
            console.error('Ошибка при сохранении восстановленного сбора:', result);
            // Если ошибка авторизации, оставляем данные в sessionStorage
            if (response.status === 401) {
                alert('Не удалось автоматически сохранить сбор. Пожалуйста, войдите в аккаунт и попробуйте снова.');
            } else {
                // Для других ошибок показываем сообщение, что сбор можно сохранить вручную
                alert('Не удалось автоматически сохранить сбор. Попробуйте сохранить его вручную.');
                sessionStorage.removeItem('pendingBlend');
            }
        }
    } catch (error) {
        console.error('Ошибка при восстановлении сбора:', error);
        // Не удаляем из sessionStorage при ошибке, чтобы пользователь мог попробовать еще раз
    }
}

// Проверяем, есть ли сохраненный сбор при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем наличие сохраненного сбора в sessionStorage
    // Только если мы вернулись со страницы авторизации (есть параметр restored=true в URL)
    const urlParams = new URLSearchParams(window.location.search);
    const restored = urlParams.get('restored');
    const pendingBlend = sessionStorage.getItem('pendingBlend');
    
    if (pendingBlend && restored === 'true') {
        console.log('Найден сохраненный сбор после авторизации, восстанавливаем...');
        // Очищаем параметр из URL
        urlParams.delete('restored');
        const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
        window.history.replaceState({}, '', newUrl);
        // Даем немного времени на полную загрузку страницы
        setTimeout(restorePendingBlend, 500);
    }
    
    // Инициализация табов категорий
    const firstTab = document.querySelector('.tab-btn');
    if (firstTab) {
        firstTab.classList.add('active');
        const firstCategory = firstTab.dataset.category;
        if (firstCategory) {
            showCategory(firstCategory);
        }
    }
});

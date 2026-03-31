// JavaScript для каталога

let currentTab = 'teas';
let currentPage = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Загрузка регионов при выборе страны
    const countrySelect = document.getElementById('countrySelect');
    const regionGroup = document.getElementById('regionGroup');
    const regionSelect = document.getElementById('regionSelect');
    
    if (countrySelect) {
        // Сохраняем изначально выбранную страну для проверки
        const initialCountryId = countrySelect.value;
        const urlParams = new URLSearchParams(window.location.search);
        const initialRegionId = urlParams.get('region_id');
        
        countrySelect.addEventListener('change', function() {
            const countryId = this.value;
            
            if (countryId) {
                // Показываем группу регионов
                regionGroup.style.display = 'block';
                
                // Сбрасываем выбранный регион, если страна изменилась
                if (regionSelect && regionSelect.value) {
                    regionSelect.value = '';
                }
                
                // Загружаем регионы через API, после загрузки применяем фильтры
                loadRegions(countryId).then(() => {
                    applyFilters();
                });
            } else {
                // Скрываем группу регионов
                regionGroup.style.display = 'none';
                regionSelect.innerHTML = '<option value="">Все регионы</option>';
                // Сбрасываем выбранный регион в форме
                if (regionSelect) {
                    regionSelect.value = '';
                }
                // Применяем фильтры
                applyFilters();
            }
        });
        
        // Обработчик изменения региона
        if (regionSelect) {
            regionSelect.addEventListener('change', function() {
                applyFilters();
            });
        }
        
        // Если страна уже выбрана при загрузке страницы, загружаем регионы
        if (initialCountryId) {
            loadRegions(initialCountryId, initialRegionId);
        }
    }
    
    // Инициализация табов после загрузки страницы
    const urlParams = new URLSearchParams(window.location.search);
    currentTab = urlParams.get('tab') || 'teas';
    currentPage = parseInt(urlParams.get('page') || '1');

    if (currentTab === 'blends') {
        // Скрываем контейнер с чаями, показываем контейнер со сборами
        const teasContainer = document.getElementById('teasContainer');
        const blendsContainer = document.getElementById('blendsContainer');
        if (teasContainer) teasContainer.style.display = 'none';
        if (blendsContainer) {
            blendsContainer.style.display = 'block';
            loadBlends(currentPage);
        }
    } else {
        // Скрываем контейнер со сборами, показываем контейнер с чаями
        const blendsContainer = document.getElementById('blendsContainer');
        if (blendsContainer) blendsContainer.style.display = 'none';
    }
    
    // Автоматическое применение фильтров при изменении (кроме страны и региона - они обрабатываются отдельно)
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        const filterSelects = filterForm.querySelectorAll('select:not(#countrySelect):not(#regionSelect)');
        const searchInput = document.getElementById('searchInput');
        
        // Для select элементов (кроме страны и региона) - применяем сразу при изменении
        filterSelects.forEach(select => {
            select.addEventListener('change', function() {
                applyFilters();
            });
        });
        
        // Для поиска - применяем с задержкой (debounce)
        let searchTimeout;
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    applyFilters();
                }, 500); // Задержка 500мс для поиска
            });
        }
    }
});

// Функция для автоматического применения фильтров
function applyFilters() {
    const filterForm = document.getElementById('filterForm');
    if (!filterForm) return;
    
    const formData = new FormData(filterForm);
    const params = new URLSearchParams();
    
    // Собираем все параметры из формы
    for (const [key, value] of formData.entries()) {
        if (value) {
            params.append(key, value);
        }
    }
    
    // Перенаправляем на URL с параметрами
    const url = `/catalog?${params.toString()}`;
    window.location.href = url;
}

async function loadRegions(countryId, selectedRegionId = null) {
    const regionSelect = document.getElementById('regionSelect');
    if (!regionSelect) return;
    
    try {
        // Показываем индикатор загрузки
        regionSelect.disabled = true;
        regionSelect.innerHTML = '<option value="">Загрузка...</option>';
        
        const response = await fetch(`/api/countries/${countryId}/regions`);
        if (!response.ok) {
            throw new Error('Ошибка загрузки регионов');
        }
        
        const data = await response.json();
        
        // Очищаем и заполняем список регионов
        regionSelect.innerHTML = '<option value="">Все регионы</option>';
        
        data.regions.forEach(region => {
            const option = document.createElement('option');
            option.value = region.id;
            option.textContent = region.name;
            if (selectedRegionId && region.id == selectedRegionId) {
                option.selected = true;
            }
            regionSelect.appendChild(option);
        });
        
        regionSelect.disabled = false;
    } catch (error) {
        console.error('Ошибка загрузки регионов:', error);
        regionSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        regionSelect.disabled = false;
    }
}

function addToCart(teaId, size = 100) {
    // Используем глобальную функцию из cart_utils.js
    if (window.addToCart) {
        window.addToCart(teaId, size, 'tea');
    } else {
        console.error('Функция addToCart не загружена');
    }
}

// Загрузка сборов
async function loadBlends(page = 1) {
    const container = document.getElementById('blendsContainer');
    const resultsCount = document.getElementById('resultsCount');
    if (!container) return;
    
    container.innerHTML = '<div class="loading">Загрузка сборов...</div>';
    
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const teaTypeId = urlParams.get('tea_type_id') || '';
        const search = urlParams.get('search') || '';
        const sort = urlParams.get('sort') || 'newest';
        
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: '12',
            sort: sort,
        });
        
        if (teaTypeId) params.append('tea_type_id', teaTypeId);
        if (search) params.append('search', search);
        
        const response = await fetch(`/api/blends?${params.toString()}`);
        const data = await response.json();
        
        if (resultsCount) {
            resultsCount.textContent = `Найдено: ${data.pagination.total} сборов`;
        }
        
        if (data.blends && data.blends.length > 0) {
            container.innerHTML = data.blends.map(blend => `
                <div class="blend-card card">
                    <div class="tea-image" style="background: linear-gradient(135deg, #8b6f47 0%, #d4a574 100%);">
                        🍵
                    </div>
                    <div class="tea-info">
                        <h3><a href="/blend/${blend.id}">${escapeHtml(blend.name)}</a></h3>
                        <div class="blend-base">
                            <span class="base-badge">${blend.base_tea ? escapeHtml(blend.base_tea.name) : (blend.base_tea_type ? escapeHtml(blend.base_tea_type.name) : 'Смесь')}</span>
                        </div>
                        ${blend.ingredients && blend.ingredients.length > 0 ? `
                            <div class="blend-ingredients">
                                ${blend.ingredients.map(ing => `<span class="ingredient-badge">${escapeHtml(ing.name)}</span>`).join('')}
                            </div>
                        ` : ''}
                        ${blend.short_description ? `<p class="tea-description">${escapeHtml(blend.short_description)}</p>` : ''}
                        <div class="tea-meta">
                            ${blend.rating > 0 ? `<span class="tea-rating">⭐ ${blend.rating.toFixed(1)} (${blend.review_count})</span>` : ''}
                            ${blend.creator ? `<span class="tea-creator">👤 ${escapeHtml(blend.creator.username)}</span>` : ''}
                        </div>
                        ${blend.price_per_100g ? `<div class="tea-price"><span class="price-main">${blend.price_per_100g.toFixed(2)} ₽ / 100г</span></div>` : ''}
                        <div class="tea-actions">
                            <button class="btn btn-primary" onclick="viewBlend(${blend.id})">Подробнее</button>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="empty-state"><p>😔 Сборы не найдены</p><p>Попробуйте изменить фильтры</p></div>';
        }
    } catch (error) {
        console.error('Ошибка загрузки сборов:', error);
        container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки сборов</p></div>';
    }
}

function viewBlend(blendId) {
    window.location.href = `/blend/${blendId}`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


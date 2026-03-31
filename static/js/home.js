// JavaScript для главной страницы

document.addEventListener('DOMContentLoaded', function() {
    // Загрузка популярных чаев
    loadPopularTeas();
    
    // Загрузка популярных сборов
    loadPopularBlends();
    
    // Загрузка чайной карты
    loadTeaMap();
    
    // Обновление счетчика корзины
    if (typeof updateCartBadge === 'function') {
        updateCartBadge();
    }
});

async function loadPopularTeas() {
    const container = document.getElementById('popularTeas');
    if (!container) return;
    
    try {
        const response = await fetch('/api/teas/popular?limit=8');
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка ответа сервера:', response.status, errorText);
            throw new Error(`Ошибка ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        container.innerHTML = '';
        
        if (data.teas && data.teas.length > 0) {
            data.teas.forEach(tea => {
                const card = createTeaCard(tea);
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p class="text-center" style="grid-column: 1 / -1; padding: 2rem;">Популярные чаи появятся здесь</p>';
        }
    } catch (error) {
        console.error('Ошибка загрузки популярных чаев:', error);
        container.innerHTML = '<p class="text-center" style="grid-column: 1 / -1; padding: 2rem; color: var(--error);">Ошибка загрузки данных. Проверьте консоль браузера.</p>';
    }
}

function createTeaCard(tea) {
    const card = document.createElement('div');
    card.className = 'card tea-card';
    
    const imageUrl = tea.main_image_url || '/static/images/placeholder-tea.jpg';
    const minPrice = tea.price_per_20g || tea.price_per_100g;
    const location = tea.country ? (tea.region ? `${tea.country.name}, ${tea.region.name}` : tea.country.name) : '';
    
    card.innerHTML = `
        <a href="/tea/${tea.slug}" class="tea-card-link">
            <div class="tea-image" style="background-image: url('${imageUrl}'); background-size: cover; background-position: center;">
                ${!tea.main_image_url ? '<span class="tea-placeholder-icon">🍃</span>' : ''}
            </div>
            <div class="tea-card-content">
                <h3>${escapeHtml(tea.name)}</h3>
                ${location ? `<p class="tea-region">${escapeHtml(location)}</p>` : ''}
                <p class="tea-price">от ${Math.round(minPrice)} ₽</p>
                <div class="tea-stats">
                    ${tea.purchase_count > 0 ? `<span class="tea-stat">👥 ${tea.purchase_count} заказов</span>` : ''}
                    ${tea.rating > 0 ? `<span class="tea-stat">⭐ ${tea.rating.toFixed(1)}</span>` : ''}
                </div>
            </div>
        </a>
    `;
    
    return card;
}

async function loadPopularBlends() {
    const container = document.getElementById('popularBlends');
    if (!container) return;
    
    try {
        const response = await fetch('/api/blends/popular?limit=6');
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка ответа сервера:', response.status, errorText);
            throw new Error(`Ошибка ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        container.innerHTML = '';
        
        if (data.blends && data.blends.length > 0) {
            data.blends.forEach(blend => {
                const card = createBlendCard(blend);
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p class="text-center" style="grid-column: 1 / -1; padding: 2rem;">Популярные сборы появятся здесь</p>';
        }
    } catch (error) {
        console.error('Ошибка загрузки популярных сборов:', error);
        container.innerHTML = '<p class="text-center" style="grid-column: 1 / -1; padding: 2rem; color: var(--error);">Ошибка загрузки данных. Проверьте консоль браузера.</p>';
    }
}

function createBlendCard(blend) {
    const card = document.createElement('div');
    card.className = 'card blend-card';
    
    const minPrice = blend.price_per_20g || blend.price_per_100g;
    const baseInfo = blend.base_tea ? blend.base_tea.name : (blend.base_tea_type ? blend.base_tea_type.name : '');
    
    card.innerHTML = `
        <div class="blend-header">
            <h3>${escapeHtml(blend.name)}</h3>
            <span class="blend-author">@${escapeHtml(blend.creator.username)}</span>
        </div>
        ${baseInfo ? `<p class="blend-base">Основа: ${escapeHtml(baseInfo)}</p>` : ''}
        ${blend.description ? `<p class="blend-description">${escapeHtml(blend.description.substring(0, 100))}${blend.description.length > 100 ? '...' : ''}</p>` : ''}
        <div class="blend-stats">
            <span>👥 ${blend.purchase_count} заказов</span>
            <span>👁️ ${blend.view_count} просмотров</span>
            ${blend.rating > 0 ? `<span>⭐ ${blend.rating.toFixed(1)}</span>` : ''}
        </div>
        ${minPrice ? `<p class="blend-price">от ${Math.round(minPrice)} ₽</p>` : ''}
        <a href="/blend/${blend.id}" class="btn btn-outline">Посмотреть рецепт</a>
    `;
    
    return card;
}

async function loadTeaMap() {
    const container = document.getElementById('worldMap');
    if (!container) return;
    
    // Проверяем, есть ли уже карта (Leaflet)
    if (typeof L === 'undefined') {
        console.error('Leaflet не загружен');
        return;
    }
    
    try {
        // Загружаем данные стран для карты
        const response = await fetch('/api/tea-map/countries');
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Ошибка ответа сервера:', response.status, errorText);
            throw new Error(`Ошибка ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        
        if (data.countries && data.countries.length > 0) {
            // Создаем контейнер для карты
            container.innerHTML = '<div id="teaMap" style="width: 100%; height: 500px;"></div>';
            
            // Инициализируем карту используя код из tea_map.js
            initTeaMapOnHomePage(data.countries);
        } else {
            container.innerHTML = '<div class="map-placeholder"><p>Чайная карта будет здесь</p><p>Пока можно перейти к <a href="/catalog">каталогу</a></p></div>';
        }
    } catch (error) {
        console.error('Ошибка загрузки чайной карты:', error);
        container.innerHTML = '<div class="map-placeholder"><p style="color: var(--error);">Ошибка загрузки карты. Проверьте консоль браузера.</p></div>';
    }
}

// Функция инициализации карты на главной странице (адаптированная версия из tea_map.js)
function initTeaMapOnHomePage(countriesData) {
    // Координаты основных чайных стран (из tea_map.js)
    const countryCoordinates = {
        "Китай": { lat: 35.8617, lng: 104.1954, zoom: 5 },
        "China": { lat: 35.8617, lng: 104.1954, zoom: 5 },
        "Индия": { lat: 20.5937, lng: 78.9629, zoom: 5 },
        "India": { lat: 20.5937, lng: 78.9629, zoom: 5 },
        "Шри-Ланка": { lat: 7.8731, lng: 80.7718, zoom: 8 },
        "Sri Lanka": { lat: 7.8731, lng: 80.7718, zoom: 8 },
        "Япония": { lat: 36.2048, lng: 138.2529, zoom: 6 },
        "Japan": { lat: 36.2048, lng: 138.2529, zoom: 6 },
        "Тайвань": { lat: 23.6978, lng: 120.9605, zoom: 8 },
        "Taiwan": { lat: 23.6978, lng: 120.9605, zoom: 8 },
        "Кения": { lat: -0.0236, lng: 37.9062, zoom: 6 },
        "Kenya": { lat: -0.0236, lng: 37.9062, zoom: 6 },
        "Непал": { lat: 28.3949, lng: 84.1240, zoom: 7 },
        "Nepal": { lat: 28.3949, lng: 84.1240, zoom: 7 },
        "Вьетнам": { lat: 14.0583, lng: 108.2772, zoom: 6 },
        "Vietnam": { lat: 14.0583, lng: 108.2772, zoom: 6 },
        "Грузия": { lat: 42.3154, lng: 43.3569, zoom: 7 },
        "Georgia": { lat: 42.3154, lng: 43.3569, zoom: 7 },
        "Турция": { lat: 38.9637, lng: 35.2433, zoom: 6 },
        "Turkey": { lat: 38.9637, lng: 35.2433, zoom: 6 },
        "Индонезия": { lat: -0.7893, lng: 113.9213, zoom: 5 },
        "Indonesia": { lat: -0.7893, lng: 113.9213, zoom: 5 },
        "Бангладеш": { lat: 23.6850, lng: 90.3563, zoom: 7 },
        "Bangladesh": { lat: 23.6850, lng: 90.3563, zoom: 7 },
        "Азербайджан": { lat: 40.1431, lng: 47.5769, zoom: 7 },
        "Azerbaijan": { lat: 40.1431, lng: 47.5769, zoom: 7 },
        "Россия": { lat: 61.5240, lng: 105.3188, zoom: 4 },
        "Russia": { lat: 61.5240, lng: 105.3188, zoom: 4 },
    };
    
    // Создаем карту
    const map = L.map('teaMap').setView([30, 100], 3);
    
    // Добавляем тайлы OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);
    
    // Добавляем маркеры стран
    countriesData.forEach(country => {
        const countryName = country.name;
        const coords = countryCoordinates[countryName] || countryCoordinates[country.name_en] || { lat: 0, lng: 0, zoom: 5 };
        
        if (coords.lat === 0 && coords.lng === 0) {
            console.warn(`Координаты не найдены для страны: ${countryName}`);
            return;
        }
        
        // Создаем маркер с флагом
        const teaIcon = L.divIcon({
            className: 'tea-country-marker',
            html: `<div class="marker-content">${country.flag || '🍃'}</div>`,
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });
        
        const marker = L.marker([coords.lat, coords.lng], { icon: teaIcon }).addTo(map);
        
        // Подготавливаем HTML для попапа
        const regionsList = country.regions.map(region =>
            `<a href="/catalog?country_id=${country.id}&region_id=${region.id}" class="region-popup-item" data-region-id="${region.id}">
                <span class="region-name">${region.name}</span>
                <span class="region-arrow">→</span>
            </a>`
        ).join('');
        
        const popupContent = `
            <div class="country-popup">
                <div class="country-popup-header">
                    <span class="country-flag-popup">${country.flag || '🌍'}</span>
                    <h3 class="country-name-popup">${country.name}</h3>
                </div>
                <p class="regions-count">${country.regions.length} ${country.regions.length === 1 ? 'регион' : country.regions.length < 5 ? 'региона' : 'регионов'}</p>
                <div class="popup-regions">
                    ${regionsList}
                </div>
                <a href="/catalog?country_id=${country.id}" class="btn-view-catalog" data-country-id="${country.id}">
                    Все чаи страны
                </a>
            </div>
        `;
        
        marker.bindPopup(popupContent, {
            maxWidth: 350,
            className: 'country-popup-container'
        });
        
        marker.on('click', function() {
            // Подсвечиваем маркер при клике
            const markerElement = marker.getElement();
            if (markerElement) {
                const content = markerElement.querySelector('.marker-content');
                if (content) {
                    content.style.boxShadow = '0 0 20px rgba(44, 80, 22, 0.8), 0 0 40px rgba(44, 80, 22, 0.5)';
                    content.style.borderColor = '#1b5e20';
                    setTimeout(() => {
                        content.style.boxShadow = '';
                        content.style.borderColor = '';
                    }, 2000);
                }
            }
        });
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


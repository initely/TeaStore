// JavaScript для чайной карты

// Координаты основных чайных стран
const countryCoordinates = {
    // Китай
    "Китай": { lat: 35.8617, lng: 104.1954, zoom: 5 },
    "China": { lat: 35.8617, lng: 104.1954, zoom: 5 },

    // Индия
    "Индия": { lat: 20.5937, lng: 78.9629, zoom: 5 },
    "India": { lat: 20.5937, lng: 78.9629, zoom: 5 },

    // Шри-Ланка
    "Шри-Ланка": { lat: 7.8731, lng: 80.7718, zoom: 8 },
    "Sri Lanka": { lat: 7.8731, lng: 80.7718, zoom: 8 },

    // Япония
    "Япония": { lat: 36.2048, lng: 138.2529, zoom: 6 },
    "Japan": { lat: 36.2048, lng: 138.2529, zoom: 6 },

    // Тайвань
    "Тайвань": { lat: 23.6978, lng: 120.9605, zoom: 8 },
    "Taiwan": { lat: 23.6978, lng: 120.9605, zoom: 8 },

    // Кения
    "Кения": { lat: -0.0236, lng: 37.9062, zoom: 6 },
    "Kenya": { lat: -0.0236, lng: 37.9062, zoom: 6 },

    // Непал
    "Непал": { lat: 28.3949, lng: 84.1240, zoom: 7 },
    "Nepal": { lat: 28.3949, lng: 84.1240, zoom: 7 },

    // Вьетнам
    "Вьетнам": { lat: 14.0583, lng: 108.2772, zoom: 6 },
    "Vietnam": { lat: 14.0583, lng: 108.2772, zoom: 6 },

    // Грузия
    "Грузия": { lat: 42.3154, lng: 43.3569, zoom: 7 },
    "Georgia": { lat: 42.3154, lng: 43.3569, zoom: 7 },

    // Турция
    "Турция": { lat: 38.9637, lng: 35.2433, zoom: 6 },
    "Turkey": { lat: 38.9637, lng: 35.2433, zoom: 6 },

    // Индонезия
    "Индонезия": { lat: -0.7893, lng: 113.9213, zoom: 5 },
    "Indonesia": { lat: -0.7893, lng: 113.9213, zoom: 5 },

    // Бангладеш
    "Бангладеш": { lat: 23.6850, lng: 90.3563, zoom: 7 },
    "Bangladesh": { lat: 23.6850, lng: 90.3563, zoom: 7 },

    // Азербайджан
    "Азербайджан": { lat: 40.1431, lng: 47.5769, zoom: 7 },
    "Azerbaijan": { lat: 40.1431, lng: 47.5769, zoom: 7 },

    // Россия
    "Россия": { lat: 61.5240, lng: 105.3188, zoom: 4 },
    "Russia": { lat: 61.5240, lng: 105.3188, zoom: 4 },
};

let map;
let countryLayers = {}; // Хранилище для слоев стран

document.addEventListener('DOMContentLoaded', function () {
    // Инициализация карты
    initMap();

    // Инициализация списка стран
    initCountriesList();
});

function initMap() {
    // Создаем карту, центрированную на Азии (где большинство чайных стран)
    map = L.map('teaMap').setView([30, 100], 3);

    // Добавляем тайлы OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    // Добавляем области стран
    if (typeof countriesData !== 'undefined' && countriesData) {
        countriesData.forEach(country => {
            addCountryArea(country);
        });
    }

    // Исправляем размер маркеров при масштабировании
    map.on('zoom', function () {
        fixMarkerSizes();
    });

    map.on('zoomend', function () {
        fixMarkerSizes();
    });
}

function addCountryArea(country) {
    const countryName = country.name;
    const coords = countryCoordinates[countryName] || countryCoordinates[country.name_en] || { lat: 0, lng: 0, zoom: 5 };

    if (coords.lat === 0 && coords.lng === 0) {
        console.warn(`Координаты не найдены для страны: ${countryName}`);
        return;
    }

    // Добавляем только маркер с флагом (без визуальных областей)
    const teaIcon = L.divIcon({
        className: 'tea-country-marker',
        html: `<div class="marker-content">${country.flag || '🍃'}</div>`,
        iconSize: [40, 40],
        iconAnchor: [20, 40],
        popupAnchor: [0, -40]
    });

    const marker = L.marker([coords.lat, coords.lng], { icon: teaIcon }).addTo(map);

    marker.on('click', function () {
        showCountryPopup(country, coords);
        highlightCountry(country.id);
    });

    // Сохраняем ссылки на слои
    countryLayers[country.id] = { marker, country };
}

function fixMarkerSizes() {
    // Исправляем размер маркеров при масштабировании
    // Компенсируем увеличение Leaflet при приближении
    const zoom = map.getZoom();
    const baseZoom = 3; // Базовый zoom
    const scale = Math.pow(2, baseZoom - zoom);

    // Ограничиваем минимальный размер (чтобы маркеры не пропадали)
    const minScale = 0.7; // Минимальный масштаб (40% от оригинала)
    const maxScale = 1; // Максимальный масштаб (140% от оригинала)
    const clampedScale = Math.max(minScale, Math.min(maxScale, scale));

    document.querySelectorAll('.tea-country-marker').forEach(marker => {
        const content = marker.querySelector('.marker-content');
        if (content) {
            content.style.transform = `scale(${clampedScale})`;
            content.style.transformOrigin = 'center center';
        }
    });
}

function showCountryPopup(country, coords) {
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

    // Открываем попап на координатах страны
    const popup = L.popup({
        maxWidth: 350,
        className: 'country-popup-container'
    })
        .setLatLng([coords.lat, coords.lng])
        .setContent(popupContent)
        .openOn(map);

    // Подсвечиваем маркер при открытии попапа
    highlightCountry(country.id);
}

function highlightCountry(countryId) {
    // Подсвечиваем маркер страны при открытии попапа
    const countryLayer = countryLayers[countryId];
    if (countryLayer && countryLayer.marker) {
        const markerElement = countryLayer.marker.getElement();
        if (markerElement) {
            const content = markerElement.querySelector('.marker-content');
            if (content) {
                content.style.boxShadow = '0 0 20px rgba(44, 80, 22, 0.8), 0 0 40px rgba(44, 80, 22, 0.5)';
                content.style.borderColor = '#1b5e20';

                // Возвращаем нормальный стиль через некоторое время
                setTimeout(() => {
                    content.style.boxShadow = '';
                    content.style.borderColor = '';
                }, 2000);
            }
        }
    }
}

function initCountriesList() {
    const countryItems = document.querySelectorAll('.country-item');

    countryItems.forEach(item => {
        item.addEventListener('click', function () {
            const countryId = parseInt(this.getAttribute('data-country-id'));
            const countryData = countriesData.find(c => c.id === countryId);

            if (countryData) {
                // Убираем активный класс со всех элементов
                countryItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');

                // Находим координаты страны
                const countryName = countryData.name;
                const coords = countryCoordinates[countryName] || countryCoordinates[countryData.name_en] || { lat: 0, lng: 0, zoom: 5 };

                if (coords.lat !== 0 && coords.lng !== 0) {
                    map.setView([coords.lat, coords.lng], coords.zoom);
                    const countryLayer = countryLayers[countryId];
                    if (countryLayer) {
                        showCountryPopup(countryData, coords);
                        highlightCountry(countryId);
                    }
                }
            }
        });
    });
}

// Исправляем размер маркеров при загрузке
setTimeout(fixMarkerSizes, 100);

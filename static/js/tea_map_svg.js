// JavaScript для упрощенной SVG карты

// Упрощенные координаты основных чайных стран (в процентах от ширины/высоты SVG)
const countryPositions = {
    // Китай
    "Китай": { x: 850, y: 220, path: "M 800 180 L 900 180 L 920 200 L 910 250 L 890 260 L 870 240 L 800 220 Z" },
    "China": { x: 850, y: 220, path: "M 800 180 L 900 180 L 920 200 L 910 250 L 890 260 L 870 240 L 800 220 Z" },
    
    // Индия
    "Индия": { x: 750, y: 280, path: "M 720 250 L 780 240 L 790 300 L 770 320 L 730 310 Z" },
    "India": { x: 750, y: 280, path: "M 720 250 L 780 240 L 790 300 L 770 320 L 730 310 Z" },
    
    // Шри-Ланка
    "Шри-Ланка": { x: 760, y: 320, path: "M 755 315 L 765 315 L 765 325 L 755 325 Z" },
    "Sri Lanka": { x: 760, y: 320, path: "M 755 315 L 765 315 L 765 325 L 755 325 Z" },
    
    // Япония
    "Япония": { x: 920, y: 230, path: "M 900 210 L 940 215 L 945 240 L 935 250 L 910 245 Z" },
    "Japan": { x: 920, y: 230, path: "M 900 210 L 940 215 L 945 240 L 935 250 L 910 245 Z" },
    
    // Тайвань
    "Тайвань": { x: 880, y: 270, path: "M 875 265 L 885 265 L 885 275 L 875 275 Z" },
    "Taiwan": { x: 880, y: 270, path: "M 875 265 L 885 265 L 885 275 L 875 275 Z" },
    
    // Кения
    "Кения": { x: 680, y: 300, path: "M 665 290 L 695 285 L 700 310 L 685 315 L 670 305 Z" },
    "Kenya": { x: 680, y: 300, path: "M 665 290 L 695 285 L 700 310 L 685 315 L 670 305 Z" },
    
    // Непал
    "Непал": { x: 780, y: 240, path: "M 775 235 L 785 235 L 785 245 L 775 245 Z" },
    "Nepal": { x: 780, y: 240, path: "M 775 235 L 785 235 L 785 245 L 775 245 Z" },
    
    // Вьетнам
    "Вьетнам": { x: 860, y: 280, path: "M 850 265 L 870 270 L 865 295 L 855 290 Z" },
    "Vietnam": { x: 860, y: 280, path: "M 850 265 L 870 270 L 865 295 L 855 290 Z" },
    
    // Грузия
    "Грузия": { x: 650, y: 180, path: "M 645 175 L 655 175 L 655 185 L 645 185 Z" },
    "Georgia": { x: 650, y: 180, path: "M 645 175 L 655 175 L 655 185 L 645 185 Z" },
    
    // Турция
    "Турция": { x: 600, y: 190, path: "M 580 180 L 620 175 L 625 205 L 590 200 Z" },
    "Turkey": { x: 600, y: 190, path: "M 580 180 L 620 175 L 625 205 L 590 200 Z" },
    
    // Индонезия
    "Индонезия": { x: 830, y: 320, path: "M 800 310 L 860 315 L 855 330 L 810 325 Z" },
    "Indonesia": { x: 830, y: 320, path: "M 800 310 L 860 315 L 855 330 L 810 325 Z" },
    
    // Бангладеш
    "Бангладеш": { x: 790, y: 270, path: "M 785 265 L 795 265 L 795 275 L 785 275 Z" },
    "Bangladesh": { x: 790, y: 270, path: "M 785 265 L 795 265 L 795 275 L 785 275 Z" },
};

let svgMap;
let activeCountryId = null;

document.addEventListener('DOMContentLoaded', function() {
    initSVGMap();
    initCountriesList();
});

function initSVGMap() {
    svgMap = document.getElementById('svgMap');
    if (!svgMap) return;
    
    // Рисуем континенты (упрощенные контуры)
    drawContinents();
    
    // Рисуем страны
    if (typeof countriesData !== 'undefined' && countriesData) {
        countriesData.forEach(country => {
            drawCountry(country);
        });
    }
}

function drawContinents() {
    // Азия (основной контур)
    const asia = document.createElementNS("http://www.w3.org/2000/svg", "path");
    asia.setAttribute("d", "M 500 100 L 950 120 L 980 350 L 950 380 L 700 360 L 600 300 L 550 250 L 500 200 Z");
    asia.setAttribute("fill", "#c5e1a5");
    asia.setAttribute("stroke", "#8bc34a");
    asia.setAttribute("stroke-width", "3");
    asia.setAttribute("opacity", "0.5");
    svgMap.appendChild(asia);
    
    // Африка
    const africa = document.createElementNS("http://www.w3.org/2000/svg", "path");
    africa.setAttribute("d", "M 550 250 L 650 240 L 680 350 L 650 400 L 580 390 L 550 320 Z");
    africa.setAttribute("fill", "#ffe082");
    africa.setAttribute("stroke", "#ffb300");
    africa.setAttribute("stroke-width", "2");
    africa.setAttribute("opacity", "0.5");
    svgMap.appendChild(africa);
}

function drawCountry(country) {
    const countryName = country.name;
    const pos = countryPositions[countryName] || countryPositions[country.name_en];
    
    if (!pos) {
        console.warn(`Позиция не найдена для страны: ${countryName}`);
        return;
    }
    
    // Рисуем контур страны
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pos.path);
    path.setAttribute("class", "country-path");
    path.setAttribute("data-country-id", country.id);
    path.setAttribute("data-country-name", countryName);
    
    // Добавляем обработчик клика
    path.addEventListener('click', function() {
        showCountryPopup(country);
        highlightCountry(country.id);
    });
    
    path.addEventListener('mouseenter', function() {
        path.style.fill = '#66bb6a';
    });
    
    path.addEventListener('mouseleave', function() {
        if (activeCountryId !== country.id) {
            path.style.fill = '#81c784';
        }
    });
    
    svgMap.appendChild(path);
    
    // Добавляем маркер (флаг или эмодзи)
    const marker = document.createElementNS("http://www.w3.org/2000/svg", "text");
    marker.setAttribute("x", pos.x);
    marker.setAttribute("y", pos.y - 10);
    marker.setAttribute("class", "country-marker");
    marker.textContent = country.flag || "🍃";
    marker.setAttribute("data-country-id", country.id);
    svgMap.appendChild(marker);
    
    // Добавляем название страны
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y + 5);
    label.setAttribute("class", "country-label");
    label.textContent = countryName;
    svgMap.appendChild(label);
}

function highlightCountry(countryId) {
    // Убираем подсветку с других стран
    document.querySelectorAll('.country-path').forEach(path => {
        if (parseInt(path.getAttribute('data-country-id')) !== countryId) {
            path.classList.remove('active');
            path.style.fill = '#81c784';
        }
    });
    
    // Подсвечиваем выбранную страну
    const activePath = document.querySelector(`.country-path[data-country-id="${countryId}"]`);
    if (activePath) {
        activePath.classList.add('active');
        activePath.style.fill = '#4caf50';
    }
    
    activeCountryId = countryId;
}

function showCountryPopup(country) {
    // Удаляем предыдущий попап, если есть
    const existingPopup = document.getElementById('countryPopup');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    // Создаем попап
    const popup = document.createElement('div');
    popup.id = 'countryPopup';
    popup.className = 'country-popup-svg';
    
    const regionsList = country.regions.map(region => 
        `<div class="region-popup-item" data-region-id="${region.id}">
            <strong>${region.name}</strong>
        </div>`
    ).join('');
    
    popup.innerHTML = `
        <div class="popup-content">
            <h3>${country.flag || '🌍'} ${country.name}</h3>
            <p>Чайных регионов: ${country.regions.length}</p>
            <div class="popup-regions">
                ${regionsList}
            </div>
            <button class="btn-view-catalog" data-country-id="${country.id}">
                Посмотреть все чаи
            </button>
        </div>
    `;
    
    document.querySelector('.map-container').appendChild(popup);
    
    // Обработчик клика на кнопку
    const catalogBtn = popup.querySelector('.btn-view-catalog');
    if (catalogBtn) {
        catalogBtn.addEventListener('click', function() {
            const countryId = this.getAttribute('data-country-id');
            window.location.href = `/catalog?country_id=${countryId}`;
        });
    }
    
    // Обработчики клика на регионы
    popup.querySelectorAll('.region-popup-item').forEach(item => {
        item.addEventListener('click', function() {
            const regionId = this.getAttribute('data-region-id');
            const countryId = country.id;
            window.location.href = `/catalog?country_id=${countryId}&region_id=${regionId}`;
        });
    });
}

function initCountriesList() {
    const countryItems = document.querySelectorAll('.country-item');
    
    countryItems.forEach(item => {
        item.addEventListener('click', function() {
            const countryId = parseInt(this.getAttribute('data-country-id'));
            const countryData = countriesData.find(c => c.id === countryId);
            
            if (countryData) {
                // Убираем активный класс со всех элементов
                countryItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');
                
                // Подсвечиваем страну на карте
                highlightCountry(countryId);
                
                // Показываем попап
                showCountryPopup(countryData);
            }
        });
    });
}









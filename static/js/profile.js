// Загрузка данных профиля и сборов
async function loadProfile() {
    try {
        // Загружаем информацию о пользователе
        const userResponse = await fetch('/api/me', {
            credentials: 'include'
        });
        
        if (!userResponse.ok) {
            if (userResponse.status === 401) {
                window.location.href = '/login?next=/profile';
                return;
            }
            throw new Error('Ошибка загрузки данных пользователя');
        }
        
        const user = await userResponse.json();
        
        // Заполняем информацию о пользователе
        document.getElementById('username').textContent = user.username || 'Не указано';
        document.getElementById('email').textContent = user.email || 'Не указано';
        document.getElementById('firstName').textContent = user.first_name || 'Не указано';
        document.getElementById('lastName').textContent = user.last_name || 'Не указано';
        
        // Загружаем заказы и сборы
        await loadOrders();
        await loadBlends();
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
        alert('Ошибка загрузки данных профиля');
    }
}

// Загрузка заказов пользователя
async function loadOrders() {
    const ordersList = document.getElementById('ordersList');
    
    try {
        const response = await fetch('/api/orders', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                ordersList.innerHTML = '<div class="error">Необходима авторизация</div>';
                return;
            }
            throw new Error('Ошибка загрузки заказов');
        }
        
        const data = await response.json();
        const orders = data.orders || [];
        
        if (orders.length === 0) {
            ordersList.innerHTML = `
                <div class="empty-orders">
                    <div class="empty-orders-icon">📦</div>
                    <div class="empty-orders-text">У вас пока нет заказов</div>
                    <a href="/catalog" class="empty-orders-link">Перейти в каталог</a>
                </div>
            `;
            // Скрываем кнопку, если заказов нет
            const toggleBtn = document.getElementById('toggleOrdersBtn');
            if (toggleBtn) {
                toggleBtn.style.display = 'none';
            }
            return;
        }
        
        // Показываем кнопку, если есть заказы
        const toggleBtn = document.getElementById('toggleOrdersBtn');
        if (toggleBtn) {
            toggleBtn.style.display = 'flex';
        }
        
        // Если заказов больше 2, сворачиваем список по умолчанию
        if (orders.length > 2) {
            ordersList.classList.add('orders-collapsed');
            const toggleText = document.getElementById('toggleOrdersText');
            const toggleIcon = document.getElementById('toggleOrdersIcon');
            if (toggleText) toggleText.textContent = 'Показать все';
            if (toggleIcon) toggleIcon.textContent = '▼';
        }
        
        // Отображаем заказы
        ordersList.innerHTML = orders.map(order => {
            const statusNames = {
                1: 'Ожидает оплаты',
                2: 'Оплачен',
                3: 'В обработке',
                4: 'Отправлен',
                5: 'Доставлен',
                6: 'Отменен',
                7: 'Возврат'
            };
            
            const statusColors = {
                1: '#ff9800',
                2: '#4caf50',
                3: '#2196f3',
                4: '#2196f3',
                5: '#4caf50',
                6: '#f44336',
                7: '#f44336'
            };
            
            const statusName = statusNames[order.status] || 'Неизвестно';
            const statusColor = statusColors[order.status] || '#666';
            
            const date = order.created_at ? new Date(order.created_at).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }) : '';
            
            const itemsHtml = order.items.map(item => {
                // Создаем ссылку на товар
                let productLink = '#';
                
                if (item.product_type === 'tea') {
                    // Проверяем, что slug существует и не пустой
                    if (item.product_slug && item.product_slug.trim() !== '') {
                        productLink = `/tea/${item.product_slug}`;
                    } else {
                        console.warn('Tea slug missing or empty for item:', item);
                    }
                } else if (item.product_type === 'blend' && item.product_id) {
                    productLink = `/blend/${item.product_id}`;
                }
                
                // Если есть ссылка, делаем название кликабельным
                const productNameHtml = productLink !== '#' 
                    ? `<a href="${productLink}" class="item-name-link">${escapeHtml(item.product_name)}</a>`
                    : `<span class="item-name">${escapeHtml(item.product_name)}</span>`;
                
                return `
                <div class="order-item-row">
                    ${productNameHtml}
                    <span class="item-quantity">${item.quantity}г (${item.size})</span>
                    <span class="item-price">${item.total_price.toFixed(2)} ₽</span>
                </div>
            `;
            }).join('');
            
            return `
                <div class="order-card">
                    <div class="order-header">
                        <div>
                            <h3 class="order-number">Заказ №${escapeHtml(order.order_number)}</h3>
                            <div class="order-date">${date}</div>
                        </div>
                        <div class="order-status" style="background-color: ${statusColor}20; color: ${statusColor}; border-color: ${statusColor};">
                            ${statusName}
                        </div>
                    </div>
                    <div class="order-items">
                        ${itemsHtml}
                    </div>
                    <div class="order-footer">
                        <div class="order-total">
                            <span>Итого:</span>
                            <span class="total-amount">${order.total_amount.toFixed(2)} ₽</span>
                        </div>
                        <div class="order-delivery">
                            <div>Доставка: ${order.delivery_city}</div>
                            <div>${order.delivery_address}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Ошибка загрузки заказов:', error);
        ordersList.innerHTML = '<div class="loading">Ошибка загрузки заказов</div>';
    }
}

// Загрузка сборов пользователя
async function loadBlends() {
    const blendsList = document.getElementById('blendsList');
    
    try {
        const response = await fetch('/api/profile/blends', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки сборов');
        }
        
        const data = await response.json();
        const blends = data.blends || [];
        
        if (blends.length === 0) {
            blendsList.innerHTML = `
                <div class="empty-blends">
                    <div class="empty-blends-icon">🍵</div>
                    <div class="empty-blends-text">У вас пока нет сохраненных сборов</div>
                    <a href="/blend-constructor" class="empty-blends-link">Создать первый сбор</a>
                </div>
            `;
            return;
        }
        
        // Отображаем сборы как кликабельные карточки
        blendsList.innerHTML = blends.map(blend => {
            const date = blend.created_at ? new Date(blend.created_at).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }) : '';
            
            const priceHtml = blend.price_per_100g ? `
                <div class="blend-price">
                    <span class="price-value">${blend.price_per_100g.toFixed(2)} ₽ / 100г</span>
                </div>
            ` : '';
            
            const baseInfo = blend.base_tea ? escapeHtml(blend.base_tea.name) : (blend.base_tea_type ? escapeHtml(blend.base_tea_type.name) : '');
            const description = blend.description ? escapeHtml(blend.description.substring(0, 100)) + (blend.description.length > 100 ? '...' : '') : '';
            
            return `
                <a href="/blend/${blend.id}" class="blend-card-link">
                    <div class="blend-card">
                        <div class="blend-header">
                            <h3 class="blend-name">${escapeHtml(blend.name)}</h3>
                            <div class="blend-date">${date}</div>
                        </div>
                        ${baseInfo ? `<p class="blend-base" style="font-size: 0.9rem; color: var(--text-secondary); margin: var(--spacing-xs) 0; font-style: italic;">Основа: ${baseInfo}</p>` : ''}
                        ${description ? `<p class="blend-description" style="color: var(--text-secondary); margin: var(--spacing-sm) 0; flex-grow: 1; font-size: 0.95rem; line-height: 1.5;">${description}</p>` : ''}
                        ${priceHtml}
                    </div>
                </a>
            `;
        }).join('');
    } catch (error) {
        console.error('Ошибка загрузки сборов:', error);
        blendsList.innerHTML = '<div class="loading">Ошибка загрузки сборов</div>';
    }
}

// Функция выхода
async function logout() {
    if (!confirm('Вы уверены, что хотите выйти?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка выхода');
        }
        
        // Перенаправляем на главную страницу
        window.location.href = '/';
    } catch (error) {
        console.error('Ошибка выхода:', error);
        alert('Ошибка выхода из аккаунта');
    }
}

// Экранирование HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadProfile();
    
    // Обработчик кнопки выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Обработчик кнопки сворачивания/разворачивания заказов
    const toggleOrdersBtn = document.getElementById('toggleOrdersBtn');
    if (toggleOrdersBtn) {
        toggleOrdersBtn.addEventListener('click', toggleOrders);
    }
});

function toggleOrders() {
    const ordersList = document.getElementById('ordersList');
    const toggleText = document.getElementById('toggleOrdersText');
    const toggleIcon = document.getElementById('toggleOrdersIcon');
    
    if (!ordersList) return;
    
    ordersList.classList.toggle('orders-collapsed');
    
    if (ordersList.classList.contains('orders-collapsed')) {
        toggleText.textContent = 'Показать все';
        toggleIcon.textContent = '▼';
    } else {
        toggleText.textContent = 'Скрыть';
        toggleIcon.textContent = '▲';
    }
}


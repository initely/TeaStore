// JavaScript для админ-панели

let currentPage = 1;
let currentStatusFilter = null;
let currentSearchQuery = '';
let currentOrderId = null;

const statusNames = {
    1: 'Ожидает оплаты',
    2: 'Оплачен',
    3: 'В обработке',
    4: 'Отправлен',
    5: 'Доставлен',
    6: 'Отменен',
    7: 'Возврат'
};

const statusClasses = {
    1: 'status-pending',
    2: 'status-paid',
    3: 'status-processing',
    4: 'status-shipped',
    5: 'status-delivered',
    6: 'status-cancelled',
    7: 'status-refunded'
};

document.addEventListener('DOMContentLoaded', function() {
    loadStatistics();
    loadOrders();
    
    // Обработчики событий
    document.getElementById('statusFilter').addEventListener('change', function() {
        currentStatusFilter = this.value ? parseInt(this.value) : null;
        currentPage = 1;
        loadOrders();
    });
    
    document.getElementById('searchInput').addEventListener('input', function() {
        currentSearchQuery = this.value.trim();
        currentPage = 1;
        loadOrders();
    });
    
    document.getElementById('refreshBtn').addEventListener('click', function() {
        loadStatistics();
        loadOrders();
    });
});

async function loadStatistics() {
    try {
        const response = await fetch('/api/admin/statistics', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login?next=/admin';
                return;
            }
            throw new Error('Ошибка загрузки статистики');
        }
        
        const data = await response.json();
        
        document.getElementById('statTotalOrders').textContent = data.orders.total;
        document.getElementById('statPendingOrders').textContent = data.orders.pending;
        document.getElementById('statRevenue').textContent = formatCurrency(data.revenue.total);
        document.getElementById('statUsers').textContent = data.users.total;
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

async function loadOrders() {
    const tbody = document.getElementById('ordersTableBody');
    tbody.innerHTML = '<tr><td colspan="7" class="loading">Загрузка заказов...</td></tr>';
    
    try {
        let url = `/api/admin/orders?page=${currentPage}&page_size=20`;
        if (currentStatusFilter) {
            url += `&status=${currentStatusFilter}`;
        }
        
        const response = await fetch(url, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                window.location.href = '/login?next=/admin';
                return;
            }
            throw new Error('Ошибка загрузки заказов');
        }
        
        const data = await response.json();
        const orders = data.orders;
        
        // Фильтрация по поисковому запросу
        let filteredOrders = orders;
        if (currentSearchQuery) {
            const query = currentSearchQuery.toLowerCase();
            filteredOrders = orders.filter(order => 
                order.order_number.toLowerCase().includes(query) ||
                order.user.email.toLowerCase().includes(query) ||
                order.user.username.toLowerCase().includes(query)
            );
        }
        
        if (filteredOrders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">Заказы не найдены</td></tr>';
            return;
        }
        
        tbody.innerHTML = filteredOrders.map(order => {
            const date = order.created_at ? new Date(order.created_at).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }) : '';
            
            return `
                <tr>
                    <td><span class="order-number">#${escapeHtml(order.order_number)}</span></td>
                    <td>
                        <div class="order-user">
                            <span class="order-user-name">${escapeHtml(order.user.username)}</span>
                            <span class="order-user-email">${escapeHtml(order.user.email)}</span>
                        </div>
                    </td>
                    <td><span class="order-date">${date}</span></td>
                    <td><span class="order-amount">${formatCurrency(order.total_amount)}</span></td>
                    <td><span class="order-status ${statusClasses[order.status]}">${statusNames[order.status]}</span></td>
                    <td><span class="order-delivery">${escapeHtml(order.delivery_city)}</span></td>
                    <td>
                        <div class="order-actions">
                            <button class="btn-action btn-view" onclick="viewOrderDetails(${order.id})">Детали</button>
                            <button class="btn-action btn-edit" onclick="openStatusModal(${order.id}, '${escapeHtml(order.order_number)}', ${order.status})">Изменить статус</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
        // Пагинация
        renderPagination(data.pagination);
        
    } catch (error) {
        console.error('Ошибка загрузки заказов:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="error">Ошибка загрузки заказов</td></tr>';
    }
}

function renderPagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    
    if (pagination.total_pages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Кнопка "Назад"
    html += `<button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} onclick="changePage(${currentPage - 1})">← Назад</button>`;
    
    // Номера страниц
    const maxPages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(pagination.total_pages, startPage + maxPages - 1);
    
    if (startPage > 1) {
        html += `<button class="pagination-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) {
            html += `<span class="pagination-info">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn" ${i === currentPage ? 'style="background: var(--primary-color); color: white;"' : ''} onclick="changePage(${i})">${i}</button>`;
    }
    
    if (endPage < pagination.total_pages) {
        if (endPage < pagination.total_pages - 1) {
            html += `<span class="pagination-info">...</span>`;
        }
        html += `<button class="pagination-btn" onclick="changePage(${pagination.total_pages})">${pagination.total_pages}</button>`;
    }
    
    // Кнопка "Вперед"
    html += `<button class="pagination-btn" ${currentPage === pagination.total_pages ? 'disabled' : ''} onclick="changePage(${currentPage + 1})">Вперед →</button>`;
    
    html += `<span class="pagination-info">Страница ${currentPage} из ${pagination.total_pages} (${pagination.total} заказов)</span>`;
    
    paginationEl.innerHTML = html;
}

function changePage(page) {
    currentPage = page;
    loadOrders();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function openStatusModal(orderId, orderNumber, currentStatus) {
    currentOrderId = orderId;
    document.getElementById('modalOrderNumber').textContent = orderNumber;
    document.getElementById('newStatus').value = currentStatus;
    document.getElementById('statusModal').classList.add('active');
}

function closeStatusModal() {
    document.getElementById('statusModal').classList.remove('active');
    currentOrderId = null;
}

async function saveOrderStatus() {
    if (!currentOrderId) return;
    
    const newStatus = parseInt(document.getElementById('newStatus').value);
    
    try {
        const response = await fetch(`/api/admin/orders/${currentOrderId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ status: newStatus })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка обновления статуса');
        }
        
        const data = await response.json();
        
        closeStatusModal();
        loadStatistics();
        loadOrders();
        
        showNotification('Статус заказа успешно обновлен', 'success');
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
        showNotification('Ошибка обновления статуса: ' + error.message, 'error');
    }
}

async function viewOrderDetails(orderId) {
    const modal = document.getElementById('orderDetailsModal');
    const content = document.getElementById('orderDetailsContent');
    content.innerHTML = '<div class="loading">Загрузка деталей заказа...</div>';
    modal.classList.add('active');
    
    try {
        const response = await fetch(`/api/admin/orders?page=1&page_size=100`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки деталей заказа');
        }
        
        const data = await response.json();
        const order = data.orders.find(o => o.id === orderId);
        
        if (!order) {
            content.innerHTML = '<div class="error">Заказ не найден</div>';
            return;
        }
        
        const date = order.created_at ? new Date(order.created_at).toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }) : '';
        
        const itemsHtml = order.items.map(item => `
            <div class="order-item-detail">
                <span class="order-item-name">${escapeHtml(item.product_name)}</span>
                <span class="order-item-quantity">${item.quantity}г (${item.size})</span>
                <span class="order-item-price">${formatCurrency(item.total_price)}</span>
            </div>
        `).join('');
        
        content.innerHTML = `
            <div class="order-details">
                <div class="order-details-section">
                    <h3>Информация о заказе</h3>
                    <div class="order-details-item">
                        <span class="order-details-label">Номер заказа:</span>
                        <span class="order-details-value">#${escapeHtml(order.order_number)}</span>
                    </div>
                    <div class="order-details-item">
                        <span class="order-details-label">Дата создания:</span>
                        <span class="order-details-value">${date}</span>
                    </div>
                    <div class="order-details-item">
                        <span class="order-details-label">Статус:</span>
                        <span class="order-details-value"><span class="order-status ${statusClasses[order.status]}">${statusNames[order.status]}</span></span>
                    </div>
                    <div class="order-details-item">
                        <span class="order-details-label">Общая сумма:</span>
                        <span class="order-details-value">${formatCurrency(order.total_amount)}</span>
                    </div>
                    <div class="order-details-item">
                        <span class="order-details-label">Стоимость доставки:</span>
                        <span class="order-details-value">${formatCurrency(order.shipping_cost)}</span>
                    </div>
                </div>
                
                <div class="order-details-section">
                    <h3>Покупатель</h3>
                    <div class="order-details-item">
                        <span class="order-details-label">Имя пользователя:</span>
                        <span class="order-details-value">${escapeHtml(order.user.username)}</span>
                    </div>
                    <div class="order-details-item">
                        <span class="order-details-label">Email:</span>
                        <span class="order-details-value">${escapeHtml(order.user.email)}</span>
                    </div>
                </div>
                
                <div class="order-details-section">
                    <h3>Доставка</h3>
                    <div class="order-details-item">
                        <span class="order-details-label">Город:</span>
                        <span class="order-details-value">${escapeHtml(order.delivery_city)}</span>
                    </div>
                    <div class="order-details-item">
                        <span class="order-details-label">Адрес:</span>
                        <span class="order-details-value">${escapeHtml(order.delivery_address)}</span>
                    </div>
                    ${order.delivery_postal_code ? `
                    <div class="order-details-item">
                        <span class="order-details-label">Почтовый индекс:</span>
                        <span class="order-details-value">${escapeHtml(order.delivery_postal_code)}</span>
                    </div>
                    ` : ''}
                    ${order.delivery_phone ? `
                    <div class="order-details-item">
                        <span class="order-details-label">Телефон:</span>
                        <span class="order-details-value">${escapeHtml(order.delivery_phone)}</span>
                    </div>
                    ` : ''}
                </div>
                
                <div class="order-details-section">
                    <h3>Товары</h3>
                    <div class="order-items-list">
                        ${itemsHtml}
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка загрузки деталей заказа:', error);
        content.innerHTML = '<div class="error">Ошибка загрузки деталей заказа</div>';
    }
}

function closeOrderDetailsModal() {
    document.getElementById('orderDetailsModal').classList.remove('active');
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Простое уведомление через alert, можно заменить на более красивое
    if (type === 'success') {
        alert('✓ ' + message);
    } else if (type === 'error') {
        alert('✗ ' + message);
    } else {
        alert(message);
    }
}

// Закрытие модальных окон при клике вне их
window.onclick = function(event) {
    const statusModal = document.getElementById('statusModal');
    const orderDetailsModal = document.getElementById('orderDetailsModal');
    
    if (event.target === statusModal) {
        closeStatusModal();
    }
    if (event.target === orderDetailsModal) {
        closeOrderDetailsModal();
    }
}





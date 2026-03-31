// JavaScript для страницы корзины

let cartData = [];

// Загрузка корзины
async function loadCart() {
    const cartContent = document.getElementById('cartContent');
    
    try {
        const response = await fetch('/api/cart', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки корзины');
        }
        
        const data = await response.json();
        cartData = data.cart || [];
        
        renderCart(cartData, data.total);
        updateCartBadge(data.count);
    } catch (error) {
        console.error('Ошибка загрузки корзины:', error);
        cartContent.innerHTML = '<div class="error">Ошибка загрузки корзины</div>';
    }
}

// Отображение корзины
function renderCart(cart, total) {
    const cartContent = document.getElementById('cartContent');
    
    if (!cart || cart.length === 0) {
        cartContent.innerHTML = `
            <div class="empty-cart">
                <div class="empty-cart-icon">🛒</div>
                <h2>Ваша корзина пуста</h2>
                <p>Добавьте товары из каталога</p>
                <a href="/catalog" class="btn btn-primary">Перейти в каталог</a>
            </div>
        `;
        return;
    }
    
    const itemsHtml = cart.map((item, index) => {
        const itemTotal = (item.price * item.quantity).toFixed(2);
        const productUrl = item.product_type === 'tea' 
            ? `/tea/${item.slug || item.product_id}` 
            : `/blend/${item.product_id}`;
        
        return `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h3><a href="${productUrl}">${escapeHtml(item.name)}</a></h3>
                    <div class="cart-item-meta">
                        <span class="item-type">${item.product_type === 'tea' ? 'Чай' : 'Сбор'}</span>
                        <span class="item-size">${item.size}</span>
                    </div>
                </div>
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <span class="quantity-label">Кол-во:</span>
                        <button class="qty-btn" onclick="updateQuantity(${index}, ${item.quantity - 1})">-</button>
                        <input type="number" class="qty-input" value="${item.quantity}" 
                               min="1" onchange="updateQuantity(${index}, parseInt(this.value))">
                        <button class="qty-btn" onclick="updateQuantity(${index}, ${item.quantity + 1})">+</button>
                        <span class="quantity-unit">шт.</span>
                    </div>
                    <div class="cart-item-price">
                        ${itemTotal} ₽
                    </div>
                    <button class="remove-btn" onclick="removeItem(${index})" title="Удалить">×</button>
                </div>
            </div>
        `;
    }).join('');
    
    cartContent.innerHTML = `
        <div class="cart-items">
            ${itemsHtml}
        </div>
        <div class="cart-summary">
            <div class="summary-row">
                <span>Товаров:</span>
                <span>${cart.length}</span>
            </div>
            <div class="summary-row total">
                <span>Итого:</span>
                <span class="total-price">${total.toFixed(2)} ₽</span>
            </div>
            <a href="/checkout" class="btn btn-primary btn-large">Оформить заказ</a>
            <a href="/catalog" class="btn btn-outline">Продолжить покупки</a>
        </div>
    `;
}

// Обновление количества
async function updateQuantity(index, newQuantity) {
    if (newQuantity < 1) {
        removeItem(index);
        return;
    }
    
    try {
        const response = await fetch(`/api/cart/update?index=${index}&quantity=${newQuantity}`, {
            method: 'PUT',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка обновления корзины');
        }
        
        await loadCart();
    } catch (error) {
        console.error('Ошибка обновления количества:', error);
        alert('Ошибка обновления количества');
    }
}

// Удаление товара
async function removeItem(index) {
    if (!confirm('Удалить товар из корзины?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/cart/remove?index=${index}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка удаления товара');
        }
        
        await loadCart();
        showNotification('Товар удален из корзины');
    } catch (error) {
        console.error('Ошибка удаления товара:', error);
        alert('Ошибка удаления товара');
    }
}

// Обновление бейджа корзины в header
function updateCartBadge(count) {
    const badge = document.querySelector('.cart-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
        // Для однозначных чисел делаем круглым, для двузначных - скругленным прямоугольником
        if (count > 0 && count < 10) {
            badge.style.width = '20px';
            badge.style.padding = '0';
            badge.style.borderRadius = '50%';
        } else if (count >= 10) {
            badge.style.width = 'auto';
            badge.style.padding = '0 6px';
            badge.style.borderRadius = '12px';
        }
    }
}

// Уведомление
function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4caf50;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Экранирование HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    loadCart();
});


// Общие функции для работы с корзиной

// Добавление товара в корзину
window.addToCart = async function(productId, size, productType = 'tea') {
    const quantity = 1; // количество единиц товара (1 пакет указанного размера)
    const sizeStr = size === 20 ? '20g' : '100g';
    
    try {
        const response = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                product_type: productType,
                product_id: productId,
                quantity: quantity,
                size: sizeStr,
            }),
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`${productType === 'tea' ? 'Чай' : 'Сбор'} добавлен в корзину (${sizeStr})!`);
            // Обновляем бейдж, перезагружая корзину для получения актуального количества
            await updateCartBadge();
        } else {
            let errorMessage = 'Ошибка добавления в корзину';
            if (result.detail) {
                errorMessage = typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail);
            }
            alert(errorMessage);
        }
    } catch (error) {
        console.error('Ошибка добавления в корзину:', error);
        alert('Произошла ошибка при добавлении в корзину');
    }
}

// Обновление бейджа корзины в header
async function updateCartBadge(count = null) {
    if (count === null) {
        // Загружаем количество из API
        try {
            const response = await fetch('/api/cart', {
                credentials: 'include'
            });
            if (response.ok) {
                const data = await response.json();
                count = data.count || 0;
            }
        } catch (error) {
            console.error('Ошибка загрузки корзины:', error);
            return;
        }
    }
    
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

// Инициализация бейджа корзины при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    updateCartBadge();
});


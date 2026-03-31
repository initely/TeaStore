// JavaScript для страницы оформления заказа

// Загрузка корзины для отображения в заказе
async function loadOrderSummary() {
    const orderSummary = document.getElementById('orderSummary');
    
    try {
        const response = await fetch('/api/cart', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Ошибка загрузки корзины');
        }
        
        const data = await response.json();
        const cart = data.cart || [];
        const total = data.total || 0;
        const shipping = 300; // Стоимость доставки
        const finalTotal = total + shipping;
        
        if (cart.length === 0) {
            orderSummary.innerHTML = '<div class="error">Корзина пуста</div>';
            return;
        }
        
        const itemsHtml = cart.map(item => {
            const itemTotal = (item.price * item.quantity).toFixed(2);
            return `
                <div class="order-item">
                    <div class="order-item-name">${escapeHtml(item.name)}</div>
                    <div class="order-item-details">
                        <span>${item.size}</span>
                        <span>× ${item.quantity} шт.</span>
                    </div>
                    <div class="order-item-price">${itemTotal} ₽</div>
                </div>
            `;
        }).join('');
        
        orderSummary.innerHTML = `
            <div class="order-items">
                ${itemsHtml}
            </div>
            <div class="order-totals">
                <div class="total-row">
                    <span>Товары:</span>
                    <span>${total.toFixed(2)} ₽</span>
                </div>
                <div class="total-row">
                    <span>Доставка:</span>
                    <span>${shipping.toFixed(2)} ₽</span>
                </div>
                <div class="total-row final">
                    <span>Итого:</span>
                    <span class="final-total">${finalTotal.toFixed(2)} ₽</span>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Ошибка загрузки корзины:', error);
        orderSummary.innerHTML = '<div class="error">Ошибка загрузки корзины</div>';
    }
}

// Оформление заказа
async function submitOrder(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Очистка предыдущих ошибок
    clearErrors();
    
    const delivery_address = (formData.get('delivery_address') || '').trim();
    const delivery_city = (formData.get('delivery_city') || '').trim();
    const delivery_postal_code = (formData.get('delivery_postal_code') || '').trim() || null;
    const delivery_phone = (formData.get('delivery_phone') || '').trim();
    const notes = (formData.get('notes') || '').trim() || null;
    
    let hasErrors = false;
    
    // Валидация города
    if (!delivery_city) {
        showFieldError('deliveryCity', 'Укажите город доставки');
        hasErrors = true;
    } else if (delivery_city.length < 2) {
        showFieldError('deliveryCity', 'Название города слишком короткое');
        hasErrors = true;
    }
    
    // Валидация адреса
    if (!delivery_address) {
        showFieldError('deliveryAddress', 'Укажите адрес доставки');
        hasErrors = true;
    } else if (delivery_address.length < 10) {
        showFieldError('deliveryAddress', 'Адрес должен содержать улицу, дом и квартиру');
        hasErrors = true;
    }
    
    // Валидация телефона
    if (!delivery_phone) {
        showFieldError('deliveryPhone', 'Укажите номер телефона');
        hasErrors = true;
    } else {
        // Простая проверка формата телефона (только цифры, +, пробелы, скобки, дефисы)
        const phoneRegex = /^[\d\s\+\-\(\)]+$/;
        if (!phoneRegex.test(delivery_phone) || delivery_phone.replace(/\D/g, '').length < 10) {
            showFieldError('deliveryPhone', 'Укажите корректный номер телефона');
            hasErrors = true;
        }
    }
    
    // Валидация почтового индекса (если указан)
    if (delivery_postal_code) {
        const postalRegex = /^\d{5,6}$/;
        if (!postalRegex.test(delivery_postal_code)) {
            showFieldError('deliveryPostalCode', 'Почтовый индекс должен содержать 5-6 цифр');
            hasErrors = true;
        }
    }
    
    if (hasErrors) {
        return;
    }
    
    const orderData = {
        delivery_address: delivery_address,
        delivery_city: delivery_city,
        delivery_postal_code: delivery_postal_code,
        delivery_phone: delivery_phone,
        notes: notes,
    };
    
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Оформление...';
    
    try {
        const response = await fetch('/api/orders/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(orderData),
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // После создания заказа переводим на страницу оплаты
            window.location.href = `/payment/${result.order_id}`;
        } else {
            // Ошибка
            let errorMessage = 'Ошибка оформления заказа';
            if (result.detail) {
                if (Array.isArray(result.detail)) {
                    // Обработка ошибок валидации Pydantic
                    result.detail.forEach(error => {
                        const fieldName = error.loc && error.loc.length > 1 ? error.loc[error.loc.length - 1] : null;
                        if (fieldName) {
                            const fieldMap = {
                                'delivery_address': 'deliveryAddress',
                                'delivery_city': 'deliveryCity',
                                'delivery_postal_code': 'deliveryPostalCode',
                                'delivery_phone': 'deliveryPhone',
                            };
                            const fieldId = fieldMap[fieldName] || fieldName;
                            showFieldError(fieldId, error.msg || 'Проверьте правильность заполнения поля');
                        }
                    });
                    errorMessage = 'Пожалуйста, исправьте ошибки в форме';
                } else {
                    errorMessage = typeof result.detail === 'string' ? result.detail : JSON.stringify(result.detail);
                }
            }
            if (!Array.isArray(result.detail)) {
                alert(errorMessage);
            }
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('Ошибка оформления заказа:', error);
        alert('Произошла ошибка при оформлении заказа');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// Показать ошибку поля
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (!field) return;
    
    // Удаляем предыдущую ошибку
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Добавляем класс ошибки
    field.classList.add('error-field');
    
    // Создаем элемент с ошибкой
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    field.parentElement.appendChild(errorDiv);
}

// Очистить все ошибки
function clearErrors() {
    document.querySelectorAll('.field-error').forEach(el => el.remove());
    document.querySelectorAll('.error-field').forEach(el => el.classList.remove('error-field'));
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
    loadOrderSummary();
    
    const form = document.getElementById('checkoutForm');
    if (form) {
        form.addEventListener('submit', submitOrder);
    }
});


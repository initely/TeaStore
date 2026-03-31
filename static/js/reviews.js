// JavaScript для работы с отзывами

async function loadReviews(productType, productId) {
    const reviewsList = document.getElementById('reviewsList');
    const reviewFormContainer = document.getElementById('reviewFormContainer');
    
    if (!reviewsList || !reviewFormContainer) return;
    
    try {
        // Загружаем отзывы
        const response = await fetch(`/api/reviews/${productType}/${productId}`, {
            credentials: 'include',
        });
        if (!response.ok) {
            throw new Error(`Ошибка ${response.status}`);
        }
        
        const data = await response.json();
        
        // Отладочный вывод
        console.log('Reviews data:', data);
        console.log('is_authenticated:', data.is_authenticated);
        console.log('user_has_review:', data.user_has_review);
        console.log('can_review:', data.can_review);
        
        // Отображаем отзывы
        if (data.reviews && data.reviews.length > 0) {
            reviewsList.innerHTML = data.reviews.map(review => createReviewHTML(review)).join('');
        } else {
            reviewsList.innerHTML = '<p class="text-secondary">Пока нет отзывов. Будьте первым!</p>';
        }
        
        // Показываем форму только если пользователь может оставить отзыв и еще не оставил
        const reviewFormContainer = document.getElementById('reviewFormContainer');
        if (reviewFormContainer) {
            // Проверяем авторизацию - если is_authenticated явно true, значит авторизован
            const isAuthenticated = data.is_authenticated === true;
            
            if (!isAuthenticated) {
                // Если пользователь не авторизован
                reviewFormContainer.innerHTML = `
                    <div class="review-form-container">
                        <p class="text-secondary">Войдите, чтобы оставить отзыв</p>
                    </div>
                `;
            } else if (data.user_has_review) {
                // Если пользователь уже оставил отзыв
                reviewFormContainer.innerHTML = `
                    <div class="review-form-container">
                        <p class="text-secondary">Вы уже оставили отзыв на этот товар</p>
                    </div>
                `;
            } else if (data.can_review) {
                // Если пользователь может оставить отзыв (есть доставленный заказ)
                showReviewForm(productType, productId);
            } else {
                // Если пользователь не может оставить отзыв (нет доставленного заказа)
                reviewFormContainer.innerHTML = `
                    <div class="review-form-container">
                        <p class="text-secondary">Вы можете оставить отзыв только на товары, которые вы получили (заказ доставлен)</p>
                    </div>
                `;
            }
        }
        
    } catch (error) {
        console.error('Ошибка загрузки отзывов:', error);
        reviewsList.innerHTML = '<p class="error-message">Ошибка загрузки отзывов</p>';
    }
}

function createReviewHTML(review) {
    const date = review.created_at ? new Date(review.created_at).toLocaleDateString('ru-RU') : '';
    const stars = '⭐'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
    
    return `
        <div class="review-item">
            <div class="review-header">
                <div class="review-user">
                    <strong>${escapeHtml(review.user.username)}</strong>
                    <span class="review-date">${date}</span>
                </div>
                <div class="review-rating">${stars}</div>
            </div>
            ${review.title ? `<h4 class="review-title">${escapeHtml(review.title)}</h4>` : ''}
            ${review.text ? `<p class="review-text">${escapeHtml(review.text)}</p>` : ''}
        </div>
    `;
}

async function showReviewForm(productType, productId) {
    const reviewFormContainer = document.getElementById('reviewFormContainer');
    if (!reviewFormContainer) return;
    
    // Показываем форму (проверка авторизации и возможности оставить отзыв уже выполнена в loadReviews)
    reviewFormContainer.innerHTML = `
            <div class="review-form-container">
                <h3>Оставить отзыв</h3>
                <form id="reviewForm">
                    <div class="form-group">
                        <label>Оценка *</label>
                        <div class="rating-input">
                            <input type="radio" name="rating" value="5" id="rating5_${productId}" required>
                            <label for="rating5_${productId}">☆</label>
                            <input type="radio" name="rating" value="4" id="rating4_${productId}" required>
                            <label for="rating4_${productId}">☆</label>
                            <input type="radio" name="rating" value="3" id="rating3_${productId}" required>
                            <label for="rating3_${productId}">☆</label>
                            <input type="radio" name="rating" value="2" id="rating2_${productId}" required>
                            <label for="rating2_${productId}">☆</label>
                            <input type="radio" name="rating" value="1" id="rating1_${productId}" required>
                            <label for="rating1_${productId}">☆</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="reviewText_${productId}">Текст отзыва (необязательно)</label>
                        <textarea id="reviewText_${productId}" name="text" rows="4" placeholder="Поделитесь своими впечатлениями"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Отправить отзыв</button>
                    <div id="reviewError_${productId}" class="error-message" style="display: none;"></div>
                </form>
            </div>
        `;
        
        // Добавляем обработчик формы
        const form = document.getElementById('reviewForm');
        if (form) {
            form.addEventListener('submit', (e) => submitReview(e, productType, productId));
            
            // Добавляем обработчики для визуального отображения выбранной оценки
            const ratingInputs = form.querySelectorAll('input[name="rating"]');
            const labels = form.querySelectorAll('.rating-input label');
            
            // Функция для обновления звездочек
            const updateStars = (selectedRating) => {
                labels.forEach((label, index) => {
                    const ratingValue = 5 - index; // Обратный порядок из-за flex-direction: row-reverse
                    if (ratingValue <= selectedRating) {
                        label.textContent = '⭐';
                    } else {
                        label.textContent = '☆';
                    }
                });
            };
            
            ratingInputs.forEach(input => {
                input.addEventListener('change', function() {
                    const selectedRating = parseInt(this.value);
                    updateStars(selectedRating);
                });
                
                // Обновляем при наведении
                const label = form.querySelector(`label[for="${input.id}"]`);
                if (label) {
                    label.addEventListener('mouseenter', function() {
                        const ratingValue = parseInt(input.value);
                        updateStars(ratingValue);
                    });
                }
            });
            
            // Сбрасываем звездочки при уходе мыши (если ничего не выбрано)
            const ratingInputContainer = form.querySelector('.rating-input');
            if (ratingInputContainer) {
                ratingInputContainer.addEventListener('mouseleave', function() {
                    const selectedInput = form.querySelector('input[name="rating"]:checked');
                    if (selectedInput) {
                        updateStars(parseInt(selectedInput.value));
                    } else {
                        updateStars(0);
                    }
                });
            }
        }
}

async function submitReview(event, productType, productId) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const rating = parseInt(formData.get('rating'));
    const title = formData.get('title') || null;
    const text = formData.get('text') || null;
    
    const errorDiv = document.getElementById(`reviewError_${productId}`);
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Блокируем кнопку во время отправки
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Отправка...';
    }
    
    try {
        const response = await fetch('/api/reviews', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                product_type: productType,
                product_id: productId,
                rating: rating,
                title: title,
                text: text,
            }),
        });
        
        // Проверяем Content-Type перед парсингом JSON
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            // Если ответ не JSON, читаем как текст
            const text = await response.text();
            console.error('Неожиданный ответ от сервера:', text);
            throw new Error('Ошибка при отправке отзыва. Попробуйте позже.');
        }
        
        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при отправке отзыва');
        }
        
        // Перезагружаем отзывы (форма автоматически скроется, так как user_has_review будет true)
        await loadReviews(productType, productId);
        
        // Показываем сообщение об успехе
        const reviewFormContainer = document.getElementById('reviewFormContainer');
        if (reviewFormContainer) {
            const successMsg = document.createElement('div');
            successMsg.className = 'success-message';
            successMsg.textContent = 'Отзыв успешно добавлен!';
            successMsg.style.display = 'block';
            successMsg.style.marginBottom = 'var(--spacing-md)';
            reviewFormContainer.insertBefore(successMsg, reviewFormContainer.firstChild);
            setTimeout(() => {
                successMsg.remove();
            }, 3000);
        }
        
    } catch (error) {
        console.error('Ошибка отправки отзыва:', error);
        if (errorDiv) {
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
        }
    } finally {
        // Разблокируем кнопку
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Отправить отзыв';
        }
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


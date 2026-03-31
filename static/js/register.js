// JavaScript для страницы регистрации

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('errorMessage');
    
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const first_name = document.getElementById('first_name').value.trim() || null;
        const last_name = document.getElementById('last_name').value.trim() || null;
        
        // Валидация
        if (password.length < 6) {
            errorMessage.textContent = 'Пароль должен быть не менее 6 символов';
            errorMessage.style.display = 'block';
            return;
        }
        
        // Скрываем предыдущие ошибки
        errorMessage.style.display = 'none';
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Важно: отправляем и получаем cookies
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password,
                    first_name: first_name,
                    last_name: last_name,
                }),
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('Регистрация успешна!', result);
                console.log('Cookies после регистрации:', document.cookie);
                
                // Успешная регистрация - проверяем, откуда пришли
                const urlParams = new URLSearchParams(window.location.search);
                let nextUrl = urlParams.get('next') || '/';
                
                // Если нужно восстановить сбор, добавляем параметр
                if (urlParams.get('restore') === 'true' && nextUrl === '/blend-constructor') {
                    nextUrl += '?restored=true';
                }
                
                // Небольшая задержка, чтобы cookie успел установиться
                setTimeout(() => {
                    window.location.href = nextUrl;
                }, 100);
            } else {
                // Показываем ошибку
                errorMessage.textContent = result.detail || 'Ошибка при регистрации';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('Ошибка при регистрации:', error);
            errorMessage.textContent = 'Произошла ошибка при регистрации. Попробуйте еще раз.';
            errorMessage.style.display = 'block';
        }
    });
});


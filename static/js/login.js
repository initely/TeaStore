// JavaScript для страницы входа

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        // Скрываем предыдущие ошибки
        errorMessage.style.display = 'none';
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Важно: отправляем и получаем cookies
                body: JSON.stringify({
                    email: email,
                    password: password,
                }),
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('Вход успешен!', result);
                console.log('Cookies после входа:', document.cookie);
                
                // Успешный вход - проверяем, откуда пришли
                const urlParams = new URLSearchParams(window.location.search);
                let nextUrl = urlParams.get('next') || '/';
                
                // Если нужно восстановить сбор, добавляем параметр
                if (urlParams.get('restore') === 'true' && nextUrl === '/blend-constructor') {
                    nextUrl += '?restored=true';
                }
                
                // Редирект - cookie должен установиться браузером после получения ответа
                window.location.href = nextUrl;
            } else {
                // Показываем ошибку
                errorMessage.textContent = result.detail || 'Ошибка при входе';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('Ошибка при входе:', error);
            errorMessage.textContent = 'Произошла ошибка при входе. Попробуйте еще раз.';
            errorMessage.style.display = 'block';
        }
    });
});


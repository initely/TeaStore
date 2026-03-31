// JavaScript для отображения статуса авторизации в header

document.addEventListener('DOMContentLoaded', async function () {
    await updateAuthStatus();
});

async function updateAuthStatus() {
    const authButton = document.getElementById('authButton');
    const userInfo = document.getElementById('userInfo');

    if (!authButton && !userInfo) return;

    try {
        const response = await fetch('/api/me', {
            method: 'GET',
            credentials: 'include',
        });

        if (response.ok) {
            const user = await response.json();
            // Пользователь авторизован
            if (authButton) {
                authButton.style.display = 'none';
            }
            if (userInfo) {
                userInfo.style.display = 'flex';
                const usernameElement = userInfo.querySelector('.username');
                if (usernameElement) {
                    usernameElement.textContent = user.username || user.email;
                }
            }
            // Показываем ссылку на админ-панель для администраторов
            const adminLink = document.getElementById('adminLink');
            if (adminLink && user.is_admin) {
                adminLink.style.display = 'inline-flex';
            } else if (adminLink) {
                adminLink.style.display = 'none';
            }
        } else {
            // Пользователь не авторизован
            if (authButton) {
                authButton.style.display = 'inline-flex';
                if (!authButton.querySelector('.auth-icon')) {
                    authButton.innerHTML = '<span class="auth-text">Войти / Зарегистрироваться</span><span class="auth-icon">👤</span>';
                }
            }
            if (userInfo) {
                userInfo.style.display = 'none';
            }
            // Скрываем ссылку на админ-панель
            const adminLink = document.getElementById('adminLink');
            if (adminLink) {
                adminLink.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Ошибка при проверке статуса авторизации:', error);
        // В случае ошибки показываем кнопку входа
        if (authButton) {
            authButton.style.display = 'inline-flex';
            if (!authButton.querySelector('.auth-icon')) {
                authButton.innerHTML = '<span class="auth-text">Войти / Зарегистрироваться</span><span class="auth-icon">👤</span>';
            }
        }
        if (userInfo) {
            userInfo.style.display = 'none';
        }
        // Скрываем ссылку на админ-панель
        const adminLink = document.getElementById('adminLink');
        if (adminLink) {
            adminLink.style.display = 'none';
        }
    }
}


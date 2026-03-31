// JavaScript для mock-оплаты заказа

let statusInterval = null;
let activeMethod = "sbp";

function setStatus(text, type = "neutral") {
    const statusEl = document.getElementById("paymentStatus");
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.className = `payment-status payment-status-${type}`;
}

function showSuccess() {
    const successBlock = document.getElementById("paymentSuccess");
    if (successBlock) successBlock.style.display = "block";
    setStatus("Оплата подтверждена", "success");
    setTimeout(() => {
        window.location.href = "/profile";
    }, 1200);
}

async function pollPaymentStatus(orderId) {
    clearInterval(statusInterval);
    statusInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/payment/${orderId}/status`, { credentials: "include" });
            const result = await response.json();
            if (!response.ok) return;
            if (result.status === "paid") {
                clearInterval(statusInterval);
                showSuccess();
            }
        } catch (error) {
            console.error("Ошибка проверки статуса оплаты:", error);
        }
    }, 1000);
}

async function startPayment(method, orderId) {
    try {
        const response = await fetch(`/api/payment/${orderId}/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ method }),
        });
        const result = await response.json();

        if (!response.ok) {
            setStatus(result.detail || "Ошибка запуска оплаты", "error");
            return;
        }

        const sbpBlock = document.getElementById("sbpBlock");
        if (method === "sbp") {
            sbpBlock.style.display = "block";
            setStatus("Сканируйте QR-код и подтвердите платеж в приложении банка", "neutral");
            pollPaymentStatus(orderId);
            return;
        }

        sbpBlock.style.display = "none";
        showSuccess();
    } catch (error) {
        console.error("Ошибка запуска оплаты:", error);
        setStatus("Произошла ошибка при запуске оплаты", "error");
    }
}

function setMethod(method) {
    activeMethod = method;
    const map = {
        sbp: "sbpPanel",
        card: "cardPanel",
    };
    document.querySelectorAll(".payment-method-btn").forEach((btn) => {
        btn.classList.toggle("is-active", btn.getAttribute("data-method") === method);
    });
    Object.keys(map).forEach((key) => {
        const panel = document.getElementById(map[key]);
        if (panel) panel.style.display = key === method ? "block" : "none";
    });
    setStatus("Выберите данные и подтвердите оплату", "neutral");
}

function setupCardMasks() {
    const number = document.getElementById("cardNumber");
    const expiry = document.getElementById("cardExpiry");
    const cvv = document.getElementById("cardCvv");

    if (number) {
        number.addEventListener("input", () => {
            let raw = number.value.replace(/\D/g, "").slice(0, 16);
            number.value = raw.replace(/(\d{4})(?=\d)/g, "$1 ").trim();
        });
    }

    if (expiry) {
        expiry.addEventListener("input", () => {
            let raw = expiry.value.replace(/\D/g, "").slice(0, 4);
            if (raw.length >= 3) {
                raw = `${raw.slice(0, 2)}/${raw.slice(2)}`;
            }
            expiry.value = raw;
        });
    }

    if (cvv) {
        cvv.addEventListener("input", () => {
            cvv.value = cvv.value.replace(/\D/g, "").slice(0, 3);
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const paymentShell = document.querySelector(".payment-shell[data-order-id]");
    if (!paymentShell) return;

    const orderId = paymentShell.getAttribute("data-order-id");
    const methodButtons = document.querySelectorAll(".payment-method-btn");
    const bankButtons = document.querySelectorAll(".bank-btn");
    const sbpPayBtn = document.getElementById("sbpPayBtn");
    const cardPayBtn = document.getElementById("cardPayBtn");

    methodButtons.forEach((button) => {
        button.addEventListener("click", () => {
            setMethod(button.getAttribute("data-method"));
        });
    });

    bankButtons.forEach((button) => {
        button.addEventListener("click", () => {
            bankButtons.forEach((el) => el.classList.remove("is-selected"));
            button.classList.add("is-selected");
        });
    });

    if (sbpPayBtn) {
        sbpPayBtn.addEventListener("click", () => startPayment("sbp", orderId));
    }

    if (cardPayBtn) {
        cardPayBtn.addEventListener("click", () => {
            const number = (document.getElementById("cardNumber")?.value || "").replace(/\s/g, "");
            const expiry = document.getElementById("cardExpiry")?.value || "";
            const cvv = document.getElementById("cardCvv")?.value || "";
            const holder = (document.getElementById("cardHolder")?.value || "").trim();

            if (number.length !== 16 || expiry.length !== 5 || cvv.length !== 3 || holder.length < 4) {
                setStatus("Заполните реквизиты карты корректно", "error");
                return;
            }
            startPayment("card", orderId);
        });
    }

    setupCardMasks();
    setMethod(activeMethod);
});

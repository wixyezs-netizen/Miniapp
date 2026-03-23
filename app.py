import os
import json
import hmac
import hashlib
import logging
from urllib.parse import parse_qs, unquote

from flask import Flask, request, jsonify, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import threading

# ─── НАСТРОЙКИ ───────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8638584778:AAEDBA2vokaJlo2NXNAr4-K5WzrrZrQWWGs")
WEBAPP_URL = "https://AimNoob.bothost.tech"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8080))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── FLASK APP ────────────────────────────────────────────────
flask_app = Flask(__name__)

# ─── HTML MINI APP ────────────────────────────────────────────
MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>AimNoob Mini App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --tg-theme-bg-color: #1a1a2e;
            --tg-theme-text-color: #eaeaea;
            --tg-theme-button-color: #e94560;
            --tg-theme-button-text-color: #ffffff;
            --tg-theme-secondary-bg-color: #16213e;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--tg-theme-bg-color, #1a1a2e);
            color: var(--tg-theme-text-color, #eaeaea);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ─── HEADER ─── */
        .header {
            background: linear-gradient(135deg, #e94560, #0f3460);
            padding: 30px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            animation: pulse 4s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 1; }
        }

        .header h1 {
            font-size: 28px;
            font-weight: 800;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header .subtitle {
            font-size: 14px;
            opacity: 0.85;
            margin-top: 8px;
            position: relative;
            z-index: 1;
        }

        /* ─── USER CARD ─── */
        .user-card {
            background: var(--tg-theme-secondary-bg-color, #16213e);
            margin: 16px;
            border-radius: 16px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            animation: slideUp 0.5s ease;
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #e94560, #533483);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            flex-shrink: 0;
        }

        .user-info h2 {
            font-size: 18px;
            margin-bottom: 4px;
        }

        .user-info p {
            font-size: 13px;
            opacity: 0.7;
        }

        /* ─── STATS ─── */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin: 0 16px 16px;
        }

        .stat-card {
            background: var(--tg-theme-secondary-bg-color, #16213e);
            border-radius: 14px;
            padding: 16px 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.15);
            animation: slideUp 0.5s ease;
        }

        .stat-card:nth-child(2) { animation-delay: 0.1s; }
        .stat-card:nth-child(3) { animation-delay: 0.2s; }

        .stat-number {
            font-size: 26px;
            font-weight: 800;
            background: linear-gradient(135deg, #e94560, #533483);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ─── MENU ─── */
        .menu-section {
            margin: 0 16px 16px;
        }

        .section-title {
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.5;
            margin-bottom: 12px;
            padding-left: 4px;
        }

        .menu-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .menu-item {
            background: var(--tg-theme-secondary-bg-color, #16213e);
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border: 1px solid transparent;
        }

        .menu-item:hover {
            transform: translateX(4px);
            border-color: rgba(233, 69, 96, 0.3);
        }

        .menu-item:active {
            transform: scale(0.98);
        }

        .menu-icon {
            font-size: 24px;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: rgba(233, 69, 96, 0.1);
            flex-shrink: 0;
        }

        .menu-text h3 {
            font-size: 15px;
            font-weight: 600;
        }

        .menu-text p {
            font-size: 12px;
            opacity: 0.5;
            margin-top: 2px;
        }

        .menu-arrow {
            margin-left: auto;
            opacity: 0.3;
            font-size: 18px;
        }

        /* ─── COUNTER GAME ─── */
        .game-section {
            margin: 0 16px 20px;
            background: var(--tg-theme-secondary-bg-color, #16213e);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .game-section h3 {
            margin-bottom: 16px;
            font-size: 16px;
        }

        .counter-display {
            font-size: 56px;
            font-weight: 900;
            background: linear-gradient(135deg, #e94560, #533483, #0f3460);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 16px 0;
            transition: transform 0.15s ease;
        }

        .counter-display.bump {
            transform: scale(1.2);
        }

        .counter-buttons {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-top: 16px;
        }

        .btn {
            padding: 12px 28px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            color: white;
        }

        .btn:active {
            transform: scale(0.95);
        }

        .btn-primary {
            background: linear-gradient(135deg, #e94560, #c23152);
            box-shadow: 0 4px 15px rgba(233, 69, 96, 0.4);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #533483, #0f3460);
            box-shadow: 0 4px 15px rgba(83, 52, 131, 0.4);
        }

        .btn-send {
            width: calc(100% - 32px);
            margin: 0 16px 20px;
            padding: 16px;
            background: linear-gradient(135deg, #e94560, #c23152);
            box-shadow: 0 4px 20px rgba(233, 69, 96, 0.4);
            font-size: 16px;
        }

        /* ─── TOAST ─── */
        .toast {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: rgba(233, 69, 96, 0.95);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 600;
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
            pointer-events: none;
        }

        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        /* ─── FOOTER ─── */
        .footer {
            text-align: center;
            padding: 20px;
            opacity: 0.3;
            font-size: 12px;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>🎯 AimNoob</h1>
        <div class="subtitle">Твоё мини-приложение в Telegram</div>
    </div>

    <div class="user-card" id="userCard">
        <div class="avatar" id="userAvatar">?</div>
        <div class="user-info">
            <h2 id="userName">Загрузка...</h2>
            <p id="userStatus">Подключение к Telegram...</p>
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number" id="visits">1</div>
            <div class="stat-label">Визиты</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="clicks">0</div>
            <div class="stat-label">Клики</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" id="level">1</div>
            <div class="stat-label">Уровень</div>
        </div>
    </div>

    <div class="game-section">
        <h3>🎮 Кликер</h3>
        <div class="counter-display" id="counter">0</div>
        <div class="counter-buttons">
            <button class="btn btn-primary" onclick="incrementCounter()">+1 🔥</button>
            <button class="btn btn-secondary" onclick="resetCounter()">Сброс 🔄</button>
        </div>
    </div>

    <div class="menu-section">
        <div class="section-title">Меню</div>
        <div class="menu-list">
            <div class="menu-item" onclick="showToast('🏆 Профиль скоро!')">
                <div class="menu-icon">👤</div>
                <div class="menu-text">
                    <h3>Профиль</h3>
                    <p>Твоя статистика и достижения</p>
                </div>
                <div class="menu-arrow">›</div>
            </div>
            <div class="menu-item" onclick="showToast('🏅 Рейтинг скоро!')">
                <div class="menu-icon">🏅</div>
                <div class="menu-text">
                    <h3>Рейтинг</h3>
                    <p>Топ игроков</p>
                </div>
                <div class="menu-arrow">›</div>
            </div>
            <div class="menu-item" onclick="showToast('⚙️ Настройки скоро!')">
                <div class="menu-icon">⚙️</div>
                <div class="menu-text">
                    <h3>Настройки</h3>
                    <p>Кастомизация приложения</p>
                </div>
                <div class="menu-arrow">›</div>
            </div>
            <div class="menu-item" onclick="showToast('📢 Новости скоро!')">
                <div class="menu-icon">📢</div>
                <div class="menu-text">
                    <h3>Новости</h3>
                    <p>Обновления и анонсы</p>
                </div>
                <div class="menu-arrow">›</div>
            </div>
        </div>
    </div>

    <button class="btn btn-send" onclick="sendData()">📤 Отправить данные боту</button>

    <div class="footer">
        AimNoob Mini App v1.0 — Powered by bothost.ru
    </div>

    <div class="toast" id="toast"></div>

    <script>
        // ─── TELEGRAM WEBAPP INIT ───
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        // Применяем тему Telegram
        if (tg.themeParams.bg_color) {
            document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color);
        }
        if (tg.themeParams.text_color) {
            document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color);
        }
        if (tg.themeParams.secondary_bg_color) {
            document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color);
        }

        // ─── USER INFO ───
        const user = tg.initDataUnsafe?.user;
        if (user) {
            const firstName = user.first_name || 'User';
            const lastName = user.last_name || '';
            document.getElementById('userName').textContent = `${firstName} ${lastName}`.trim();
            document.getElementById('userAvatar').textContent = firstName.charAt(0).toUpperCase();
            document.getElementById('userStatus').textContent = `ID: ${user.id} • @${user.username || 'no_username'}`;
        } else {
            document.getElementById('userName').textContent = 'Гость';
            document.getElementById('userStatus').textContent = 'Откройте через Telegram';
            document.getElementById('userAvatar').textContent = 'G';
        }

        // ─── COUNTER LOGIC ───
        let count = parseInt(localStorage.getItem('aimnoob_count') || '0');
        let totalClicks = parseInt(localStorage.getItem('aimnoob_clicks') || '0');
        let visits = parseInt(localStorage.getItem('aimnoob_visits') || '0') + 1;

        localStorage.setItem('aimnoob_visits', visits);

        document.getElementById('counter').textContent = count;
        document.getElementById('clicks').textContent = totalClicks;
        document.getElementById('visits').textContent = visits;
        updateLevel();

        function incrementCounter() {
            count++;
            totalClicks++;
            localStorage.setItem('aimnoob_count', count);
            localStorage.setItem('aimnoob_clicks', totalClicks);

            const el = document.getElementById('counter');
            el.textContent = count;
            el.classList.add('bump');
            setTimeout(() => el.classList.remove('bump'), 150);

            document.getElementById('clicks').textContent = totalClicks;
            updateLevel();

            // Хаптик
            if (tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }
        }

        function resetCounter() {
            count = 0;
            localStorage.setItem('aimnoob_count', count);
            document.getElementById('counter').textContent = count;

            if (tg.HapticFeedback) {
                tg.HapticFeedback.notificationOccurred('warning');
            }
            showToast('🔄 Счётчик сброшен!');
        }

        function updateLevel() {
            const level = Math.floor(totalClicks / 10) + 1;
            document.getElementById('level').textContent = level;
        }

        // ─── SEND DATA TO BOT ───
        function sendData() {
            const data = JSON.stringify({
                action: 'game_result',
                counter: count,
                total_clicks: totalClicks,
                visits: visits,
                level: Math.floor(totalClicks / 10) + 1,
                timestamp: new Date().toISOString()
            });

            try {
                tg.sendData(data);
                showToast('✅ Данные отправлены!');
            } catch (e) {
                showToast('❌ Откройте через Telegram');
            }
        }

        // ─── TOAST ───
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
        }

        // ─── Main Button (опционально) ───
        tg.MainButton.setText('📤 Отправить результат');
        tg.MainButton.color = '#e94560';
        tg.MainButton.textColor = '#ffffff';
        tg.MainButton.onClick(sendData);
        // tg.MainButton.show(); // Раскомментируй если нужна кнопка внизу
    </script>
</body>
</html>
"""

# ─── FLASK ROUTES ─────────────────────────────────────────────

@flask_app.route("/")
def index():
    """Главная страница — Mini App"""
    return render_template_string(MINI_APP_HTML)


@flask_app.route("/health")
def health():
    """Health check для bothost"""
    return jsonify({"status": "ok", "bot": "AimNoob"})


@flask_app.route("/api/user", methods=["POST"])
def api_user():
    """API endpoint (для будущего расширения)"""
    data = request.get_json(silent=True) or {}
    return jsonify({"status": "ok", "received": data})


# ─── WEBHOOK ROUTE ────────────────────────────────────────────

bot_app = None  # Будет инициализировано позже


@flask_app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Приём обновлений от Telegram через webhook"""
    if bot_app is None:
        return "Bot not ready", 503

    update = Update.de_json(request.get_json(force=True), bot_app.bot)

    # Обработка асинхронно
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot_app.process_update(update))
    finally:
        loop.close()

    return "OK", 200


# ─── TELEGRAM BOT HANDLERS ───────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton(
            "🎯 Открыть Mini App",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
        [InlineKeyboardButton(
            "📢 Канал разработчика",
            url="https://t.me/AimNoob"
        )],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"🎯 Я бот <b>AimNoob</b> с Mini App!\n\n"
        f"Нажми кнопку ниже, чтобы открыть приложение 👇",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    await update.message.reply_text(
        "📖 <b>Помощь</b>\n\n"
        "🔹 /start — Главное меню\n"
        "🔹 /help — Эта справка\n"
        "🔹 /app — Открыть Mini App\n"
        "🔹 /stats — Твоя статистика\n\n"
        "💡 Нажми кнопку <b>«Открыть Mini App»</b> чтобы запустить приложение!",
        parse_mode="HTML",
    )


async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /app — открыть мини-приложение"""
    keyboard = [
        [InlineKeyboardButton(
            "🚀 Запустить Mini App",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
    ]
    await update.message.reply_text(
        "🎮 Нажми кнопку, чтобы открыть приложение:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    user = update.effective_user
    await update.message.reply_text(
        f"📊 <b>Статистика</b>\n\n"
        f"👤 Имя: {user.first_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📛 Username: @{user.username or 'не указан'}\n\n"
        f"💡 Больше статистики — в Mini App!",
        parse_mode="HTML",
    )


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка данных из Mini App"""
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        counter = data.get("counter", 0)
        total_clicks = data.get("total_clicks", 0)
        visits = data.get("visits", 0)
        level = data.get("level", 1)

        await update.message.reply_text(
            f"📦 <b>Данные из Mini App получены!</b>\n\n"
            f"🎮 Счётчик: <b>{counter}</b>\n"
            f"👆 Всего кликов: <b>{total_clicks}</b>\n"
            f"👁 Визитов: <b>{visits}</b>\n"
            f"⭐ Уровень: <b>{level}</b>\n\n"
            f"🔥 Отлично! Продолжай играть!",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error processing web_app_data: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    keyboard = [
        [InlineKeyboardButton(
            "🎯 Открыть Mini App",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )],
    ]
    await update.message.reply_text(
        "🤖 Я понимаю только команды!\n\n"
        "Попробуй /start или открой Mini App 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ─── ИНИЦИАЛИЗАЦИЯ БОТА ──────────────────────────────────────

def setup_bot():
    """Создаём и настраиваем бота"""
    global bot_app

    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем хэндлеры
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("app", app_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Обработка данных из WebApp
    application.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data)
    )

    # Обработка обычных сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    bot_app = application

    # Устанавливаем webhook
    async def set_webhook():
        await application.initialize()
        webhook_url = f"{WEBAPP_URL}/webhook/{BOT_TOKEN}"
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook установлен: {webhook_url}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(set_webhook())
    finally:
        loop.close()

    logger.info("🤖 Бот инициализирован!")


# ─── ЗАПУСК ───────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("🚀 Запуск AimNoob Bot + Mini App...")
    logger.info(f"🌐 Web App URL: {WEBAPP_URL}")

    # Инициализируем бота
    try:
        setup_bot()
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        logger.info("⚠️ Flask запустится без бота (только Mini App)")

    # Запускаем Flask
    flask_app.run(host=HOST, port=PORT, debug=False)

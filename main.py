import asyncio
import json
import logging
import os
import threading
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("sweet-toys")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
APP_URL = os.getenv("APP_URL", "").strip()
PORT = int(os.getenv("PORT", "8000"))

if not APP_URL:
    APP_URL = f"http://localhost:{PORT}"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# Демо-каталог: замените image на свои ссылки/файлы при необходимости.
PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "toy_001",
        "name": "Плюшевый Мишка Luna",
        "category": "Мягкие игрушки",
        "price": 2490,
        "old_price": 2990,
        "badge": "Хит",
        "description": "Невероятно мягкий мишка из гипоаллергенного плюша для уютных объятий.",
        "image": "https://picsum.photos/seed/sweet-toy-001/900/900",
        "age_label": "3+",
        "in_stock": True,
    },
    {
        "id": "toy_002",
        "name": "Зайка Cloud Hug",
        "category": "Мягкие игрушки",
        "price": 2190,
        "old_price": None,
        "badge": "Новинка",
        "description": "Нежный зайка в пастельных оттенках, который легко станет любимцем малыша.",
        "image": "https://picsum.photos/seed/sweet-toy-002/900/900",
        "age_label": "0+",
        "in_stock": True,
    },
    {
        "id": "toy_003",
        "name": "Пирамидка Bloom",
        "category": "Для малышей",
        "price": 1590,
        "old_price": 1890,
        "badge": "Скидка",
        "description": "Развивает моторику и восприятие цвета. Безопасный ABS-пластик без запаха.",
        "image": "https://picsum.photos/seed/sweet-toy-003/900/900",
        "age_label": "1+",
        "in_stock": True,
    },
    {
        "id": "toy_004",
        "name": "Бизикуб Smart Home",
        "category": "Развивающие игрушки",
        "price": 3490,
        "old_price": None,
        "badge": "Хит",
        "description": "6 игровых зон для развития логики, внимания и мелкой моторики.",
        "image": "https://picsum.photos/seed/sweet-toy-004/900/900",
        "age_label": "2+",
        "in_stock": True,
    },
    {
        "id": "toy_005",
        "name": "Набор кубиков Nordic",
        "category": "Для малышей",
        "price": 1890,
        "old_price": None,
        "badge": "Новинка",
        "description": "Лёгкие кубики с мягкими гранями для безопасной игры и первых башен.",
        "image": "https://picsum.photos/seed/sweet-toy-005/900/900",
        "age_label": "1+",
        "in_stock": True,
    },
    {
        "id": "toy_006",
        "name": "Конструктор Mini City",
        "category": "Конструкторы",
        "price": 2790,
        "old_price": 3290,
        "badge": "Скидка",
        "description": "Собери уютный городок: домики, парк и милые персонажи в одном наборе.",
        "image": "https://picsum.photos/seed/sweet-toy-006/900/900",
        "age_label": "4+",
        "in_stock": True,
    },
    {
        "id": "toy_007",
        "name": "Магнитный конструктор Glow",
        "category": "Конструкторы",
        "price": 3990,
        "old_price": None,
        "badge": "Хит",
        "description": "Светящиеся детали с безопасными магнитами для фантазийных конструкций.",
        "image": "https://picsum.photos/seed/sweet-toy-007/900/900",
        "age_label": "5+",
        "in_stock": True,
    },
    {
        "id": "toy_008",
        "name": "Сортер Rainbow Nest",
        "category": "Развивающие игрушки",
        "price": 1690,
        "old_price": None,
        "badge": "Новинка",
        "description": "Помогает изучать формы и цвета. Идеален для первых самостоятельных игр.",
        "image": "https://picsum.photos/seed/sweet-toy-008/900/900",
        "age_label": "2+",
        "in_stock": True,
    },
    {
        "id": "toy_009",
        "name": "Подарочный бокс Joy Box",
        "category": "Подарки",
        "price": 4590,
        "old_price": 5190,
        "badge": "Скидка",
        "description": "Готовый премиальный набор: мягкая игрушка, игра и открытка.",
        "image": "https://picsum.photos/seed/sweet-toy-009/900/900",
        "age_label": "3+",
        "in_stock": True,
    },
    {
        "id": "toy_010",
        "name": "Музыкальный слоник Melody",
        "category": "Для малышей",
        "price": 2390,
        "old_price": None,
        "badge": "Хит",
        "description": "Нежные мелодии, сенсорные элементы и безопасные материалы для малышей.",
        "image": "https://picsum.photos/seed/sweet-toy-010/900/900",
        "age_label": "0+",
        "in_stock": True,
    },
]

orders: list[dict[str, Any]] = []
orders_lock = threading.Lock()


def format_price(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₽"


def get_product_map() -> dict[str, dict[str, Any]]:
    return {product["id"]: product for product in PRODUCTS}


def build_order_lines(items: list[dict[str, Any]]) -> tuple[str, int]:
    product_map = get_product_map()
    lines: list[str] = []
    total = 0

    for item in items:
        product_id = str(item.get("id", "")).strip()
        qty = int(item.get("qty", 0) or 0)
        if not product_id or qty <= 0:
            continue

        product = product_map.get(product_id)
        if not product:
            continue

        line_total = product["price"] * qty
        total += line_total
        lines.append(f"• {product['name']} × {qty} = {format_price(line_total)}")

    return "\n".join(lines), total


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    webapp_url = APP_URL.rstrip("/") + "/"
    keyboard = [[KeyboardButton("🛍 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]]

    welcome_text = (
        "🌸 <b>Добро пожаловать в Sweet Toys</b>\n\n"
        "Игрушки, которые радуют с первого взгляда.\n"
        "Откройте витрину и соберите заказ за пару минут 💛"
    )

    message_target = update.effective_message
    chat_id = update.effective_chat.id if update.effective_chat else None

    if message_target:
        await message_target.reply_text(
            welcome_text,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        )
        await message_target.reply_text(
            "Быстрый доступ к магазину:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🛍 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]]
            ),
        )
        return

    if chat_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="Быстрый доступ к магазину:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🛍 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]]
            ),
        )


async def notify_order(order: dict[str, Any]) -> None:
    try:
        from telegram import Bot

        bot = Bot(BOT_TOKEN)
        lines_text, total = build_order_lines(order.get("items", []))
        admin_text = (
            "🧾 <b>Новый заказ</b>\n"
            f"№ <b>{order['id']}</b>\n"
            f"👤 Имя: <b>{order['name']}</b>\n"
            f"📞 Телефон: <b>{order['phone']}</b>\n"
            f"🧸 Товары:\n{lines_text or '—'}\n"
            f"💰 Итого: <b>{format_price(total)}</b>\n"
            f"💬 Комментарий: {order.get('comment') or '—'}\n"
            f"🆔 Telegram ID: <code>{order.get('telegram_user_id', 'не передан')}</code>"
        )

        if ADMIN_ID:
            await bot.send_message(chat_id=int(ADMIN_ID), text=admin_text, parse_mode="HTML")

        user_id = order.get("telegram_user_id")
        if user_id:
            await bot.send_message(
                chat_id=int(user_id),
                text="Спасибо! Ваш заказ принят, скоро с вами свяжутся 💛",
            )
    except Exception as exc:
        logger.exception("Failed to notify order: %s", exc)


@app.get("/")
def index() -> str:
    catalog_json = json.dumps(PRODUCTS, ensure_ascii=False)
    html = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>Sweet Toys — Premium Toy Boutique</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root{
      --bg:#fffaf5;
      --surface:#ffffff;
      --surface-soft:#fff7f0;
      --text:#28231f;
      --muted:#7d736b;
      --line:rgba(90,65,42,.12);
      --accent:#f2c965;
      --accent-deep:#dfb450;
      --peach:#ffe9db;
      --rose:#fbe4ea;
      --sand:#f9f1e8;
      --radius-xxl:28px;
      --radius-xl:22px;
      --radius-lg:18px;
      --radius-md:14px;
      --shadow-soft:0 10px 30px rgba(66,44,22,.07);
      --shadow-card:0 18px 36px rgba(70,44,20,.08);
    }
    *{box-sizing:border-box}
    body {
      margin: 0;
      font-family: Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Ubuntu,"Helvetica Neue",Arial,sans-serif;
      background: radial-gradient(1400px 700px at 50% -120px,#ffeede 0%,#fff6ef 40%,var(--bg) 75%);
      color: var(--text);
      padding-bottom: 124px;
      -webkit-font-smoothing: antialiased;
    }
    .container{padding:16px;max-width:920px;margin:0 auto}
    .topbar{
      position:sticky;
      top:0;
      z-index:18;
      margin:0 -16px;
      padding:10px 16px 12px;
      backdrop-filter: blur(14px);
      background:rgba(255,250,245,.72);
      border-bottom:1px solid rgba(90,65,42,.08);
    }
    .brand{display:flex;align-items:center;justify-content:space-between;gap:10px}
    .brand-badge{
      display:inline-flex;align-items:center;gap:8px;
      background:#fff;
      border-radius:999px;
      padding:8px 12px;
      box-shadow:var(--shadow-soft);
      font-size:12px;
      color:#63574f;
      letter-spacing:.2px;
    }
    .search{
      margin-top:10px;
      background:#fff;
      border-radius:14px;
      padding:12px 14px;
      border:1px solid var(--line);
      display:flex;align-items:center;gap:10px;
      box-shadow:var(--shadow-soft);
    }
    .search input{
      border:none;outline:none;background:transparent;
      width:100%;font-size:14px;color:var(--text);
    }
    .hero{
      margin-top:14px;
      padding:24px 20px 18px;
      border-radius:var(--radius-xxl);
      background:
        radial-gradient(circle at 82% 10%, rgba(255,255,255,.75), transparent 33%),
        linear-gradient(130deg,#fff4e8 0%,#ffe8db 55%,#ffe0ea 100%);
      box-shadow:var(--shadow-card);
      position:relative;
      overflow:hidden;
    }
    .hero h1{margin:0;font-size:32px;line-height:1.07;letter-spacing:-.5px;max-width:92%}
    .hero p{margin:10px 0 0;font-size:14px;color:#6d625a;line-height:1.5;max-width:88%}
    .hero-chip{
      margin-top:14px;display:inline-flex;align-items:center;gap:8px;
      background:rgba(255,255,255,.82);padding:9px 12px;border-radius:999px;
      font-size:12px;color:#584c44
    }
    .chips{display:flex;gap:8px;overflow:auto;padding:14px 2px 2px}
    .chip{
      border:none;border-radius:999px;padding:10px 14px;white-space:nowrap;
      background:#fff;color:#5b514a;font-size:13px;font-weight:500;
      box-shadow:var(--shadow-soft)
    }
    .chip.active{background:#2d2824;color:#fff}
    .section{margin-top:18px}
    .section h2{margin:0;font-size:21px;letter-spacing:-.2px}
    .section-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
    .section-sub{font-size:13px;color:var(--muted);margin-top:6px}
    .cards-row{display:flex;gap:10px;overflow:auto;padding-bottom:4px}
    .mini-card{
      min-width:230px;background:var(--surface);border-radius:16px;padding:14px;
      box-shadow:var(--shadow-soft);border:1px solid rgba(90,65,42,.08)
    }
    .mini-card h4{margin:0 0 8px;font-size:15px}
    .mini-card p{margin:0;font-size:13px;color:var(--muted);line-height:1.45}
    .social{
      margin-top:10px;padding:14px;border-radius:16px;
      background:linear-gradient(120deg,#fff 0%,#fff7ef 100%);
      border:1px solid rgba(90,65,42,.08);
      box-shadow:var(--shadow-soft);
      font-size:13px;color:#5f554d
    }
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}
    .card{
      background:var(--surface);border-radius:20px;overflow:hidden;
      box-shadow:var(--shadow-card);animation:fadeUp .45s ease;border:1px solid rgba(90,65,42,.08)
    }
    .img-wrap{position:relative;aspect-ratio:1/1;overflow:hidden}
    .img-wrap img{width:100%;height:100%;object-fit:cover;transform:scale(1.01)}
    .badge{
      position:absolute;top:10px;left:10px;background:#2f2a26;color:#fff;
      border-radius:999px;padding:6px 10px;font-size:11px
    }
    .age{
      position:absolute;bottom:10px;left:10px;
      background:rgba(255,255,255,.9);padding:5px 9px;border-radius:999px;
      font-size:11px;color:#5f544c
    }
    .content{padding:12px 12px 13px}
    .name{font-weight:700;margin:0;font-size:14px;line-height:1.3;min-height:36px}
    .desc{margin:6px 0 0;color:var(--muted);font-size:12px;line-height:1.42;min-height:34px}
    .price-row{margin-top:10px;display:flex;align-items:center;gap:8px}
    .price{font-weight:700}
    .old-price{color:#aca29c;text-decoration:line-through;font-size:12px}
    .btn{
      width:100%;margin-top:11px;border:none;border-radius:12px;padding:11px 12px;
      font-weight:700;background:linear-gradient(180deg,var(--accent),var(--accent-deep));
      color:#3f3013;transition:.2s transform,.2s box-shadow;box-shadow:0 8px 14px rgba(223,180,80,.34)
    }
    .btn:active{transform:translateY(1px) scale(.995)}
    .skeleton{
      display:grid;grid-template-columns:1fr 1fr;gap:13px;margin-top:10px
    }
    .s-card{
      border-radius:20px;height:235px;background:linear-gradient(100deg,#fff 20%,#fff7ef 40%,#fff 60%);
      background-size:300% 100%;animation:shine 1.2s linear infinite;
      box-shadow:var(--shadow-soft);
    }
    @keyframes shine { 0%{background-position:100% 0} 100%{background-position:0 0} }
    .sticky-cart {
      position: fixed;
      bottom: calc(88px + env(safe-area-inset-bottom));
      right: 16px;
      z-index: 26;
      border: none;
      background: #2e2925;
      color: #fff;
      border-radius: 999px;
      padding: 13px 15px;
      box-shadow: 0 18px 30px rgba(0,0,0,.24);
      display: none;
    }
    .bottom-nav {
      position: fixed;
      left: 0; right: 0;
      bottom: 0;
      padding: 10px 16px calc(12px + env(safe-area-inset-bottom));
      background: rgba(255, 250, 245, .88);
      backdrop-filter: blur(14px);
      border-top: 1px solid rgba(80,60,50,.08);
      display: flex;
      gap: 10px;
      z-index: 40;
    }
    .nav-btn{
      flex:1;border:none;background:#fff;border-radius:15px;padding:13px 12px;
      font-weight:600;color:#4f4540;box-shadow:var(--shadow-soft)
    }
    .nav-btn.primary{
      background:linear-gradient(180deg,var(--accent),var(--accent-deep));
      color:#3d2f15
    }
    .sheet {
      position: fixed; left: 0; right: 0; bottom: 0; max-height: 85vh; background: #fff;
      border-radius: 24px 24px 0 0; box-shadow: 0 -20px 40px rgba(0,0,0,.16); padding: 16px;
      transform: translateY(110%); transition: .25s ease; z-index: 50; overflow:auto;
    }
    .sheet.open { transform: translateY(0); }
    .overlay{
      position:fixed; inset:0; background:rgba(27,20,16,.34);
      z-index:49; opacity:0; pointer-events:none; transition:.24s;
    }
    .overlay.open{opacity:1;pointer-events:auto}
    .sheet-head{
      display:flex;align-items:center;justify-content:space-between;gap:10px
    }
    .close-btn{
      width:34px;height:34px;border:none;border-radius:999px;background:#f6eee6;
      font-size:20px;line-height:1;color:#4b3f36
    }
    .sheet-title { margin: 0 0 12px; font-size: 20px; }
    .cart-item { display: flex; justify-content: space-between; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f0e8e2; }
    .qty { display: inline-flex; gap: 6px; align-items:center; }
    .qty button { width: 24px; height: 24px; border-radius: 8px; border: none; background: #f4eee7; }
    .field {
      width:100%;border:1px solid #e8ddd4;border-radius:13px;padding:13px 12px;
      margin-bottom:10px;font-size:15px;outline:none
    }
    .field:focus{border-color:#dfb450;box-shadow:0 0 0 3px rgba(223,180,80,.18)}
    .toast { position: fixed; left: 50%; transform: translateX(-50%); bottom: 132px; background: #2d2925; color: #fff; padding: 10px 14px; border-radius: 999px; opacity: 0; transition:.25s; z-index: 60; }
    .toast.show { opacity: 1; }
    .success { text-align:center; padding: 30px 10px; }
    .success .icon { font-size: 54px; animation: pop .4s ease; }
    .empty{
      text-align:center;padding:26px 8px 12px;color:#6f655d
    }
    .empty strong{display:block;color:#322c27;margin-bottom:6px}
    .sticky-checkout{
      position:sticky;bottom:-16px;background:#fff;padding:12px 0 calc(8px + env(safe-area-inset-bottom));
      margin-top:8px;border-top:1px solid #f2e7df
    }
    @keyframes fadeUp { from {opacity:0; transform: translateY(8px);} to {opacity:1; transform:translateY(0);} }
    @keyframes pop { from {transform: scale(.8); opacity:.5} to {transform: scale(1); opacity:1} }
  </style>
</head>
<body>
  <div class="container" id="app"></div>
  <button id="stickyCart" class="sticky-cart">🛒 Корзина</button>
  <div class="bottom-nav">
    <button class="nav-btn" id="homeBtn">Главная</button>
    <button class="nav-btn" id="catalogBtn">Каталог</button>
    <button class="nav-btn primary" id="cartBtn">Корзина · 0</button>
  </div>
  <div class="overlay" id="overlay"></div>
  <section class="sheet" id="sheet"></section>
  <div class="toast" id="toast"></div>
<script>
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }
const products = __CATALOG__;
const categories = ['Все', ...new Set(products.map(p => p.category))];
let selectedCategory = 'Все';
let searchValue = '';
let cart = {};
const appEl = document.getElementById('app');
const sheetEl = document.getElementById('sheet');
const overlayEl = document.getElementById('overlay');
const toastEl = document.getElementById('toast');
const cartBtn = document.getElementById('cartBtn');
const stickyCart = document.getElementById('stickyCart');
function price(v) { return new Intl.NumberFormat('ru-RU').format(v) + ' ₽'; }
function toast(msg) { toastEl.textContent = msg; toastEl.classList.add('show'); setTimeout(() => toastEl.classList.remove('show'), 1200); }
const fallbackImage = "data:image/svg+xml;utf8," + encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='900' height='900'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop stop-color='#fff2e6'/><stop offset='1' stop-color='#fbe4ea'/></linearGradient></defs><rect width='100%' height='100%' fill='url(#g)'/><text x='50%' y='48%' dominant-baseline='middle' text-anchor='middle' fill='#6f5e52' font-family='Arial' font-size='42'>Sweet Toys</text><text x='50%' y='56%' dominant-baseline='middle' text-anchor='middle' fill='#8d7b6f' font-family='Arial' font-size='24'>Изображение обновляется</text></svg>`);
function safeImage(url){ return `src="${url}" onerror="this.onerror=null;this.src='${fallbackImage}'"`; }
function productMatchesSearch(p){
  if(!searchValue) return true;
  const q = searchValue.toLowerCase();
  return [p.name,p.description,p.category,p.badge,p.age_label].filter(Boolean).join(' ').toLowerCase().includes(q);
}
function pickByCategory(cat){
  return products.filter(p => (cat === 'Все' || p.category === cat) && productMatchesSearch(p));
}
function byCategory(cat){
  return products.filter(p => p.category === cat).slice(0,6);
}
function renderHome() {
  const chips = categories.map(c => `<button class="chip ${selectedCategory===c?'active':''}" onclick="setCategory('${c}')">${c}</button>`).join('');
  const list = pickByCategory(selectedCategory);
  const popular = products.filter(p => ['Хит','Новинка'].includes(p.badge)).slice(0,5);
  const baby = byCategory('Для малышей');
  const gifts = byCategory('Подарки');
  const popularCards = popular.map(p=>`<article class='mini-card' onclick="openProduct('${p.id}')"><h4>${p.name}</h4><p>${p.description}</p></article>`).join('');
  const babyCards = baby.map(p=>`<article class='mini-card' onclick="openProduct('${p.id}')"><h4>${p.name}</h4><p>${p.age_label} · ${price(p.price)}</p></article>`).join('');
  const giftCards = gifts.map(p=>`<article class='mini-card' onclick="openProduct('${p.id}')"><h4>${p.name}</h4><p>${p.badge || 'Подарок'} · ${price(p.price)}</p></article>`).join('');
  const listHtml = list.length ? list.map(cardTpl).join('') : `<div style='grid-column:1/-1' class='empty'><strong>Ничего не найдено</strong>Попробуйте другой запрос или категорию.</div>`;
  appEl.innerHTML = `
  <section class='topbar'>
    <div class='brand'>
      <div class='brand-badge'>✨ Sweet Toys Boutique</div>
      <div class='brand-badge'>Для мам и малышей</div>
    </div>
    <label class='search'>
      <span>🔎</span>
      <input id='searchInput' placeholder='Поиск по каталогу' value="${searchValue.replace(/"/g,'&quot;')}" />
    </label>
  </section>
  <section class='hero'>
    <h1>Игрушки, которые радуют с первого взгляда</h1>
    <p>Аккуратная premium-подборка безопасных и красивых игрушек. Удобный заказ прямо в Telegram.</p>
    <div class='hero-chip'>💛 Быстрая связь после заказа · Проверенные материалы</div>
  </section>
  <div class='chips'>${chips}</div>
  <section class='section'>
    <div class='section-top'><h2>Популярное</h2></div>
    <div class='cards-row'>${popularCards}</div>
  </section>
  <section class='section'>
    <div class='section-top'><h2>Подарки</h2></div>
    <div class='cards-row'>${giftCards || "<article class='mini-card'><h4>Скоро добавим</h4><p>Подборки в разработке.</p></article>"}</div>
  </section>
  <section class='section'>
    <div class='section-top'><h2>Для малышей</h2></div>
    <div class='cards-row'>${babyCards || "<article class='mini-card'><h4>Скоро добавим</h4><p>Подборки в разработке.</p></article>"}</div>
  </section>
  <section class='section'>
    <div class='section-top'><h2>Каталог</h2></div>
    <p class='section-sub'>Чистый premium-интерфейс для быстрого выбора и заказа.</p>
    <section class='grid'>${listHtml}</section>
  </section>
  <section class='section'>
    <div class='section-top'><h2>Почему нам доверяют</h2></div>
    <div class='cards-row'>
      <article class='mini-card'><h4>🛡 Безопасные материалы</h4><p>Только проверенные игрушки, которые приятно дарить и спокойно выбирать.</p></article>
      <article class='mini-card'><h4>⚡ Быстрая связь</h4><p>После заказа быстро подтверждаем детали в Telegram.</p></article>
      <article class='mini-card'><h4>📲 Удобный формат</h4><p>Весь путь покупки внутри Telegram WebApp — без лишних шагов.</p></article>
    </div>
    <div class='social'>“Очень аккуратный магазин и понятный заказ. Быстро ответили и помогли подобрать подарок.” — мама Анастасия</div>
  </section>`;
  const searchInput = document.getElementById('searchInput');
  if(searchInput){
    searchInput.addEventListener('input', (e)=>{ searchValue = e.target.value || ''; renderHome(); });
  }
  updateCartUI();
}
function cardTpl(p) {
  return `<article class="card"><div class="img-wrap" onclick="openProduct('${p.id}')"><img ${safeImage(p.image)} alt="${p.name}" loading="lazy" />${p.badge ? `<span class='badge'>${p.badge}</span>` : ''}<span class='age'>${p.age_label}</span></div><div class="content"><p class="name">${p.name}</p><p class="desc">${p.description}</p><div class="price-row"><span class="price">${price(p.price)}</span>${p.old_price ? `<span class='old-price'>${price(p.old_price)}</span>` : ''}</div><button class="btn" onclick="addToCart('${p.id}', 1)">Добавить</button></div></article>`;
}
function setCategory(cat) { selectedCategory = cat; renderHome(); }
function openProduct(id) {
  const p = products.find(i => i.id === id);
  if (!p) return;
  const qtyId = `qty_${p.id}`;
  const also = products.filter(x => x.category === p.category && x.id !== p.id).slice(0,3).map(x=>`<article class='mini-card' onclick="openProduct('${x.id}')"><h4>${x.name}</h4><p>${price(x.price)}</p></article>`).join('');
  sheetEl.innerHTML = `
    <div class='sheet-head'><h3 class='sheet-title'>Товар</h3><button class='close-btn' onclick='closeSheet()'>×</button></div>
    <img ${safeImage(p.image)} style='width:100%;border-radius:16px;max-height:280px;object-fit:cover' />
    <h3 class='sheet-title' style='margin-top:12px'>${p.name}</h3>
    <p style='color:#7d7068;margin:10px 0 0'>${p.description}</p>
    <p style='margin:8px 0 0'><b>${price(p.price)}</b>${p.old_price ? ` <span class='old-price'>${price(p.old_price)}</span>` : ''}</p>
    <p style='margin:8px 0 0;font-size:13px;color:#6e645b'>Возраст: ${p.age_label} · Категория: ${p.category} · ${p.in_stock ? 'В наличии' : 'Нет в наличии'}</p>
    <div style='margin-top:10px;background:#fff7ef;padding:12px;border-radius:12px;color:#5c5149;font-size:13px'>
      ✅ Безопасные материалы · 🚚 Быстрая связь после заказа · 💬 Удобно через Telegram
    </div>
    <div style='display:flex;align-items:center;gap:10px;margin-top:10px'>
      <div class='qty'><button onclick="modalQty('${qtyId}',-1)">−</button><b id='${qtyId}'>1</b><button onclick="modalQty('${qtyId}',1)">+</button></div>
      <button class='btn' style='margin:0' onclick="addToCart('${p.id}', modalQtyRead('${qtyId}')); closeSheet();">Добавить в корзину</button>
    </div>
    <h4 style='margin:16px 0 8px'>С этим товаром берут</h4>
    <div class='cards-row'>${also || "<article class='mini-card'><h4>Подборки обновляются</h4><p>Скоро добавим больше рекомендаций.</p></article>"}</div>`;
  openSheet();
}
function modalQtyRead(id){ const el = document.getElementById(id); return Math.max(1, Number(el?.textContent || 1)); }
function modalQty(id, delta){
  const el = document.getElementById(id);
  if(!el) return;
  const next = Math.max(1, Number(el.textContent || 1) + delta);
  el.textContent = String(next);
}
function addToCart(id, qty) { cart[id] = (cart[id] || 0) + qty; toast('Добавлено в корзину'); updateCartUI(); }
function changeQty(id, delta) { cart[id] = (cart[id] || 0) + delta; if (cart[id] <= 0) delete cart[id]; renderCart(); updateCartUI(); }
function cartItems() { return Object.entries(cart).map(([id, qty]) => { const p = products.find(x => x.id === id); return p ? {id, qty, name: p.name, price: p.price} : null; }).filter(Boolean); }
function cartTotal() { return cartItems().reduce((s, i) => s + i.price * i.qty, 0); }
function updateCartUI() { const count = Object.values(cart).reduce((s, n) => s + n, 0); cartBtn.textContent = `Корзина · ${count}`; stickyCart.style.display = count ? 'block' : 'none'; }
function renderCart() {
  const items = cartItems();
  if (!items.length) {
    sheetEl.innerHTML = `<div class='sheet-head'><h3 class='sheet-title'>Корзина</h3><button class='close-btn' onclick='closeSheet()'>×</button></div><div class='empty'><strong>Корзина пока пустая</strong>Добавьте понравившиеся игрушки, чтобы оформить заказ.</div>`;
    openSheet();
    return;
  }
  sheetEl.innerHTML = `<div class='sheet-head'><h3 class='sheet-title'>Корзина</h3><button class='close-btn' onclick='closeSheet()'>×</button></div>${items.map(i => `<div class='cart-item'><div><div style='font-weight:600'>${i.name}</div><div style='color:#7e746d;font-size:13px'>${price(i.price*i.qty)}</div></div><div class='qty'><button onclick="changeQty('${i.id}',-1)">−</button><b>${i.qty}</b><button onclick="changeQty('${i.id}',1)">+</button></div></div>`).join('')}<div class='sticky-checkout'><p style='font-size:18px;margin:0 0 8px'><b>Итого: ${price(cartTotal())}</b></p><button class='btn' onclick='renderCheckout()'>Оформить заказ</button></div>`;
  openSheet();
}
function renderCheckout() { sheetEl.innerHTML = `<div class='sheet-head'><h3 class='sheet-title'>Оформление заказа</h3><button class='close-btn' onclick='closeSheet()'>×</button></div><input id='name' class='field' placeholder='Ваше имя' /><input id='phone' class='field' placeholder='Телефон' /><textarea id='comment' class='field' rows='3' placeholder='Комментарий к заказу'></textarea><button class='btn' onclick='submitOrder()'>Отправить заказ</button>`; }
async function submitOrder() {
  const name = document.getElementById('name').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const comment = document.getElementById('comment').value.trim();
  const items = cartItems().map(i => ({id: i.id, qty: i.qty}));
  if (!items.length) return toast('Корзина пуста');
  if (!name || !phone) return toast('Укажите имя и телефон');
  const payload = { name, phone, comment, items, telegram_user_id: tg?.initDataUnsafe?.user?.id || null };
  try {
    const r = await fetch('/api/order', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const data = await r.json();
    if (!r.ok || !data.ok) throw new Error(data.error || 'Ошибка отправки');
    cart = {}; renderSuccess(data.order_id); updateCartUI(); if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  } catch (e) { toast(e.message || 'Не удалось отправить заказ'); }
}
function renderSuccess(orderId) { sheetEl.innerHTML = `<div class='sheet-head'><h3 class='sheet-title'>Заказ оформлен</h3><button class='close-btn' onclick='closeSheet()'>×</button></div><div class='success'><div class='icon'>✅</div><h3 class='sheet-title'>Заказ #${orderId} принят</h3><p style='color:#7d7068'>Спасибо! Скоро свяжемся с вами 💛</p><button class='btn' onclick='closeSheet();'>Вернуться в каталог</button></div>`; }
function openSheet() { overlayEl.classList.add('open'); sheetEl.classList.add('open'); }
function closeSheet() { overlayEl.classList.remove('open'); sheetEl.classList.remove('open'); }
document.getElementById('homeBtn').onclick = () => { closeSheet(); renderHome(); };
document.getElementById('catalogBtn').onclick = () => { closeSheet(); renderHome(); };
document.getElementById('cartBtn').onclick = renderCart;
stickyCart.onclick = renderCart;
overlayEl.onclick = closeSheet;
appEl.innerHTML = `<section class='skeleton'><div class='s-card'></div><div class='s-card'></div><div class='s-card'></div><div class='s-card'></div></section>`;
setTimeout(renderHome, 220);
</script>
</body>
</html>
"""
    return html.replace("__CATALOG__", catalog_json)


@app.get("/health")
def health() -> Any:
    return jsonify(
        {
            "status": "ok",
            "service": "toy-shop",
            "time": datetime.utcnow().isoformat(),
        }
    )


@app.post("/api/order")
def api_order() -> Any:
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    comment = str(data.get("comment", "")).strip()
    items = data.get("items") or []
    telegram_user_id = data.get("telegram_user_id")

    if not isinstance(items, list) or not items:
        return jsonify({"ok": False, "error": "Корзина пуста"}), 400
    if not name:
        return jsonify({"ok": False, "error": "Введите имя"}), 400
    if not phone:
        return jsonify({"ok": False, "error": "Введите телефон"}), 400

    lines, total = build_order_lines(items)
    if total <= 0:
        return jsonify({"ok": False, "error": "Некорректные товары в корзине"}), 400

    with orders_lock:
        order_id = len(orders) + 1
        order = {
            "id": order_id,
            "name": name,
            "phone": phone,
            "comment": comment,
            "items": items,
            "total": total,
            "telegram_user_id": telegram_user_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        orders.append(order)

    threading.Thread(target=lambda: asyncio.run(notify_order(order)), daemon=True).start()

    return jsonify({"ok": True, "order_id": order_id, "total": total, "items_text": lines})


def run_flask() -> None:
    logger.info("Flask started | host=0.0.0.0 port=%s", PORT)
    app.run(host="0.0.0.0", port=PORT, threaded=True, use_reloader=False)


def run_bot_polling() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required. Bot polling will not start.")

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    logger.info("Bot polling started | mode=polling")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=False,
        close_loop=False,
    )


def log_startup_config() -> None:
    logger.info("BOT_TOKEN loaded: %s", "yes" if BOT_TOKEN else "no")
    logger.info("ADMIN_ID loaded: %s", "yes" if ADMIN_ID else "no")
    logger.info("APP_URL loaded: %s", "yes" if APP_URL else "no")


if __name__ == "__main__":
    log_startup_config()

    flask_thread = threading.Thread(target=run_flask, daemon=True, name="flask-thread")
    flask_thread.start()

    run_bot_polling()

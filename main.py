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
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO
)
logger = logging.getLogger("toyshop")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8000")
PORT = int(os.getenv("PORT", "8000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")

app = Flask(__name__)

# Демо-каталог: здесь удобно менять товары и фото.
# Для production можно заменить image на /static/img/toy1.jpg и добавить реальные файлы.
PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "toy_001",
        "name": "Плюшевый Мишка Luna",
        "category": "Мягкие игрушки",
        "price": 2490,
        "old_price": 2990,
        "badge": "Хит",
        "description": "Невероятно мягкий мишка из гипоаллергенного плюша для уютных объятий.",
        "image": "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1563901935883-cb10a08a1d7c?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1587654780291-39c9404d746b?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1558060370-d644479cb6f7?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1621600411688-4be93ce4bd45?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1513883049090-d0b7439799bf?auto=format&fit=crop&w=900&q=80",
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
        "image": "https://images.unsplash.com/photo-1607453998774-d533f65dac99?auto=format&fit=crop&w=900&q=80",
        "age_label": "0+",
        "in_stock": True,
    },
]

orders: list[dict[str, Any]] = []
orders_lock = threading.Lock()
app.config["JSON_AS_ASCII"] = False


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
    text = (
        "🌸 <b>Добро пожаловать в Sweet Toys</b>\n\n"
        "Игрушки, которые радуют с первого взгляда.\n"
        "Откройте витрину и соберите заказ за пару минут 💛"
    )
    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    await update.message.reply_text(
        "Быстрый доступ к магазину:",
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
def index():
    catalog_json = json.dumps(PRODUCTS, ensure_ascii=False)
    html = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>Sweet Toys — Premium Kids Store</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg: #fffaf6;
      --card: #ffffff;
      --text: #2a2521;
      --muted: #7e746d;
      --accent: #f1c75b;
      --accent-2: #ffdca3;
      --rose: #f9dfe4;
      --peach: #ffe8d5;
      --shadow: 0 10px 30px rgba(83, 57, 27, 0.08);
      --radius-xl: 24px;
      --radius-lg: 18px;
      --radius-md: 14px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Ubuntu,"Helvetica Neue",Arial,sans-serif;
      background: radial-gradient(circle at top, #fff4ea 0%, var(--bg) 55%);
      color: var(--text);
      padding-bottom: 112px;
      -webkit-font-smoothing: antialiased;
    }
    .container { padding: 16px; max-width: 860px; margin: 0 auto; }
    .header {
      padding: 20px;
      border-radius: var(--radius-xl);
      background: linear-gradient(135deg, #fff8f1, #ffe9dc 50%, #ffe2ed 100%);
      box-shadow: var(--shadow);
      animation: fadeUp .5s ease;
    }
    h1 { margin: 0; font-size: 28px; line-height: 1.1; }
    .sub { margin-top: 10px; color: var(--muted); font-size: 14px; line-height: 1.5; }
    .chip-row { display: flex; gap: 8px; overflow-x: auto; padding: 12px 0 4px; }
    .chip { border: none; background: #fff; padding: 10px 14px; border-radius: 999px; color: #4e443e; box-shadow: var(--shadow); font-size: 13px; white-space: nowrap; }
    .chip.active { background: #2e2a27; color: #fff; }
    .trust { margin: 16px 0; background: #fff; border-radius: var(--radius-lg); padding: 14px; box-shadow: var(--shadow); }
    .trust h3 { margin: 0 0 6px; font-size: 15px; }
    .trust p { margin: 0; color: var(--muted); font-size: 13px; }
    .benefits { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0 18px; }
    .benefit { background: #fff; border-radius: var(--radius-md); padding: 12px; box-shadow: var(--shadow); font-size: 13px; color: #50463f; }
    .section-title { font-size: 19px; margin: 20px 2px 10px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { background: var(--card); border-radius: var(--radius-lg); box-shadow: var(--shadow); overflow: hidden; animation: fadeUp .4s ease; }
    .img-wrap { position: relative; aspect-ratio: 1/1; overflow: hidden; }
    .img-wrap img { width: 100%; height: 100%; object-fit: cover; }
    .badge { position: absolute; top: 10px; left: 10px; background: #2d2a26; color: #fff; border-radius: 999px; padding: 6px 10px; font-size: 11px; }
    .content { padding: 12px; }
    .name { font-weight: 700; margin: 0 0 6px; font-size: 14px; line-height: 1.3; min-height: 36px; }
    .desc { margin: 0; color: var(--muted); font-size: 12px; min-height: 34px; }
    .price-row { margin-top: 10px; display: flex; align-items: center; gap: 8px; }
    .price { font-weight: 700; }
    .old-price { color: #a89e98; text-decoration: line-through; font-size: 12px; }
    .btn { width: 100%; margin-top: 10px; border: none; background: linear-gradient(180deg, #f4d37f, #edbe4e); color: #3d2f15; font-weight: 700; border-radius: 12px; padding: 10px 12px; }
    .sticky-cart {
      position: fixed;
      bottom: calc(84px + env(safe-area-inset-bottom));
      right: 16px;
      z-index: 20;
      border: none;
      background: #2f2a26;
      color: #fff;
      border-radius: 999px;
      padding: 12px 14px;
      box-shadow: 0 12px 30px rgba(0,0,0,.2);
      display: none;
    }
    .bottom-nav {
      position: fixed;
      left: 0; right: 0;
      bottom: 0;
      padding: 10px 16px calc(10px + env(safe-area-inset-bottom));
      background: rgba(255, 250, 246, .92);
      backdrop-filter: blur(14px);
      border-top: 1px solid rgba(80,60,50,.08);
      display: flex;
      gap: 10px;
      z-index: 30;
    }
    .nav-btn { flex: 1; border: none; background: #fff; border-radius: 14px; padding: 12px; font-weight: 600; color: #4f4540; }
    .nav-btn.primary { background: linear-gradient(180deg,#f4d37f,#edbe4e); color: #3d2f15; }
    .sheet {
      position: fixed; left: 0; right: 0; bottom: 0; max-height: 85vh; background: #fff;
      border-radius: 24px 24px 0 0; box-shadow: 0 -20px 40px rgba(0,0,0,.16); padding: 16px;
      transform: translateY(110%); transition: .25s ease; z-index: 50; overflow:auto;
    }
    .sheet.open { transform: translateY(0); }
    .sheet-title { margin: 0 0 12px; font-size: 20px; }
    .cart-item { display: flex; justify-content: space-between; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f0e8e2; }
    .qty { display: inline-flex; gap: 6px; align-items:center; }
    .qty button { width: 24px; height: 24px; border-radius: 8px; border: none; background: #f4eee7; }
    .field { width: 100%; border: 1px solid #e8ddd4; border-radius: 12px; padding: 11px 12px; margin-bottom: 10px; font-size: 14px; }
    .toast { position: fixed; left: 50%; transform: translateX(-50%); bottom: 132px; background: #2d2925; color: #fff; padding: 10px 14px; border-radius: 999px; opacity: 0; transition:.25s; z-index: 60; }
    .toast.show { opacity: 1; }
    .success { text-align:center; padding: 30px 10px; }
    .success .icon { font-size: 54px; animation: pop .4s ease; }
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
  <section class="sheet" id="sheet"></section>
  <div class="toast" id="toast"></div>
<script>
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }
const products = __CATALOG__;
const categories = ['Все', ...new Set(products.map(p => p.category))];
let selectedCategory = 'Все';
let cart = {};
const appEl = document.getElementById('app');
const sheetEl = document.getElementById('sheet');
const toastEl = document.getElementById('toast');
const cartBtn = document.getElementById('cartBtn');
const stickyCart = document.getElementById('stickyCart');
function price(v) { return new Intl.NumberFormat('ru-RU').format(v) + ' ₽'; }
function toast(msg) { toastEl.textContent = msg; toastEl.classList.add('show'); setTimeout(() => toastEl.classList.remove('show'), 1200); }
function renderHome() {
  const chips = categories.map(c => `<button class="chip ${selectedCategory===c?'active':''}" onclick="setCategory('${c}')">${c}</button>`).join('');
  const list = products.filter(p => selectedCategory === 'Все' || p.category === selectedCategory).map(cardTpl).join('');
  appEl.innerHTML = `<header class="header"><h1>Игрушки, которые радуют с первого взгляда</h1><p class="sub">Премиальные материалы, заботливый выбор и удобный заказ прямо в Telegram.</p><div class="chip-row">${chips}</div></header><section class="trust"><h3>Для мам, которые ценят качество</h3><p>Подберём идеальные игрушки и быстро свяжемся после оформления заказа.</p></section><section class="benefits"><div class="benefit">🛡 Безопасные материалы</div><div class="benefit">⚡ Быстрый заказ</div><div class="benefit">💛 Любимые игрушки детей</div><div class="benefit">📲 Удобно заказать в Telegram</div></section><h2 class="section-title">Каталог</h2><section class="grid">${list}</section>`;
  updateCartUI();
}
function cardTpl(p) {
  return `<article class="card"><div class="img-wrap" onclick="openProduct('${p.id}')"><img src="${p.image}" alt="${p.name}" loading="lazy" />${p.badge ? `<span class='badge'>${p.badge}</span>` : ''}</div><div class="content"><p class="name">${p.name}</p><p class="desc">${p.description}</p><div class="price-row"><span class="price">${price(p.price)}</span>${p.old_price ? `<span class='old-price'>${price(p.old_price)}</span>` : ''}</div><button class="btn" onclick="addToCart('${p.id}', 1)">В корзину</button></div></article>`;
}
function setCategory(cat) { selectedCategory = cat; renderHome(); }
function openProduct(id) { const p = products.find(i => i.id === id); if (!p) return; sheetEl.innerHTML = `<h3 class='sheet-title'>${p.name}</h3><img src='${p.image}' style='width:100%;border-radius:16px;max-height:240px;object-fit:cover' /><p style='color:#7d7068'>${p.description}</p><p><b>${price(p.price)}</b> · возраст: ${p.age_label}</p><button class='btn' onclick="addToCart('${p.id}',1); closeSheet();">Добавить в корзину</button>`; openSheet(); }
function addToCart(id, qty) { cart[id] = (cart[id] || 0) + qty; toast('Добавлено в корзину'); updateCartUI(); }
function changeQty(id, delta) { cart[id] = (cart[id] || 0) + delta; if (cart[id] <= 0) delete cart[id]; renderCart(); updateCartUI(); }
function cartItems() { return Object.entries(cart).map(([id, qty]) => { const p = products.find(x => x.id === id); return p ? {id, qty, name: p.name, price: p.price} : null; }).filter(Boolean); }
function cartTotal() { return cartItems().reduce((s, i) => s + i.price * i.qty, 0); }
function updateCartUI() { const count = Object.values(cart).reduce((s, n) => s + n, 0); cartBtn.textContent = `Корзина · ${count}`; stickyCart.style.display = count ? 'block' : 'none'; }
function renderCart() {
  const items = cartItems();
  if (!items.length) { sheetEl.innerHTML = `<h3 class='sheet-title'>Корзина</h3><p style='color:#7d7068'>Пока пусто. Добавьте товары из каталога ✨</p>`; openSheet(); return; }
  sheetEl.innerHTML = `<h3 class='sheet-title'>Корзина</h3>${items.map(i => `<div class='cart-item'><div><div style='font-weight:600'>${i.name}</div><div style='color:#7e746d;font-size:13px'>${price(i.price*i.qty)}</div></div><div class='qty'><button onclick="changeQty('${i.id}',-1)">−</button><b>${i.qty}</b><button onclick="changeQty('${i.id}',1)">+</button></div></div>`).join('')}<p style='font-size:18px'><b>Итого: ${price(cartTotal())}</b></p><button class='btn' onclick='renderCheckout()'>Оформить заказ</button>`;
  openSheet();
}
function renderCheckout() { sheetEl.innerHTML = `<h3 class='sheet-title'>Оформление заказа</h3><input id='name' class='field' placeholder='Ваше имя' /><input id='phone' class='field' placeholder='Телефон' /><textarea id='comment' class='field' rows='3' placeholder='Комментарий к заказу'></textarea><button class='btn' onclick='submitOrder()'>Отправить заказ</button>`; }
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
function renderSuccess(orderId) { sheetEl.innerHTML = `<div class='success'><div class='icon'>✅</div><h3 class='sheet-title'>Заказ #${orderId} принят</h3><p style='color:#7d7068'>Спасибо! Скоро свяжемся с вами 💛</p><button class='btn' onclick='closeSheet();renderHome();'>Вернуться в каталог</button></div>`; }
function openSheet() { sheetEl.classList.add('open'); }
function closeSheet() { sheetEl.classList.remove('open'); }
document.getElementById('homeBtn').onclick = () => { closeSheet(); renderHome(); };
document.getElementById('catalogBtn').onclick = () => { closeSheet(); renderHome(); };
document.getElementById('cartBtn').onclick = renderCart;
stickyCart.onclick = renderCart;
renderHome();
</script>
</body>
</html>
"""
    return html.replace("__CATALOG__", catalog_json)


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "service": "toy-shop", "time": datetime.utcnow().isoformat()})


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

    # Асинхронная отправка уведомлений боту/админу.
    threading.Thread(target=lambda: asyncio.run(notify_order(order)), daemon=True).start()

    return jsonify({"ok": True, "order_id": order_id, "total": total, "items_text": lines})


def run_bot_polling() -> None:
    app_telegram = Application.builder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    logger.info("Telegram bot polling started")
    app_telegram.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot_polling, daemon=True)
    bot_thread.start()

    logger.info("Flask app started on 0.0.0.0:%s", PORT)
    app.run(host="0.0.0.0", port=PORT)

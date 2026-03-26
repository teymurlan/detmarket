# Sweet Toys Telegram WebApp MVP

Минимальный проект интернет-магазина игрушек для Telegram WebApp.

## Файлы проекта
- `main.py` — Flask + Telegram bot (polling) + WebApp UI + API
- `requirements.txt` — зависимости
- `.env.example` — пример переменных окружения

## Быстрый запуск локально
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Далее задайте реальные значения переменных окружения и запустите:
```bash
export BOT_TOKEN="..."
export ADMIN_ID="..."
export APP_URL="http://localhost:8000"
export PORT="8000"
python main.py
```

## Railway
1. Подключите репозиторий в Railway.
2. Добавьте Variables:
   - `BOT_TOKEN`
   - `ADMIN_ID`
   - `APP_URL` (ваш Railway HTTPS URL)
   - `PORT` (`8000` как fallback)
3. Start command: `python main.py`
4. Проверьте healthcheck: `GET /health`

## Если «файлов нет в GitHub»
Из локального репозитория нужно отправить коммиты в удалённый origin:
```bash
git remote -v
git push -u origin HEAD
```

Если `origin` не настроен, добавьте его:
```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin HEAD
```

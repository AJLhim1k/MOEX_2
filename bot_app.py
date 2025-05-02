# bot_app.py
import os
import json
import base64
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from dotenv import load_dotenv
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Загрузка .env
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    raise RuntimeError(".env файл не найден")

bot = Bot(token=os.getenv("TELEGRAM_API_KEY"))
dp = Dispatcher()

# Настройка сессий
secret_key = base64.urlsafe_b64decode(os.getenv("SESSION_SECRET").encode())
storage = EncryptedCookieStorage(secret_key)
middleware = session_middleware(storage)

app = web.Application(middlewares=[middleware])
setup(app, storage)

# ==== ОБРАБОТЧИКИ ====

# bot_app.html — стартовая страница
async def index(request):
    return web.FileResponse('./html_dir/bot_app.html')

# init_session устанавливает user_id, username и score
async def init_session(request):
    session = await get_session(request)
    user_id = request.query.get('user_id')
    username = request.query.get('username')

    if user_id and username:
        session['user_id'] = user_id
        session['username'] = username
        user_id = int(user_id)
        session['score'] = db.get_score(user_id)

    return web.HTTPFound(f'/html_dir/quiz.html?user_id={user_id}&username={username}')

# Команда /start в Telegram
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user = message.from_user
    db.get_or_create_user(user.id, user.first_name)

    web_app_url = (
        f"{os.getenv('WEB_APP_URL')}?user_id={user.id}&username={user.first_name}"
    )

    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Открыть WebApp", web_app=types.WebAppInfo(url=web_app_url))]],
        resize_keyboard=True
    )

    await message.answer(f"Привет, {user.first_name}! Нажми кнопку, чтобы начать!", reply_markup=kb)

async def api_check_user(request):
    session = await get_session(request)
    if not session.get('user_id'):
        return web.json_response({
            'error': 'Unauthorized',
            'user_id': None,
            'username': None,
            'score': 0,
            'limit_reached': True,
            'remaining_attempts': 0  # Добавляем количество оставшихся попыток
        }, status=200)

    user_id = session['user_id']
    username = session['username']
    db.get_or_create_user(user_id, username)
    can_request = db.can_user_request(user_id)
    score = db.get_score(user_id)

    # Определяем количество оставшихся попыток
    remaining_attempts = 20 - db.get_user_requests_today(user_id) # 20 - максимальные попытки в день

    return web.json_response({
        'user_id': user_id,
        'username': username,
        'score': score,
        'limit_reached': can_request,
        'remaining_attempts': remaining_attempts  # Отправляем количество оставшихся попыток
    })

# Получение ответа и обновление очков
async def api_submit_answer(request):
    session = await get_session(request)
    if not session.get('user_id'):
        return web.json_response({'error': 'Unauthorized'}, status=401)

    data = await request.json()
    user_id = session['user_id']
    correct = data.get('correct')
    db.register_user_request(user_id)

    if not db.can_user_request(user_id):
        return web.json_response({'error': 'Лимит попыток исчерпан'}, status=403)

    delta = 5 if correct else -5
    db.update_score(user_id, delta)
    session['score'] = db.get_score(user_id)

    return web.json_response({'new_score': session['score']})

# bot_app.py
async def api_use_attempt(request):
    session = await get_session(request)
    if not session.get('user_id'):
        return web.json_response({'error': 'Unauthorized'}, status=401)

    user_id = int(session['user_id'])

    if not db.can_user_request(user_id):
        return web.json_response({'error': 'Лимит попыток исчерпан'}, status=403)
    remaining = 20 - db.get_user_requests_today(user_id)

    return web.json_response({'ok': True, 'remaining_attempts': remaining})

# bot_app.py (изменения)
async def api_get_rating(request):
    session = await get_session(request)
    if not session.get('user_id'):
        return web.json_response({'error': 'Unauthorized'}, status=401)

    user_id = int(session['user_id'])
    top_players = db.get_top_players(3)
    full_rating = db.get_full_rating()

    # Находим позицию и счет пользователя
    user_position = next(
        (i + 1 for i, user in enumerate(full_rating) if user['id'] == user_id),
        len(full_rating) + 1
    )
    user_score = next(
        (user['score'] for user in full_rating if user['id'] == user_id),
        0
    )

    # Получаем ближайших конкурентов
    nearby_players = []
    if user_position > 3:
        start_idx = max(0, user_position - 3)
        end_idx = min(len(full_rating), user_position + 2)
        nearby_players = full_rating[start_idx:end_idx]

    return web.json_response({
        'top_players': top_players,
        'user_position': user_position,
        'user_score': user_score,
        'nearby_players': nearby_players  # Добавляем ближайших конкурентов
    })


async def serve_list_json(request):
    json_path = os.path.join(questions_path, "list.json")
    if not os.path.exists(json_path):
        return web.json_response({'error': 'Файл list.json не найден'}, status=404)

    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    return web.json_response(data)


# ==== РОУТИНГ ====

questions_path = os.path  .join(BASE_DIR, "questions")
app.router.add_get('/questions/list.json', serve_list_json)
app.router.add_get('/api/get_rating', api_get_rating)
app.router.add_get('/', index)
app.router.add_get('/init_session', init_session)
app.router.add_post('/api/check_user', api_check_user)
app.router.add_post('/api/submit_answer', api_submit_answer)
app.router.add_static('/html_dir/', path=os.path.join(BASE_DIR, 'html_dir'))
app.router.add_static('/questions/', path=questions_path)
app.router.add_post('/api/use_attempt', api_use_attempt)



# Старт aiogram
async def on_startup(app):
    import asyncio
    asyncio.create_task(dp.start_polling(bot))

app.on_startup.append(on_startup)



if __name__ == '__main__':
    web.run_app(app, port=8080)

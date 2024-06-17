import logging
import asyncio
import MySQLdb
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import db_config  # Assuming db_config contains your MySQL connection parameters

API_TOKEN = "YOUR_API_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)

conn = MySQLdb.connect(**db_config)
cursor = conn.cursor()

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

class Survey(StatesGroup):
    start = State()
    age = State()
    familiarity = State()
    previous_site = State()
    communicative = State()
    english_level = State()
    other_languages = State()
    contact_info = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message, state: FSMContext):
    user_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "name": message.from_user.first_name,
        "surname": message.from_user.last_name
    }
    await state.update_data(**user_data)
    await message.answer(
        "Привет 👋 Я чат-бот крутой студии 🌸\n"
        "— Бесплатное обучение работе 💝\n"
        "— Нет ограничений по заработку 💰\n"
        "— Конфиденциальность и безопасность!\n"
        "Для того чтобы оставить заявку на собеседование жми кнопку start 👇",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="start")]], resize_keyboard=True
        )
    )
    await state.set_state(Survey.start)

@dp.message_handler(state=Survey.start)
async def ask_age(message: types.Message, state: FSMContext):
    await Survey.age.set()
    await message.answer("Ваш возраст 🌺", reply_markup=age_keyboard())

def age_keyboard():
    buttons = [
        InlineKeyboardButton(text="18-25", callback_data="age_18-25"),
        InlineKeyboardButton(text="25-33", callback_data="age_25-33"),
        InlineKeyboardButton(text="33-37", callback_data="age_33-37")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@dp.callback_query_handler(state=Survey.age)
async def process_age(callback_query: types.CallbackQuery, state: FSMContext):
    age_group = callback_query.data.split('_')[1]
    await state.update_data(age_group=age_group)
    await save_to_db(state)
    await Survey.familiarity.set()
    await callback_query.message.edit_text("Были ли вы ранее знакомы с этой сферой? 🌹",
                                           reply_markup=familiarity_keyboard())

def familiarity_keyboard():
    buttons = [
        InlineKeyboardButton(text="Да, слышала об этой работе", callback_data="familiar_yes_heard"),
        InlineKeyboardButton(text="Да, ранее работала", callback_data="familiar_yes_worked"),
        InlineKeyboardButton(text="Нет, впервые слышу", callback_data="familiar_no_first_time")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@dp.callback_query_handler(state=Survey.familiarity)
async def process_familiarity(callback_query: types.CallbackQuery, state: FSMContext):
    familiarity = callback_query.data.split('_')[1]
    await state.update_data(familiarity=familiarity)
    await save_to_db(state)
    await Survey.previous_site.set()
    await callback_query.message.edit_text("Если работали ранее, на каком сайте? Если нет, жмите пропустить. 💸",
                                           reply_markup=previous_site_keyboard())

def previous_site_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Bongacams (Рунетки)", callback_data="site_bongacams"),
         InlineKeyboardButton(text="Chaturbate", callback_data="site_chaturbate")],
        [InlineKeyboardButton(text="MyFreeCams", callback_data="site_myfreecams"),
         InlineKeyboardButton(text="Livejasmin", callback_data="site_livejasmin")],
        [InlineKeyboardButton(text="Streamate", callback_data="site_streamate"),
         InlineKeyboardButton(text="Другой вариант", callback_data="site_other")],
        [InlineKeyboardButton(text="Пропустить", callback_data="site_skip")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query_handler(state=Survey.previous_site)
async def process_previous_site(callback_query: types.CallbackQuery, state: FSMContext):
    previous_site = callback_query.data.split('_')[1]
    await state.update_data(previous_site=previous_site)
    await save_to_db(state)
    await Survey.communicative.set()
    await callback_query.message.edit_text("Вы общительный человек? 👭", reply_markup=communicative_keyboard())

def communicative_keyboard():
    buttons = [
        InlineKeyboardButton(text="Да, я открытый и общительный человек🙋‍♀️", callback_data="communicative_yes"),
        InlineKeyboardButton(text="Нет, мне сложно находить общий язык с людьми 🙅‍♀️",
                             callback_data="communicative_no"),
        InlineKeyboardButton(text="Затрудняюсь ответить 🤷‍♀️", callback_data="communicative_unsure")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@dp.callback_query_handler(state=Survey.communicative)
async def process_communicative(callback_query: types.CallbackQuery, state: FSMContext):
    communicative = callback_query.data.split('_')[1]
    await state.update_data(communicative=communicative)
    await save_to_db(state)
    await Survey.english_level.set()
    await callback_query.message.edit_text("Уровень знаний английского языка? 🌼", reply_markup=english_level_keyboard())

def english_level_keyboard():
    buttons = [
        InlineKeyboardButton(text="Высокий ⬆️", callback_data="english_high"),
        InlineKeyboardButton(text="Средний ↔️", callback_data="english_medium"),
        InlineKeyboardButton(text="Низкий ⬇️", callback_data="english_low")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@dp.callback_query_handler(state=Survey.english_level)
async def process_english_level(callback_query: types.CallbackQuery, state: FSMContext):
    english_level = callback_query.data.split('_')[1]
    await state.update_data(english_level=english_level)
    await save_to_db(state)
    await Survey.other_languages.set()
    await callback_query.message.edit_text(
        "Владеете ли вы другими языками (не учитывая Украинский и Русский)? Если да, укажите каким в разделе 'другой'.",
        reply_markup=other_languages_keyboard())

def other_languages_keyboard():
    buttons = [
        InlineKeyboardButton(text="Да ✅", callback_data="languages_yes"),
        InlineKeyboardButton(text="Нет ❎", callback_data="languages_no"),
        InlineKeyboardButton(text="Другой ↔️", callback_data="languages_other")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@dp.callback_query_handler(state=Survey.other_languages)
async def process_other_languages(callback_query: types.CallbackQuery, state: FSMContext):
    other_languages = callback_query.data.split('_')[1]
    await state.update_data(other_languages=other_languages)
    await save_to_db(state)
    await Survey.contact_info.set()
    await callback_query.message.edit_text(
        "Для того чтобы с вами связались наши администраторы, оставьте действующий номер телефона и ссылку на Инстаграм или любые другие соцсети (необязательно) 🌸")

@dp.message_handler(state=Survey.contact_info)
async def process_contact_info(message: types.Message, state: FSMContext):
    contact_info = message.text
    await state.update_data(contact_info=contact_info)
    await save_to_db(state)
    await message.answer("Спасибо! Ваши данные записаны, и с вами свяжутся наши администраторы.",
                         reply_markup=ReplyKeyboardRemove())
    await state.finish()

async def save_to_db(state: FSMContext):
    data = await state.get_data()
    cursor.execute("""
        INSERT INTO responses (user_id, username, name, surname, age_group, familiarity_with_field, previous_site, communicative, english_level, other_languages, phone_number
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                age_group=VALUES(age_group),
                familiarity_with_field=VALUES(familiarity_with_field),
                previous_site=VALUES(previous_site),
                communicative=VALUES(communicative),
                english_level=VALUES(english_level),
                other_languages=VALUES(other_languages),
                phone_number=VALUES(phone_number),
                social_media=VALUES(social_media)
        """, (
        data.get('user_id'), data.get('username'), data.get('name'), data.get('surname'),
        data.get('age_group'), data.get('familiarity'), data.get('previous_site'),
        data.get('communicative'), data.get('english_level'), data.get('other_languages'),
        data.get('contact_info', '').split()[0], ' '.join(data.get('contact_info', '').split()[1:])
    ))
    conn.commit()


if __name__ == "__main__":
    async def on_startup(_):
        await bot.send_message(chat_id='your_admin_chat_id', text="Бот запущен и готов к работе!")


    async def on_shutdown(_):
        await bot.send_message(chat_id='your_admin_chat_id', text="Бот остановлен.")


    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(on_startup(None))
        executor.start_polling(dp, skip_updates=True, on_shutdown=on_shutdown)
    finally:
        loop.run_until_complete(on_shutdown(None))
        loop.close()

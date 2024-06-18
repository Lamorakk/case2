import logging
import asyncio
import MySQLdb
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import db_config

API_TOKEN = "7348976764:AAGhbRFbCs9apuWirkQledQ_QQG-D-ZlBDg"
ADMIN_CHAT_ID = '-1002198942105'

logging.basicConfig(level=logging.INFO)

conn = MySQLdb.connect(**db_config)
cursor = conn.cursor()

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

class Survey(StatesGroup):
    start = State()
    age = State()
    familiarity = State()
    previous_site = State()
    communicative = State()
    english_level = State()
    other_languages = State()
    contact_info = State()

@router.message(CommandStart())
async def send_welcome(message: types.Message, state: FSMContext):
    user_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "name": message.from_user.first_name,
        "surname": message.from_user.last_name
    }
    await state.update_data(**user_data)
    await save_to_db(state)
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

@router.message(Survey.start)
async def ask_age(message: types.Message, state: FSMContext):
    await state.set_state(Survey.age)
    await message.answer("Ваш возраст 🌺", reply_markup=age_keyboard())

def age_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="18-25", callback_data="age_18-25"))
    builder.add(InlineKeyboardButton(text="25-33", callback_data="age_25-33"))
    builder.add(InlineKeyboardButton(text="33-37", callback_data="age_33-37"))
    return builder.as_markup()

@router.callback_query(Survey.age)
async def process_age(callback_query: types.CallbackQuery, state: FSMContext):
    age_group = callback_query.data.split('_')[1]
    await state.update_data(age_group=age_group)
    await save_to_db(state)
    await state.set_state(Survey.familiarity)
    await callback_query.message.edit_text("Были ли вы ранее знакомы с этой сферой? 🌹", reply_markup=familiarity_keyboard())

def familiarity_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да, слышала об этой работе", callback_data="familiar_yes_heard"))
    builder.add(InlineKeyboardButton(text="Да, ранее работала", callback_data="familiar_yes_worked"))
    builder.add(InlineKeyboardButton(text="Нет, впервые слышу", callback_data="familiar_no_first_time"))
    return builder.as_markup()

@router.callback_query(Survey.familiarity)
async def process_familiarity(callback_query: types.CallbackQuery, state: FSMContext):
    familiarity = callback_query.data.split('_')[1]
    await state.update_data(familiarity=familiarity)
    await save_to_db(state)
    await state.set_state(Survey.previous_site)
    await callback_query.message.edit_text("Если работали ранее, на каком сайте? Если нет, жмите пропустить. 💸", reply_markup=previous_site_keyboard())

def previous_site_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Bongacams (Рунетки)", callback_data="site_bongacams"))
    builder.add(InlineKeyboardButton(text="Chaturbate", callback_data="site_chaturbate"))
    builder.add(InlineKeyboardButton(text="MyFreeCams", callback_data="site_myfreecams"))
    builder.add(InlineKeyboardButton(text="Livejasmin", callback_data="site_livejasmin"))
    builder.add(InlineKeyboardButton(text="Streamate", callback_data="site_streamate"))
    builder.add(InlineKeyboardButton(text="Другой вариант", callback_data="site_other"))
    builder.add(InlineKeyboardButton(text="Пропустить", callback_data="site_skip"))
    return builder.as_markup()

@router.callback_query(Survey.previous_site)
async def process_previous_site(callback_query: types.CallbackQuery, state: FSMContext):
    previous_site = callback_query.data.split('_')[1]
    await state.update_data(previous_site=previous_site)
    await save_to_db(state)
    await state.set_state(Survey.communicative)
    await callback_query.message.edit_text("Вы общительный человек? 👭", reply_markup=communicative_keyboard())

def communicative_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да, я открытый и общительный человек🙋‍♀️", callback_data="communicative_yes"))
    builder.add(InlineKeyboardButton(text="Нет, мне сложно находить общий язык с людьми 🙅‍♀️", callback_data="communicative_no"))
    builder.add(InlineKeyboardButton(text="Затрудняюсь ответить 🤷‍♀️", callback_data="communicative_unsure"))
    return builder.as_markup()

@router.callback_query(Survey.communicative)
async def process_communicative(callback_query: types.CallbackQuery, state: FSMContext):
    communicative = callback_query.data.split('_')[1]
    await state.update_data(communicative=communicative)
    await save_to_db(state)
    await state.set_state(Survey.english_level)
    await callback_query.message.edit_text("Уровень знаний английского языка? 🌼", reply_markup=english_level_keyboard())

def english_level_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Высокий ⬆️", callback_data="english_high"))
    builder.add(InlineKeyboardButton(text="Средний ↔️", callback_data="english_medium"))
    builder.add(InlineKeyboardButton(text="Низкий ⬇️", callback_data="english_low"))
    return builder.as_markup()

@router.callback_query(Survey.english_level)
async def process_english_level(callback_query: types.CallbackQuery, state: FSMContext):
    english_level = callback_query.data.split('_')[1]
    await state.update_data(english_level=english_level)
    await save_to_db(state)
    await state.set_state(Survey.other_languages)
    await callback_query.message.edit_text("Владеете ли вы другими языками (не учитывая Украинский и Русский)? Если да, укажите каким в разделе 'другой'.", reply_markup=other_languages_keyboard())

def other_languages_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да ✅", callback_data="languages_yes"))
    builder.add(InlineKeyboardButton(text="Нет ❎", callback_data="languages_no"))
    builder.add(InlineKeyboardButton(text="Другой ↔️", callback_data="languages_other"))
    return builder.as_markup()

@router.callback_query(Survey.other_languages)
async def process_other_languages(callback_query: types.CallbackQuery, state: FSMContext):
    other_languages = callback_query.data.split('_')[1]
    await state.update_data(other_languages=other_languages)
    await save_to_db(state)
    await state.set_state(Survey.contact_info)
    await callback_query.message.edit_text("Для того чтобы с вами связались наши администраторы, оставьте действующий номер телефона и ссылку на Инстаграм или любые другие соцсети (необязательно) 🌸")

@router.message(Survey.contact_info)
async def process_contact_info(message: types.Message, state: FSMContext):
    contact_info = message.text
    await state.update_data(contact_info=contact_info)
    await save_to_db(state)
    await message.answer("Спасибо! Ваши данные записаны, и с вами свяжутся наши администраторы.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

async def save_to_db(state: FSMContext):
    data = await state.get_data()
    contact_info = data.get('contact_info', '')
    contact_parts = contact_info.split()
    phone_number = contact_parts[0] if len(contact_parts) > 0 else None
    social_media = ' '.join(contact_parts[1:]) if len(contact_parts) > 1 else None

    cursor.execute("""
        INSERT INTO responses (user_id, username, name, surname, age_group, familiarity_with_field, previous_site, communicative, english_level, other_languages, phone_number, social_media)
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
        phone_number, social_media
    ))
    conn.commit()

if __name__ == "__main__":
    async def main():
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Бот запущен и готов к работе!")
        await dp.start_polling(bot, skip_updates=True)

    async def shutdown():
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Бот остановлен.")
        await bot.session.close()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(shutdown())

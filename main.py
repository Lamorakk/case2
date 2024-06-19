import asyncio
import logging

import MySQLdb
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardMarkup, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

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
    social_links = State()
    custom_site = State()
    custom_language = State()


@router.message(CommandStart())
async def send_welcome(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = {
        "user_id": user_id,
        "username": message.from_user.username,
        "name": message.from_user.first_name,
        "surname": message.from_user.last_name
    }

    progress = get_user_progress(user_id)

    if progress:
        await state.update_data(**user_data)
        await state.update_data(**progress)
        await message.answer(
            "Welcome back! Resuming your survey.",
            reply_markup=ReplyKeyboardRemove()
        )
        await resume_survey(message, state, progress)
    else:
        await state.update_data(**user_data)
        await save_to_db(state)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=FSInputFile('logo.jpg'),
            caption=(
                "Привет 👋 Я чат-бот крутой студии 🌸\n"
                "— Бесплатное обучение работе 💝\n"
                "— Нет ограничений по заработку 💰\n"
                "— Конфиденциальность и безопасность!\n"
                "Для того чтобы оставить заявку на собеседование жми кнопку start 👇"
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="start")]], resize_keyboard=True, one_time_keyboard=True
            )
        )
        await state.set_state(Survey.start)
@router.message(Survey.start)
async def ask_age(message: types.Message, state: FSMContext):
    await state.set_state(Survey.age)
    await message.answer("Ваш возраст 🌺", reply_markup=age_keyboard())

def age_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="18-25", callback_data="age_18-25")
    builder.button(text="25-33", callback_data="age_25-33")
    builder.button(text="33-37", callback_data="age_33-37")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

@router.callback_query(Survey.age)
async def process_age(callback_query: types.CallbackQuery, state: FSMContext):
    age_group = callback_query.data.split('_')[1]
    await state.update_data(age_group=age_group)
    await save_to_db(state)
    await state.set_state(Survey.familiarity)
    await callback_query.message.edit_text("Были ли вы ранее знакомы с этой сферой? 🌹",
                                           reply_markup=familiarity_keyboard())

def familiarity_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, слышала об этой работе", callback_data="familiar_yes_heard")
    builder.button(text="Да, ранее работала", callback_data="familiar_yes_worked")
    builder.button(text="Нет, впервые слышу", callback_data="familiar_no_first_time")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

@router.callback_query(Survey.familiarity)
async def process_familiarity(callback_query: types.CallbackQuery, state: FSMContext):
    familiarity = callback_query.data.split('_')[1]
    await state.update_data(familiarity=familiarity)
    await save_to_db(state)
    if familiarity == "no_first_time":
        await state.set_state(Survey.communicative)
        await callback_query.message.edit_text("Вы общительный человек? 👭", reply_markup=communicative_keyboard())
    else:
        await state.set_state(Survey.previous_site)
        await callback_query.message.edit_text("Если работали ранее, на каком сайте? Если нет, жмите пропустить. 💸",
                                               reply_markup=previous_site_keyboard())


def previous_site_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Bongacams (Рунетки)", callback_data="site_bongacams")
    builder.button(text="Chaturbate", callback_data="site_chaturbate")
    builder.button(text="MyFreeCams", callback_data="site_myfreecams")
    builder.button(text="Livejasmin", callback_data="site_livejasmin")
    builder.button(text="Streamate", callback_data="site_streamate")
    builder.button(text="Другой вариант", callback_data="site_other")
    builder.button(text="Пропустить", callback_data="site_skip")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

@router.callback_query(Survey.previous_site, F.data == "site_other")
async def ask_custom_site(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(Survey.custom_site)
    await callback_query.message.edit_text("Введите ваш вариант сайта:")

@router.message(Survey.custom_site)
async def process_custom_site(message: types.Message, state: FSMContext):
    custom_site = message.text
    await state.update_data(previous_site=custom_site)
    await save_to_db(state)
    await state.set_state(Survey.communicative)
    await message.answer("Вы общительный человек? 👭", reply_markup=communicative_keyboard())

@router.callback_query(Survey.previous_site)
async def process_previous_site(callback_query: types.CallbackQuery, state: FSMContext):
    previous_site = callback_query.data.split('_')[1]
    if previous_site == "other":
        await state.set_state(Survey.custom_site)
        await callback_query.message.edit_text("Введите ваш вариант сайта:")
    else:
        await state.update_data(previous_site=previous_site)
        await save_to_db(state)
        await state.set_state(Survey.communicative)
        await callback_query.message.edit_text("Вы общительный человек? 👭", reply_markup=communicative_keyboard())

def communicative_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, я открытый и общительный человек🙋‍♀️", callback_data="communicative_yes")
    builder.button(text="Нет, мне сложно находить общий язык с людьми 🙅‍♀️", callback_data="communicative_no")
    builder.button(text="Затрудняюсь ответить 🤷‍♀️", callback_data="communicative_unsure")
    builder.adjust(1, 1, 1)
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
    builder.button(text="Высокий ⬆️", callback_data="english_high")
    builder.button(text="Средний ↔️", callback_data="english_medium")
    builder.button(text="Низкий ⬇️", callback_data="english_low")
    builder.adjust(1, 1, 1)
    return builder.as_markup()

@router.callback_query(Survey.english_level)
async def process_english_level(callback_query: types.CallbackQuery, state: FSMContext):
    english_level = callback_query.data.split('_')[1]
    await state.update_data(english_level=english_level)
    await save_to_db(state)
    await state.set_state(Survey.social_links)
    await callback_query.message.edit_text(
        "Для того чтобы с вами связались наши администраторы, оставьте ссылку на Инстаграм или любые другие соцсети (необязательно(-)) 🌸",
    )
# def other_languages_keyboard():
#     builder = InlineKeyboardBuilder()
#     builder.button(text="Да ✅", callback_data="languages_yes")
#     builder.button(text="Нет ❎", callback_data="languages_no")
#     builder.button(text="Другой ↔️", callback_data="languages_other")
#     builder.adjust(1, 1, 1)
#     return builder.as_markup()
#
# @router.callback_query(Survey.other_languages, F.data == "languages_other")
# async def ask_custom_language(callback_query: types.CallbackQuery, state: FSMContext):
#     await state.set_state(Survey.custom_language)
#     await callback_query.message.edit_text("Введите ваш вариант языка:")
#
# @router.callback_query(Survey.other_languages)
# async def process_custom_languages(callback_query: types.CallbackQuery, state: FSMContext):
#     if callback_query.data == "languages_yes":
#         await state.update_data(other_languages="yes")
#         await save_to_db(state)
#         await state.set_state(Survey.contact_info)
#         await callback_query.message.edit_text(
#             "Для того чтобы с вами связались наши администраторы, оставьте действующий номер телефона(необязательно(-)) 🌸",
#             reply_markup=contact_info_keyboard())
#     elif callback_query.data == "languages_no":
#         await state.update_data(other_languages="no")
#         await save_to_db(state)
#         await state.set_state(Survey.contact_info)
#         await callback_query.message.edit_text(
#             "Для того чтобы с вами связались наши администраторы, оставьте действующий номер телефона(необязательно(-)) 🌸",
#             reply_markup=contact_info_keyboard())
#     elif callback_query.data == "languages_other":
#         await state.set_state(Survey.custom_language)
#         await callback_query.message.edit_text("Введите ваш вариант языка:")


# def contact_info_keyboard():
#     builder = InlineKeyboardBuilder()
#     builder.button(text="Share phone number", callback_data="share_phone_number")
#     builder.button(text="Skip", callback_data="skip")
#     builder.adjust(1)
#     return builder.as_markup()

# @router.callback_query(F.data == "share_phone_number", Survey.contact_info)
# async def ask_for_phone(callback_query: types.CallbackQuery, state: FSMContext):
#     await callback_query.message.answer(
#     "Please share your phone number by clicking the button below.",
#     reply_markup=ReplyKeyboardMarkup(
#     keyboard=[[KeyboardButton(text="Share phone number", request_contact=True)]],
#     resize_keyboard=True,
#     one_time_keyboard=True,)
#     )
# @router.message(F.content_type == types.ContentType.CONTACT, Survey.contact_info)
# async def process_phone_number(message: types.Message, state: FSMContext):
#     phone_number = message.contact.phone_number
#     await state.update_data(phone_number=phone_number)
#     await save_to_db(state)
#     await message.delete()
#     await state.set_state(Survey.social_links)
#     await message.answer(
#         "Также можете оставить ссылку на Инстаграм или любые другие соцсети (необязательно(-)) 🌸"
#     )

# @router.callback_query(F.data == "skip", Survey.contact_info)
# async def skip_contact_info(callback_query: types.CallbackQuery, state: FSMContext):
#     await state.update_data(phone_number=None)
#     await save_to_db(state)
#     await state.set_state(Survey.social_links)
#     await callback_query.message.answer(
#         "Также можете оставить ссылку на Инстаграм или любые другие соцсети (необязательно(-)) 🌸"
#     )

@router.message(Survey.social_links)
async def process_social_links(message: types.Message, state: FSMContext):
    social_links = message.text
    await state.update_data(social_links=social_links)
    await save_to_db(state)
    await message.answer("Спасибо! Ваши данные записаны, и с вами свяжутся наши администраторы.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

async def resume_survey(message: types.Message, state: FSMContext, progress):
    if 'age_group' not in progress:
        await state.set_state(Survey.age)
        await message.answer("Ваш возраст 🌺", reply_markup=age_keyboard())
    elif 'familiarity' not in progress:
        await state.set_state(Survey.familiarity)
        await message.answer("Были ли вы ранее знакомы с этой сферой? 🌹", reply_markup=familiarity_keyboard())
    elif 'previous_site' not in progress:
        await state.set_state(Survey.previous_site)
        await message.answer("Если работали ранее, на каком сайте? Если нет, жмите пропустить. 💸",
                             reply_markup=previous_site_keyboard())
    elif 'communicative' not in progress:
        await state.set_state(Survey.communicative)
        await message.answer("Вы общительный человек? 👭", reply_markup=communicative_keyboard())
    elif 'english_level' not in progress:
        await state.set_state(Survey.english_level)
        await message.answer("Уровень знаний английского языка? 🌼", reply_markup=english_level_keyboard())
    elif 'social_links' not in progress:
        await state.set_state(Survey.social_links)
        await message.answer(
            "Также можете оставить ссылку на Инстаграм или любые другие соцсети (необязательно(-)) 🌸"
        )
    else:
        await state.clear()
        await message.answer("Спасибо! Ваши данные записаны, и с вами свяжутся наши администраторы.", reply_markup=ReplyKeyboardRemove())

def get_user_progress(user_id):
    cursor.execute("SELECT * FROM responses WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()

    if result:
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, result))
    return {}

async def save_to_db(state: FSMContext):
    data = await state.get_data()
    user_id = data.get('user_id')
    cursor.execute("SELECT * FROM responses WHERE user_id = %s", (user_id,))
    existing_data = cursor.fetchone()

    if existing_data:
        for key, value in data.items():
            if key not in existing_data or existing_data[key] != value:
                cursor.execute(f"UPDATE responses SET {key} = %s WHERE user_id = %s", (value, user_id))
    else:
        cursor.execute("""
            INSERT INTO responses (user_id, username, name, surname, age_group, familiarity, previous_site, communicative, social_links)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
            data.get('user_id'), data.get('username'), data.get('name'), data.get('surname'),
            data.get('age_group'), data.get('familiarity'), data.get('previous_site'),
            data.get('communicative'), data.get('social_links')
        ))
    conn.commit()

    if data.get('social_links'):
        await send_registration_info_to_channel(bot, data)



async def send_registration_info_to_channel(bot: Bot, user_data: dict):
    message_text = (
        f"New Registration:\n"
        f"Username: @{user_data.get('username')}\n"
        f"Name: {user_data.get('name')}\n"
        f"Surname: {user_data.get('surname')}\n"
        f"Age Group: {user_data.get('age_group')}\n"
        f"Familiarity: {user_data.get('familiarity')}\n"
        f"Previous Site: {user_data.get('previous_site')}\n"
        f"Communicative: {user_data.get('communicative')}\n"
        f"Social Links: {user_data.get('social_links')}\n"
    )
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=message_text)


if __name__ == "__main__":
    async def main():
        # await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Бот запущен и готов к работе!")
        await dp.start_polling(bot, skip_updates=True)

    async def shutdown():
        # await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Бот остановлен.")
        await bot.session.close()

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(shutdown())

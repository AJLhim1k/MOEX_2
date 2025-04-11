import asyncio
import types
import emoji
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import message, KeyboardButton, ReplyKeyboardMarkup, FSInputFile, CallbackQuery
from aiogram.filters.command import Command
import random
import os
from aiogram.fsm.state import State, StatesGroup
from kots import make_graph

class GameState(StatesGroup):
    waiting_for_answer = State()

load_dotenv()
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
bot = Bot(token=TELEGRAM_API_KEY)
dp = Dispatcher()


@dp.message(Command('викторина'))
async def send_welcome(message: message, state: FSMContext):
    kb = [
        [KeyboardButton(text="Long shares", )],
        [KeyboardButton(text="Short shares")],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Хмм...")
    _, _, files = next(os.walk(".\questions"))
    file_count = len(files) + 99
    pic = random.randint(100, file_count)
    make_graph(pic, "q")
    await state.update_data(current_pic=pic)
    await message.answer_photo(photo=FSInputFile(f'.\questions\plot{pic}.png'), caption="Начнем игру!\nОпредели, есть ли на данном графике манипуляуция?", reply_markup=keyboard)
    await state.set_state(GameState.waiting_for_answer)


@dp.message(GameState.waiting_for_answer)
async def handle_answer(message: message, state: FSMContext):
    kb = [
        [KeyboardButton(text="Я молодец..?", )],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Хмм...")
    data = await state.get_data()
    pic = data.get("current_pic")
    make_graph(pic, "ans")
    await state.update_data(current_pic=pic)
    user_response = message.text
    if user_response == "Long shares":
        kb = [
            [KeyboardButton(text="Круто! Назад в меню", )],
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Хмм...")
        await message.answer_photo(photo=FSInputFile(f'.\\answers\plot{pic}.png'), caption="Молодец, ты был прав!", reply_markup=keyboard)
    elif user_response == "Short shares":
        kb = [
            [KeyboardButton(text="Плаки-плаки, назад в меню", )],
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Хмм...")
        await message.answer_photo(photo=FSInputFile(f'.\\answers\plot{pic}.png'), caption="Нет", reply_markup=keyboard)



@dp.message(F.text.lower() == "я молодец..?")
async def nice(message: message):
    await message.reply("Да, друг, ты как всегда прав!!!")


@dp.message(F.text.lower() == "ура")
async def nice(message: message):
    kb = [
        [KeyboardButton(text="А сколько стоит сбер?")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="SBEEEEEEEEEEEER", one_time_keyboard=True)
    await message.reply("Ты крутой, друг", reply_markup=keyboard)


@dp.message(F.text.lower() == "а сколько стоит сбер?")
async def photo(message: message):
    await message.answer_photo(photo=FSInputFile('INDA7fFP_big.png', filename='SBER'), caption="А вот столько!", reply_markup=keyboard())


@dp.message(F.text.lower() == "pum")
async def photo(message: message):
    await message.answer_photo(photo=FSInputFile('INDA7fFP_big.png', filename='SBER'), caption="А вот столько!", reply_markup=keyboard())


def keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text=emoji.emojize(":up_arrow:"), callback_data="tralalelo")
    kb.button(text=emoji.emojize(":down_arrow:"), callback_data="tralalelo")
    return kb.as_markup()


@dp.message(F.text.lower() == "lalala")
async def photo(message: message):
    kb = keyboard()
    await message.reply("Ты крутой, друг", reply_markup=kb)


@dp.message(F.text.lower() == "tralalelo")
async def photo(message: message):
    await message.reply("Ты крутой, друг")


@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    if callback.data == "tralalelo":
        await callback.answer("Кнопка нажата!")
        await callback.message.answer("Ты нажал на кнопку tralalelo 🎉")


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

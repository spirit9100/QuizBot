import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from module.questions import quiz_data
import module.db as db
from module.config import API_TOKEN

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"right_answer_{option}" if option == right_answer else f"wrong_answer_{option}")
        )

    builder.adjust(2)
    return builder.as_markup()


@dp.callback_query(F.data.startswith("right_answer"))
async def right_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )
    answer = callback.data.replace("right_answer_", "")

    result = await db.get_quiz_result(callback.from_user.id)
    result += 1


    await callback.message.answer(answer + " правильный ответ!")

    current_question_index = await db.get_quiz_index(callback.from_user.id)
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await db.update_quiz_index(callback.from_user.id, current_question_index)
    await db.update_quiz_result(callback.from_user.id, result)
    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data.startswith("wrong_answer"))
async def wrong_answer(callback: types.CallbackQuery):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса из словаря состояний пользователя
    answer = callback.data.replace("wrong_answer_", "")
    current_question_index = await db.get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]['correct_option']

    await callback.message.answer(
        f"{answer} Неправильный ответ!\n Правильный ответ: {quiz_data[current_question_index]['options'][correct_option]}")

    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await db.update_quiz_index(callback.from_user.id, current_question_index)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    builder.add(types.KeyboardButton(text="Результаты"))
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команду /result
@dp.message(F.text == "Результаты")
@dp.message(Command("result"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Результаты квиза:\n{await db.get_quiz_result(message.from_user.id)}")


async def get_question(message, user_id):
    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await db.get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    current_question_index = 0
    result = 0
    await db.update_quiz_index(user_id, current_question_index)
    await db.update_quiz_result(user_id, result)
    await get_question(message, user_id)


# Хэндлер на команду /quiz
@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)


# Запуск процесса поллинга новых апдейтов
async def main():
    # Запускаем создание таблицы базы данных
    await db.create_table()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

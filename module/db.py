import aiosqlite

from module.config import DB_NAME


async def create_table():
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index 
        INTEGER, result INTEGER)''')
        # Сохраняем изменения
        await db.commit()


async def update_quiz_index(user_id, index):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT INTO quiz_state (user_id, question_index) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE  SET question_index = ?', (user_id, index,index))
        # Сохраняем изменения
        await db.commit()


async def get_quiz_index(user_id):
    # Подключаемся к базе данных
    async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def get_quiz_result(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT result FROM quiz_state WHERE user_id = (?)', (user_id,)) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def update_quiz_result(user_id, result):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE quiz_state SET result = (?) WHERE user_id = (?)', (result, user_id,))
        await db.commit()

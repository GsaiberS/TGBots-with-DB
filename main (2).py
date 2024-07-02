import telebot
import sqlite3

bot = telebot.TeleBot('YOUR TOKEN TG BOTS')


db_file = 'bot.db'
conn = sqlite3.connect(db_file, check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY,
    category TEXT,
    question TEXT,
    answer_yes TEXT,
    answer_no TEXT
)
''')
conn.commit()


questions_data = [
    ('Перегрузка по току ETM', 'Силовые кабели затянуты?', 'Сопротивление изоляции в норме?',
     'Плохой контакт силовых кабелей'),
    ('Перегрузка по току ETM', 'Сопротивление изоляции в норме?', 'Вал вращается свободно?',
     'Пробой изоляции /Обрыв фазы обмотки статора'),
    ('Перегрузка по току ETM', 'Вал вращается свободно?', 'Номер контакта совпадает с номером клеммы?', 'Разрушение подшипников вала'),
    ('Перегрузка по току ETM', 'Номер контакта совпадает с номером клеммы?', 'Обнаружены следы оплавления клеммы?',
     'Неправильное подключение'),
    ('Перегрузка по току ETM', 'Обнаружены следы оплавления клеммы?',
     'Нарушение контакта (замена клеммы или гнезда подключения)', 'Имеется обрыв провода?'),
    ('Перегрузка по току ETM', 'Имеется обрыв провода?', 'Обрыв провода', 'Проблемы не найдено'),


    ('Авария запуска дизельного двигателя', 'IsolatingSwitch в положении 0?', 'Перевод IsolatingSwitch в положение 1',
     'Имеются видимые повреждения дизельного двигателя?'),
    ('Авария запуска дизельного двигателя', 'Имеются видимые повреждения дизельного двигателя?',
     'Поиск механической поломки', 'Напряжение на стартере ниже 25 В?'),
    ('Авария запуска дизельного двигателя', 'Напряжение на стартере ниже 25 В?',
     'Выход из строя одного из стартерных аккумуляторов', 'Стартерные аккумуляторы подключены правильно?'),
    ('Авария запуска дизельного двигателя', 'Стартерные аккумуляторы подключены правильно?',
     'Имеют дефекты на тяге актуатора?', 'Неправильное подключение стартерных аккумуляторов'),
    ('Авария запуска дизельного двигателя', 'Имеют дефекты на тяге актуатора?', 'Поломка тяги актуатора',
     'Воздух поступает в дизельный двигатель?'),
    ('Авария запуска дизельного двигателя', 'Воздух поступает в дизельный двигатель?',
     'Топливо поступает в дизельный двигатель?', 'Перекрыта подача воздуха во впускной коллектор'),
    ('Авария запуска дизельного двигателя', 'Топливо поступает в дизельный двигатель? ', 'Проблемы не найдено', 'Перекрыта подача топлива/Отключение топливного насоса/Засорение топливного бака/Воздушная пробка/Открыт клапан слива топлива' ),

]
cursor.executemany('''
INSERT INTO questions (category, question, answer_yes, answer_no)
VALUES (?, ?, ?, ?)
''', questions_data)
conn.commit()


user_states = {}



@bot.message_handler(commands=['start'])
def handle_start(message):
    return_to_main_menu(message)



def return_to_main_menu(message):
    bot.send_message(message.chat.id, 'Привет! Выберите где произошел отказ:', reply_markup=keyboard_markup())
    user_states[message.chat.id] = {'state': 'start'}



def keyboard_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Перегрузка по току ETM', 'Авария запуска дизельного двигателя')
    return markup



@bot.message_handler(
    func=lambda message: message.text in ['Перегрузка по току ETM', 'Авария запуска дизельного двигателя'])
def handle_choice(message):
    if message.text == 'Перегрузка по току ETM':
        user_states[message.chat.id] = {'state': 'question', 'category': 'Перегрузка по току ETM', 'question_id': 1}
        ask_question(message)
    elif message.text == 'Авария запуска дизельного двигателя':
        user_states[message.chat.id] = {'state': 'question', 'category': 'Авария запуска дизельного двигателя',
                                        'question_id': 7}
        ask_question(message)



def keyboard_yes_no():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Да', 'Нет')
    return markup



def ask_question(message):
    chat_id = message.chat.id
    state = user_states[chat_id]
    cursor.execute('SELECT question FROM questions WHERE id = ?', (state['question_id'],))
    question = cursor.fetchone()[0]
    bot.send_message(chat_id, question, reply_markup=keyboard_yes_no())



@bot.message_handler(func=lambda message: message.text in ['Да', 'Нет'])
def handle_answer(message):
    chat_id = message.chat.id
    state = user_states[chat_id]
    cursor.execute('SELECT answer_yes, answer_no FROM questions WHERE id = ?', (state['question_id'],))
    answers = cursor.fetchone()

    if message.text == 'Да':
        next_question = answers[0]
    elif message.text == 'Нет':
        next_question = answers[1]

    if next_question in ['Проблемы не обнаружены', 'Разрушение подшипников вала', 'Неправильное подключение',
                         'Нарушение контакта (замена клеммы или гнезда подключения)', 'Обрыв провода',
                         'Проблемы не найдено']:
        bot.send_message(chat_id, f'Решение: {next_question}')
        return_to_main_menu(message)
    else:
        cursor.execute('SELECT id FROM questions WHERE category = ? AND question = ?',
                       (state['category'], next_question))
        next_question_id = cursor.fetchone()
        if next_question_id:
            user_states[chat_id]['question_id'] = next_question_id[0]
            ask_question(message)
        else:
            bot.send_message(chat_id, f'Решение: {next_question}')
            return_to_main_menu(message)


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
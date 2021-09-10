from mysql.connector import connect, Error
from flask import Flask, jsonify, request

OPTIONS_FILE_PATH = "options.txt"
DB_NAME = "sample_database"


class ControllerRAM:
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в оперативной памяти.
    Он может быть подключен к классу Repo в качестве одного из дух возможных контроллеров.
    Другая возможность - использовать контроллер ControllerDB
    """

    def __init__(self, options):
        """
        Простая инициализация
        Формат базы: список словарей с данными пользователей
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__db = []  # Инициализируется база пользователей.

    def get_user(self, user_id):
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает -1
        """
        for entry in self.__db:
            if entry["id"] == user_id:
                return entry
        return -1

    def get_users(self):
        """
        Возвращает всех пользователей в базе
        :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает -1
        """
        result = self.__db
        if len(result) != 0:
            return result
        return -1

    def add_user(self, user_id, title):
        """
        Добавляет нового пользователя в базу
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        new_user = {"id": user_id, "title": title}
        if self.get_user(user_id) == -1:
            self.__db.append(new_user)
            return 0
        return -1

    def get_index(self, user_id):
        """
        Вспомогательная процедура для поиска индекса пользователя по известному id.
        Нужна, так как база реализована в виде списка
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует, то возвращает индекс, иначе возвращает -1
        """
        for i in range(len(self.__db)):
            entry = self.__db[i]
            if entry["id"] == user_id:
                return i
        return -1

    def del_user(self, user_id):
        """
        Удаляет одного пользователя из базы
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        i = self.get_index(user_id)
        if i != -1:
            del self.__db[i]
            return 0
        return -1

    def upd_user(self, user_id, title):
        """
        Обновляет данные пользователя в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
        """
        new_user = {"id": user_id, "title": title}
        i = self.get_index(user_id)
        if i != -1:
            self.__db[i] = new_user
            return 0
        return -1


class ControllerDB:
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в базе данных.
    Работает с базами MySQL. Используется доступ по логину и паролю
    Он может быть подключен к классу Repo в качестве одного из дух возможных контроллеров.
    Другая возможность - использовать контроллер ControllerRAM.
    """

    def __init__(self, options):
        """
        Простая инициализация
        :param options: словарь параметров. Загружается из файла. Для данного контроллера используются параметры
            username, password
        """
        self.__options = options
        self.init_db()

    def get_db_connection(self):
        """
        Вспомогательная процедура для создания подключения к базе данных, расположенной на локальном компьютере.
        В качестве параметров использует логин и пароль, хранимые в словаре __options.
        В качестве имени базы использует значение глобальной константы DB_NAME
        :return: если подключение к базе успешно, то возвращает объект mysql.connector.connect, иначе возвращает -1
        """
        try:
            return connect(
                host="localhost",
                user=self.__options["username"],
                password=self.__options["password"],
                database=DB_NAME,
            )
        except Error as e:
            print(e)
            return -1

    def make_query(self, query, user_id=0, title=""):
        """
        Вспомогательная процедура для создания запросов к базе данных
        Использует передачу именованных параметров для противостояния атакам SQL injection
        Если при вызове программист передал небезопасный запрос, то исключения не возникает
        :param query: строка запроса к базе, отформатированная в соответствии со стандартами MySQL
        :param user_id: целочисленное значение id пользователя для передачи в качестве параметра в запрос
        :param title: строковое значение ФИО пользователя для передачи в качестве параметра в запрос
        :return: возвращает ответ от базы данных.
        Это может быть список словарей с данными пользователей в случае запроса SELECT,
        либо пустая строка в других случаях
        Если запрос к базе возвращает исключение, то данная процедура возвращает -1
        """
        try:
            conn = self.get_db_connection()  # Создать подключение
            with conn.cursor(dictionary=True) as cursor:  # параметр dictionary указывает, что курсор возвращает словари
                cursor.execute(query, {'user_id': user_id, 'title': title})  # выполнить запрос безопасным образом
                result = cursor.fetchall()  # получить результаты выполнения
                cursor.close()  # вручную закрыть курсор
            conn.commit()  # вручную указать, что транзакции завершены
            conn.close()  # вручную закрыть соединение
            return result
        except Error as err:
            print(f"Error with db: {err}")
            return -1

    def init_db(self):
        """
        Инициализация базы данных
        :return: возвращает всегда 0, так как исключения обрабатываются в вызываемой процедуре
        """
        self.make_query(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")  # создать базу с именем DB_NAME, если не существует
        # self.make_query("DROP TABLE IF EXISTS users;")  # не удаляем таблицу из предыдущих запусков
        # далее создать таблицу.
        # id: целочисленное без автоматического инкремента
        # title: строковое с максимальной длинной 255
        self.make_query("""CREATE TABLE IF NOT EXISTS users (
                           id INT PRIMARY KEY,
                           title VARCHAR(255) NOT NULL);""")
        return 0

    def get_user(self, user_id):
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает -1
        """
        result = self.make_query("SELECT * FROM users WHERE id = %(user_id)s", user_id=user_id)
        if len(result) == 0:
            return -1
        return result[0]

    def get_users(self):
        """
        Возвращает всех пользователей в базе
        :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает -1
        """
        result = self.make_query("SELECT * FROM users")
        if len(result) == 0:
            return -1
        return result

    def add_user(self, user_id, title):
        """
        Добавляет нового пользователя в базу
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.get_user(user_id) == -1:
            self.make_query("INSERT INTO users (id, title) VALUES (%(user_id)s, %(title)s);",
                            user_id=user_id, title=title)
            return 0
        return -1

    def del_user(self, user_id):
        """
        Удаляет одного пользователя из базы
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get_user(user_id) != -1:
            self.make_query("DELETE FROM users WHERE id = %(user_id)s;", user_id=user_id)
            return 0
        return -1

    def upd_user(self, user_id, title):
        """
        Обновляет данные пользователя в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
        """
        if self.get_user(user_id) != -1:
            self.make_query("UPDATE users SET title = %(title)s WHERE id = %(user_id)s",
                            user_id=user_id, title=title)
            return 0
        return -1


class Repo:
    """
    Этот класс загружает в качестве контроллера один из двух вариантов:
        ControllerDB для хранения записей пользователей в MySQL базе данных или
        ControllerRAM для хранения записей пользователей в оперативной памяти.
    Также он загружает настройки программы из файла при помощи метода get_options()
    Методы get_user(), get_users(), add_user(), del_user(), upd_user() - это интерфейсы подключения контроллера
    """
    def __init__(self):
        """
        Простая инициализация. Запускает получение настроек программы. Выбирает один из двух контроллеров
        """
        self.__options = self.get_options()
        if self.__options["use_db_repo"]:
            self.__controller = ControllerDB(self.__options)
        else:
            self.__controller = ControllerRAM(self.__options)

    @staticmethod
    def get_options():
        """
        Вспомогательный статический метод.
        Считывает настройки программы из файла OPTIONS_FILE_PATH.
        Рекомендации по форматированию параметров приведены в комментариях в файле.
        :return: словарь с настройками
            use_db_repo: принимает значение True, если в данные пользователей хранятся в MySQL базе, иначе False
            username: логин для доступа к базе
            password: пароль для доступа к базе
        """

        options = {"use_db_repo": False, "username": None, "password": None}  # настройки по умолчанию

        try:
            s = open(OPTIONS_FILE_PATH, "rt", encoding="utf-8")
            stream = list(s)
            s.close()
        except OSError:
            print("Got exception while reading options from file")
            return options

        for line in stream:  # начало считывания параметров
            if line.lstrip().startswith("#"):  # do not read comments
                continue
            # прочитать содержимое следующей строки из файла
            line = line.rstrip("\r\n")  # вручную убрать символы перевода строки и возврата каретки
            fragments = line.split(":")  # выделить ключ и значение из строки
            # считать значение параметра для выбора контроллера
            if "use_db_repo" in fragments[0]:
                if "True" in fragments[1]:
                    options["use_db_repo"] = True
            # считать значение логина
            elif "username" in fragments[0]:
                options["username"] = fragments[1]
            # считать значение пароля
            elif "password" in fragments[0]:
                options["password"] = fragments[1]

        return options

    def get_user(self, user_id):
        """
        Передаёт управление контроллеру, а тот возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает -1
        """
        result = self.__controller.get_user(user_id)
        return result

    def get_users(self):
        """
        Передаёт управление контроллеру, а тот возвращает всех пользователей в базе
        :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает -1
        """
        result = self.__controller.get_users()
        return result

    def add_user(self, user_id, title):
        """
        Передаёт управление контроллеру, а тот добавляет нового пользователя в базу
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        result = self.__controller.add_user(user_id, title)
        return result

    def del_user(self, user_id):
        """
        Передаёт управление контроллеру, а тот удаляет одного пользователя из базы
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        result = self.__controller.del_user(user_id)
        return result

    def upd_user(self, user_id, title):
        """
        Передаёт управление контроллеру, а тот обновляет данные пользователя в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
        """
        result = self.__controller.upd_user(user_id, title)
        return result


"""
Начало работы REST API сервиса
Небольшие приложения Flask принято разрабатывать в процедурном подходе
"""
app = Flask(__name__)  # инициализация объекта, с которым сможет работать WSGI сервер
app.config['SECRET_KEY'] = 'gh5ng843bh68hfi4nfc6h3ndh4xc53b56lk89gm4bf2gc6ehm'  # произвольная случайная длинная строка
repo = Repo()  # инициализация репозитория. Область видимости - глобальная


@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/user/2
    :param user_id: целочисленное значение id пользователя
    :return: если пользователь найден в базе, то возвращает json с данными пользователя и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: {"id": user_id, "title": title}
    """
    user = repo.get_user(user_id)
    if user == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return jsonify(user), 200


@app.route('/users', methods=['GET'])
def get_users():
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/users
    :return: если база не пуста, то возвращает json с данными пользователей и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: [{"id": user_id1, "title": title1}, {"id": user_id2, "title": title2}]
    """
    users = repo.get_users()
    if users == -1:
        return "Rejected. DB is empty", 404
    return jsonify(users), 200


@app.route('/user/<int:user_id>', methods=['POST'])
def add_user(user_id):
    """
    Точка входа для запроса на добавление записи пользователя по id. Пример запроса:
    curl -X POST http://localhost:80/user/3?title=Mikhail%20Vasilevich%20Lomonosov
    :param user_id: целочисленное значение id пользователя
    :аргумент запроса title: строковое значение ФИО пользователя
    :return: если пользователь существует в базе, то не создаёт пользователя и возвращает код 422,
             иначе создаёт и возвращает код 204
    """
    title = request.args.get('title')
    if repo.add_user(user_id, title) == -1:
        return "Rejected. User with id=" + str(user_id) + " already exists", 422
    return 'Success. User created', 204


@app.route('/user/<int:user_id>', methods=['DELETE'])
def del_user(user_id):
    """
    Точка входа для запроса на удаление записи пользователя по id. Пример запроса:
    curl -X DELETE http://localhost:80/user/3
    :param user_id: целочисленное значение id пользователя
    :return: если пользователь не существует в базе, то возвращает код 422,
             иначе удаляет его и возвращает код 204
    """
    if repo.del_user(user_id) == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User deleted', 204


@app.route('/user/<int:user_id>', methods=['PATCH'])
def upd_user(user_id):
    """
    Точка входа для запроса на изменение записи пользователя по id. Пример запроса:
    curl -X PATCH http://localhost:80/user/3?title=Aleksandr%20Sergeevich%20Pushkin
    :param user_id: целочисленное значение id пользователя
    :аргумент запроса title: строковое значение ФИО пользователя
    :return: если пользователь не существует в базе, то возвращает код 422,
             иначе изменяет его данные и возвращает код 204
    """
    title = request.args.get('title')
    result = repo.upd_user(user_id, title)
    if result == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User updated', 204


if __name__ == '__main__':
    """
    Тестовый запуск сервиса. Активируется только при непосредственном запуске приложения.
    При запуске через WSGI-сервер этот блок игнорируется
    """
    repo.add_user(1, "Pyotr Pervy")
    repo.add_user(2, "Aleksandr Sergeevich Pushkin")
    app.run(host="127.0.0.1", port=80)



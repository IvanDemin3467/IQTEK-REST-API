from __future__ import annotations
from abc import ABC, abstractmethod

from mysql.connector import connect, Error
from flask import Flask, jsonify, request

OPTIONS_FILE_PATH = "options.txt"
DB_NAME = "sample_database"
REPOSITORY_CREATION_METHOD = "from-file"

# Factory fot entities start
class Entity:
    def __init__(self, entity_id: int, title: str) -> None:
        self.id = entity_id
        self.title = title


# AbstractRepository start
class AbstractRepository(ABC):

    @abstractmethod
    def get(self, reference) -> Entity:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[Entity]:
        raise NotImplementedError

    @abstractmethod
    def add(self, entity: Entity) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete(self, reference) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, reference) -> Entity:
        raise NotImplementedError


class RepositoryRAM(AbstractRepository):
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в оперативной памяти.
    Он может быть подключен к классу RepositoryCreatorFromFile в качестве одного из дух возможных контроллеров.
    Другая возможность - использовать контроллер RepositoryMySQL
    """

    def __init__(self, options: dict):
        """
        Простая инициализация
        Формат базы: список словарей с данными пользователей
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__db = []  # Инициализируется база пользователей.

    def __get_index(self, user_id: int) -> int:
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

    def get(self, user_id: int) -> dict:
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает {}
        """
        for entry in self.__db:
            if entry["id"] == user_id:
                return entry
        return {}

    def list(self) -> list:
        """
        Возвращает всех пользователей в базе
        :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает []
        """
        result = self.__db
        if len(result) != 0:
            return result
        return []

    def add(self, entity: Entity) -> int:
        """
        Добавляет нового пользователя в базу
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        new_user = {"id": entity.id, "title": entity.title}
        if self.get(entity.id) == {}:
            self.__db.append(new_user)
            return 0
        return -1

    def delete(self, user_id: int) -> int:
        """
        Удаляет одного пользователя из базы
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(user_id)
        if i != -1:
            del self.__db[i]
            return 0
        return -1

    def update(self, entity: Entity) -> int:
        """
        Обновляет данные пользователя в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
        """
        new_user = {"id": entity.id, "title": entity.title}
        i = self.__get_index(entity.id)
        if i != -1:
            self.__db[i] = new_user
            return 0
        return -1


class RepositoryMySQL(AbstractRepository):
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в базе данных.
    Работает с базами MySQL. Используется доступ по логину и паролю
    Он может быть подключен к классу RepositoryCreatorFromFile в качестве одного из дух возможных контроллеров.
    Другая возможность - использовать контроллер RepositoryRAM.
    """

    def __init__(self, options: dict):
        """
        Простая инициализация
        :param options: словарь параметров. Загружается из файла. Для данного контроллера используются параметры
            username, password
        """
        self.__options = options
        self.__init_db()

    def __get_db_connection(self):
        """
        Вспомогательная процедура для создания подключения к базе данных, расположенной на локальном компьютере.
        В качестве параметров использует логин и пароль, хранимые в словаре __options.
        В качестве имени базы использует значение глобальной константы DB_NAME
        :return: если подключение к базе успешно, то возвращает объект mysql.connector.connect, иначе возвращает None
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
            return None

    def __make_query(self, query: str, user_id=0, title="") -> list:
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
        Если запрос к базе возвращает исключение, то данная процедура возвращает []
        """
        try:
            conn = self.__get_db_connection()  # Создать подключение
            with conn.cursor(dictionary=True) as cursor:  # параметр dictionary указывает, что курсор возвращает словари
                cursor.execute(query, {'user_id': user_id, 'title': title})  # выполнить запрос безопасным образом
                result = cursor.fetchall()  # получить результаты выполнения
                cursor.close()  # вручную закрыть курсор
            conn.commit()  # вручную указать, что транзакции завершены
            conn.close()  # вручную закрыть соединение
            return result
        except Error as err:
            print(f"Error with db: {err}")
            return []

    def __init_db(self) -> int:
        """
        Инициализация базы данных
        :return: возвращает всегда 0, так как исключения обрабатываются в вызываемой процедуре
        """
        self.__make_query(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")  # создать базу с именем DB_NAME, если не существует
        self.__make_query("DROP TABLE IF EXISTS users;")  # удаляем таблицу из предыдущих запусков
        # далее создать таблицу.
        # id: целочисленное без автоматического инкремента
        # title: строковое с максимальной длинной 255
        self.__make_query("""CREATE TABLE IF NOT EXISTS users (
                           id INT PRIMARY KEY,
                           title VARCHAR(255) NOT NULL);""")
        return 0

    def get(self, user_id: int) -> dict:
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает {}
        """
        result = self.__make_query("SELECT * FROM users WHERE id = %(user_id)s", user_id=user_id)
        if len(result) == 0:
            return {}
        return result[0]

    def list(self) -> list:
        """
        Возвращает всех пользователей в базе
        :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает []
        """
        result = self.__make_query("SELECT * FROM users")
        if len(result) == 0:
            return []
        return result

    def add(self, entity: Entity):
        """
        Добавляет нового пользователя в базу
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id) == {}:
            self.__make_query("INSERT INTO users (id, title) VALUES (%(user_id)s, %(title)s);",
                              user_id=entity.id, title=entity.title)
            return 0
        return -1

    def delete(self, user_id: int):
        """
        Удаляет одного пользователя из базы
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get(user_id) != {}:
            self.__make_query("DELETE FROM users WHERE id = %(user_id)s;", user_id=user_id)
            return 0
        return -1

    def update(self, entity: Entity):
        """
        Обновляет данные пользователя в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id) != {}:
            self.__make_query("UPDATE users SET title = %(title)s WHERE id = %(user_id)s",
                              user_id=entity.id, title=entity.title)
            return 0
        return -1


class AbstractRepositoryCreator(ABC):
    @abstractmethod
    def factory(self) -> AbstractRepository:
        raise NotImplementedError


class InterfaceRepositoryCreator:
    def create(self):
        if REPOSITORY_CREATION_METHOD == "from-file":
            return RepositoryCreatorFromFile()


class RepositoryCreatorFromFile(AbstractRepositoryCreator):
    """
    Этот класс загружает в качестве контроллера один из двух вариантов:
        RepositoryMySQL для хранения записей пользователей в MySQL базе данных или
        RepositoryRAM для хранения записей пользователей в оперативной памяти.
    Также он загружает настройки программы из файла при помощи метода get_options()
    Методы get_user(), get_users(), add_user(), del_user(), upd_user() - это интерфейсы подключения контроллера
    """
    def __init__(self):
        """
        Простая инициализация. Запускает получение настроек программы. Выбирает один из двух контроллеров
        """
        self.__options = self.__get_options()
        if self.__options["use_db_repo"]:
            self.__controller = RepositoryMySQL(self.__options)
        else:
            self.__controller = RepositoryRAM(self.__options)

    @staticmethod
    def __get_options():
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

    def factory(self) -> AbstractRepository:
        return self.__controller


# Sample Factory start

class Creator(ABC):
    """
    Класс Создатель объявляет фабричный метод, который должен возвращать объект
    класса Продукт. Подклассы Создателя обычно предоставляют реализацию этого
    метода.
    """

    @abstractmethod
    def factory_method(self):
        """
        Обратите внимание, что Создатель может также обеспечить реализацию
        фабричного метода по умолчанию.
        """
        pass

    def some_operation(self) -> str:
        """
        Также заметьте, что, несмотря на название, основная обязанность
        Создателя не заключается в создании продуктов. Обычно он содержит
        некоторую базовую бизнес-логику, которая основана на объектах Продуктов,
        возвращаемых фабричным методом. Подклассы могут косвенно изменять эту
        бизнес-логику, переопределяя фабричный метод и возвращая из него другой
        тип продукта.
        """

        # Вызываем фабричный метод, чтобы получить объект-продукт.
        product = self.factory_method()

        # Далее, работаем с этим продуктом.
        result = f"Creator: The same creator's code has just worked with {product.operation()}"

        return result


"""
Конкретные Создатели переопределяют фабричный метод для того, чтобы изменить тип
результирующего продукта.
"""


class ConcreteCreator1(Creator):
    """
    Обратите внимание, что сигнатура метода по-прежнему использует тип
    абстрактного продукта, хотя фактически из метода возвращается конкретный
    продукт. Таким образом, Создатель может оставаться независимым от конкретных
    классов продуктов.
    """

    def factory_method(self) -> Product:
        return ConcreteProduct1()


class ConcreteCreator2(Creator):
    def factory_method(self) -> Product:
        return ConcreteProduct2()


class Product(ABC):
    """
    Интерфейс Продукта объявляет операции, которые должны выполнять все
    конкретные продукты.
    """

    @abstractmethod
    def operation(self) -> str:
        pass


"""
Конкретные Продукты предоставляют различные реализации интерфейса Продукта.
"""


class ConcreteProduct1(Product):
    def operation(self) -> str:
        return "{Result of the ConcreteProduct1}"


class ConcreteProduct2(Product):
    def operation(self) -> str:
        return "{Result of the ConcreteProduct2}"


def client_code(creator: Creator) -> None:
    """
    Клиентский код работает с экземпляром конкретного создателя, хотя и через
    его базовый интерфейс. Пока клиент продолжает работать с создателем через
    базовый интерфейс, вы можете передать ему любой подкласс создателя.
    """

    print(f"Client: I'm not aware of the creator's class, but it still works.\n"
          f"{creator.some_operation()}", end="")


if __name__ == "__main__":
    print("App: Launched with the ConcreteCreator1.")
    client_code(ConcreteCreator1())
    print("\n")

    print("App: Launched with the ConcreteCreator2.")
    client_code(ConcreteCreator2())

# Factory end


"""
Начало работы REST API сервиса
Небольшие приложения Flask принято разрабатывать в процедурном подходе
"""
app = Flask(__name__)  # инициализация объекта, с которым сможет работать WSGI сервер
app.config['SECRET_KEY'] = 'gh5ng843bh68hfi4nfc6h3ndh4xc53b56lk89gm4bf2gc6ehm'  # произвольная случайная длинная строка
repo = InterfaceRepositoryCreator().create().factory()  # инициализация репозитория


@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id: int) -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/user/2
    :param user_id: целочисленное значение id пользователя
    :return: если пользователь найден в базе, то возвращает json с данными пользователя и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: {"id": user_id, "title": title}
    """
    user = repo.get(user_id)
    if user == {}:
        return "Rejected. No user with id=" + str(user_id), 404
    return jsonify(user), 200


@app.route('/users', methods=['GET'])
def get_users() -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/users
    :return: если база не пуста, то возвращает json с данными пользователей и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: [{"id": user_id1, "title": title1}, {"id": user_id2, "title": title2}]
    """
    result = repo.list()
    if not result:
        return "Rejected. DB is empty", 404
    users = []
    # for entity in result:
    #     # entry = "id: " + str(entity.id) + ", title: " + str(entity.title)
    #     users.append(entry)
    return jsonify(result), 200


@app.route('/user/<int:user_id>', methods=['POST'])
def add_user(user_id: int) -> (str, int):
    """
    Точка входа для запроса на добавление записи пользователя по id. Пример запроса:
    curl -X POST http://localhost:80/user/3?title=Mikhail%20Vasilevich%20Lomonosov
    :param user_id: целочисленное значение id пользователя
    :аргумент запроса title: строковое значение ФИО пользователя
    :return: если пользователь существует в базе, то не создаёт пользователя и возвращает код 422,
             иначе создаёт и возвращает код 204
    """
    title = request.args.get('title')
    entity = Entity(user_id, title)
    if repo.add(entity) == -1:
        return "Rejected. User with id=" + str(user_id) + " already exists", 422
    return 'Success. User created', 204


@app.route('/user/<int:user_id>', methods=['DELETE'])
def del_user(user_id: int) -> (str, int):
    """
    Точка входа для запроса на удаление записи пользователя по id. Пример запроса:
    curl -X DELETE http://localhost:80/user/3
    :param user_id: целочисленное значение id пользователя
    :return: если пользователь не существует в базе, то возвращает код 422,
             иначе удаляет его и возвращает код 204
    """
    if repo.delete(user_id) == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User deleted', 204


@app.route('/user/<int:user_id>', methods=['PATCH'])
def upd_user(user_id: int) -> (str, int):
    """
    Точка входа для запроса на изменение записи пользователя по id. Пример запроса:
    curl -X PATCH http://localhost:80/user/3?title=Aleksandr%20Sergeevich%20Pushkin
    :param user_id: целочисленное значение id пользователя
    :аргумент запроса title: строковое значение ФИО пользователя
    :return: если пользователь не существует в базе, то возвращает код 422,
             иначе изменяет его данные и возвращает код 204
    """
    title = request.args.get('title')
    entity = Entity(user_id, title)
    result = repo.update(entity)
    if result == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User updated', 204


if __name__ == '__main__':
    """
    Тестовый запуск сервиса. Активируется только при непосредственном запуске приложения.
    При запуске через WSGI-сервер этот блок игнорируется
    """
    app.run(host="127.0.0.1", port=80)

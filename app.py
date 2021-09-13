from __future__ import annotations
from abc import ABC, abstractmethod

from mysql.connector import connect, Error
from flask import Flask, jsonify, request

OPTIONS_FILE_PATH = "options.txt"
DB_NAME = "sample_database"
REPOSITORY_CREATION_METHOD = "from-file"


# Factory fot entities start
class Entity(ABC):
    def __init__(self, entity_id: int, properties: dict) -> None:
        self.id = entity_id
        self.properties = properties

    @abstractmethod
    def get_dict(self):
        pass


class User(Entity):
    def __init__(self, user_id: int, properties: dict) -> None:
        if user_id == -1:
            properties = {"title": ""}
        super().__init__(user_id, properties)

    def get_dict(self):
        result = {"id": self.id}
        result.update(self.properties)
        return result


class AbstractFactory(ABC):
    @abstractmethod
    def create(self, entity_id: int, properties: dict):
        raise NotImplementedError

    @abstractmethod
    def create_empty(self, entity_id: int, properties: dict):
        raise NotImplementedError

    @abstractmethod
    def get_factory_name(self) -> str:
        raise NotImplementedError


class UserFactory(AbstractFactory):
    def create(self, user_id: int, properties: dict) -> Entity:
        user = User(user_id, properties)
        return user

    def create_empty(self) -> Entity:
        user = User(-1, {"title": ""})
        return user

    def get_factory_name(self) -> str:
        return "user"


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
    def update(self, reference) -> int:
        raise NotImplementedError


class RepositoryRAM(AbstractRepository):
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в оперативной памяти.
    Он может быть подключен к классу RepositorySelector в качестве одного из дух возможных контроллеров.
    Другая возможность - использовать контроллер RepositoryMySQL
    """

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        Формат базы: список словарей с данными пользователей
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__db = []  # Инициализируется база пользователей.
        self.__factory = fact

    def __get_index(self, user_id: int) -> int:
        """
        Вспомогательная процедура для поиска индекса пользователя по известному id.
        Нужна, так как база реализована в виде списка
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует, то возвращает индекс, иначе возвращает -1
        """
        for i in range(len(self.__db)):
            if self.__db[i].id == user_id:
                return i
        return -1

    def get(self, user_id: int) -> Entity:
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает {}
        """
        for entity in self.__db:
            if entity.id == user_id:
                return entity
        return self.__factory.create_empty()

    def list(self) -> list[Entity]:
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
        if self.__get_index(entity.id) == -1:
            self.__db.append(entity)
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
        i = self.__get_index(entity.id)
        if i != -1:
            self.__db[i] = entity
            return 0
        return -1


class RepositoryMySQL(AbstractRepository):
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в базе данных.
    Работает с базами MySQL. Используется доступ по логину и паролю
    Он может быть подключен к классу RepositorySelector в качестве одного из дух возможных контроллеров.
    Другая возможность - использовать контроллер RepositoryRAM.
    """

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        :param factory:
        :param options: словарь параметров. Загружается из файла. Для данного контроллера используются параметры
            username, password
        """
        self.__options = options
        self.__init_db()
        self.__factory = fact

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

    def get(self, user_id: int) -> Entity:
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает {}
        """
        result = self.__make_query("SELECT * FROM users WHERE id = %(user_id)s", user_id=user_id)
        if len(result) == 0:
            return self.__factory.create_empty()
        entity = result[0]
        return self.__factory.create(entity["id"], {"title": entity["title"]})

    def list(self) -> list:
        """
        Возвращает всех пользователей в базе
        :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает []
        """
        entities_list = self.__make_query("SELECT * FROM users")
        if len(entities_list) == 0:
            return []
        result = []
        for entity in entities_list:
            result.append(self.__factory.create(entity["id"], {"title": entity["title"]}))
        return result

    def add(self, entity: Entity) -> int:
        """
        Добавляет нового пользователя в базу
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id == -1:
            self.__make_query("INSERT INTO users (id, title) VALUES (%(user_id)s, %(title)s);",
                              user_id=entity.id, title=entity.properties["title"])
            return 0
        return -1

    def delete(self, user_id: int) -> int:
        """
        Удаляет одного пользователя из базы
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get(user_id).id != -1:
            self.__make_query("DELETE FROM users WHERE id = %(user_id)s;", user_id=user_id)
            return 0
        return -1

    def update(self, entity: Entity) -> int:
        """
        Обновляет данные пользователя в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param title: строковое значение ФИО пользователя
        :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id != -1:
            self.__make_query("UPDATE users SET title = %(title)s WHERE id = %(user_id)s",
                              user_id=entity.id, title=entity.properties["title"])
            return 0
        return -1

#
# class InterfaceRepository:
#     def __init__(self, fact: AbstractFactory):
#         self.factory = fact
#         self.__repository = RepositoryCreator().create()
#
#     def get(self, user_id: int) -> dict:
#         """
#         Передаёт управление контроллеру, а тот возвращает одного пользователя по id
#         :param user_id: целочисленное значение id пользователя
#         :return: если пользователь найден в базе, то возвращает словарь с данными пользователя, иначе возвращает {}
#         """
#         result = self.__repository.get(user_id)
#         return result
#
#     def list(self) -> list[dict]:
#         """
#         Передаёт управление контроллеру, а тот возвращает всех пользователей в базе
#         :return: если база не пуста, то возвращает список словарей с данными пользователей, иначе возвращает []
#         """
#         result = self.__repository.list()
#         return result
#
#     def add(self, entity: Entity) -> int:
#         """
#         Передаёт управление контроллеру, а тот добавляет нового пользователя в базу
#         :param user_id: целочисленное значение id пользователя
#         :param title: строковое значение ФИО пользователя
#         :return: если пользователь с таким id не существует, то возвращает 0, иначе возвращает -1
#         """
#
#         result = self.__repository.add(entity)
#         return result
#
#     def delete(self, user_id: int) -> int:
#         """
#         Передаёт управление контроллеру, а тот удаляет одного пользователя из базы
#         :param user_id: целочисленное значение id пользователя
#         :return: если пользователь с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
#         """
#         result = self.__repository.delete(user_id)
#         return result
#
#     def update(self, entity: Entity) -> int:
#         """
#         Передаёт управление контроллеру, а тот обновляет данные пользователя в соответствии с переданными параметрами
#         :param user_id: целочисленное значение id пользователя
#         :param title: строковое значение ФИО пользователя
#         :return: если пользователь с таким id существует, то возвращает 0, иначе возвращает -1
#         """
#         result = self.__repository.update(entity)
#         return result


class AbstractRepositoryCreator(ABC):
    @abstractmethod
    def create(self) -> AbstractRepository:
        raise NotImplementedError


class RepositoryCreator(AbstractRepositoryCreator):
    """
    Этот класс загружает в качестве контроллера один из двух вариантов:
        RepositoryMySQL для хранения записей пользователей в MySQL базе данных или
        RepositoryRAM для хранения записей пользователей в оперативной памяти.
    Также он загружает настройки программы из файла при помощи метода get_options()
    Методы get_user(), get_users(), add_user(), del_user(), upd_user() - это интерфейсы подключения контроллера
    """
    def __init__(self, fact: AbstractFactory):
        """
        Простая инициализация
        :param factory:
        :param options: словарь параметров. Загружается из файла. Для данного контроллера используются параметры
            username, password
        """
        self.factory = fact

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

    def create(self) -> AbstractRepository:
        if REPOSITORY_CREATION_METHOD == "from-file":
            self.__select_from_file()
        return self.__repository

    def __select_from_file(self) -> None:
        self.__options = self.__get_options()
        if self.__options["use_db_repo"]:
            self.__repository = RepositoryMySQL(self.__options, self.factory)
        else:
            self.__repository = RepositoryRAM(self.__options, self.factory)


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
factory = UserFactory()  # инициализация фабрики сущностей пользователей
repo = RepositoryCreator(factory).create()  # инициализация репозитория


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
    if user.id == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return jsonify(user.get_dict()), 200


@app.route('/users', methods=['GET'])
def get_users() -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/users
    :return: если база не пуста, то возвращает json с данными пользователей и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: [{"id": user_id1, "title": title1}, {"id": user_id2, "title": title2}]
    """
    entities_list = repo.list()
    if not entities_list:
        return "Rejected. DB is empty", 404
    result = []
    for entity in entities_list:
        result.append(entity.get_dict())
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
    user = factory.create(user_id, {'title': title})
    if repo.add(user) == -1:
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
    user = factory.create(user_id, {'title': title})
    result = repo.update(user)
    if result == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User updated', 204


if __name__ == '__main__':
    """
    Тестовый запуск сервиса. Активируется только при непосредственном запуске приложения.
    При запуске через WSGI-сервер этот блок игнорируется
    """
    app.run(host="127.0.0.1", port=80)

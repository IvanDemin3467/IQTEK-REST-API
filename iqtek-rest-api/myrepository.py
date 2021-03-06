from __future__ import annotations

from mysql.connector import connect, Error
import json  # to read options from file
import sys  # for repository factory (it creates class by name (string))

import time

from myfactory import *


def measure_time(func):
    def inner(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            ex_time = time.time() - start_time
            print(f'Execution time: {ex_time:.2f} seconds')
    return inner


def memoize(func):
    _cache = {}

    def wrapper(*args, **kwargs):
        name = func.__name__
        key = (name, args, frozenset(kwargs.items()))
        if key in _cache:
            return _cache[key]
        response = func(*args, **kwargs)
        _cache[key] = response
        return response
    return wrapper


OPTIONS_FILE_PATH = "options.json"
DB_NAME = "sample_database"


# Repository start
class AbstractRepository(ABC):
    """
    Абстрактный репозиторий для работы с сущностями Entity
    Предполагает реализацию методов get(), list(), add(), delete(), update()
    """

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


class RepositoryBytearray(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в массиве байтов.
    Работает быстрее, чем repositoryRAM, так как сложность чтения О(1)
    Но есть ограничения:
        фиксированная длина записи
        сложнее удалять записи из репозитория
    Он может быть создан при помощи RepositoryCreator в качестве одного из возможных вариантов.
    """
    __id_length = 2
    __title_length = 40
    __entry_length = __title_length
    __db_length = 4

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        Формат репозитория: bytearray
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        :param fact: фабрика. Используется при необходимости создать сущность Entity, возвращаемую из репозитория
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__factory = fact  # Сохраняется фабрика сущностей
        self.__db = bytearray(self.__title_length * self.__db_length)  # Инициализируется база пользователей.

    def __get_address(self, user_id: int) -> tuple[int, int]:
        """
        Вспомогательная функция.Преобразует ID сущности в начальный и конечный адрес в репозитории
        :param user_id: user_id: целочисленное значение id сущности
        :return: кортеж, состоящий из первого и конечного адресов в репозитории
        """
        first_byte = (user_id - 1) * self.__entry_length
        last_byte = first_byte + self.__entry_length
        return first_byte, last_byte

    @measure_time
    def get(self, user_id: int) -> Entity:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param user_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность,
            иначе возвращает пустую сущность
        """
        first_byte, last_byte = self.__get_address(user_id)
        if self.__db[first_byte] != 0:
            response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
            return self.__factory.create(user_id, {"title": response})
        return self.__factory.empty_entity

    @measure_time
    def list(self) -> list[Entity]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = []
        for i in range(self.__db_length):
            first_byte, last_byte = self.__get_address(i)
            if self.__db[first_byte] != 0:
                response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
                results.append(self.__factory.create(i, {"title": response}))

        if len(results) != 0:
            return results
        return []

    @measure_time
    def add(self, entity: Entity) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(entity.id)
        title = entity.properties["title"]
        to_db = bytearray(title, 'utf-8')
        if self.__db[first_byte] == 0:
            for i in range(len(to_db)):
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1

    @measure_time
    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория
        :param user_id: целочисленное значение id пользователя
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(user_id)
        if self.__db[first_byte] != 0:
            for i in range(self.__entry_length):
                self.__db[first_byte + i] = 0
            return 0
        return -1

    @measure_time
    def update(self, entity: Entity) -> int:
        """
        Обновляет данные сущности в репозитории в соответствии с переданными параметрами
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(entity.id)
        title = entity.properties["title"]
        to_db = bytearray(title, 'utf-8')
        if self.__db[first_byte] != 0:
            for i in range(len(to_db)):
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1


class RepositoryRAM(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в оперативной памяти.
    Он может быть создан при помощи RepositoryCreator в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryMySQL
    """

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        Формат репозитория: список сущностей Entity
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        :param fact: фабрика. Используется при необходимости создать сущность Entity, возвращаемую из репозитория
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__factory = fact  # Сохраняется фабрика сущностей
        self.__db = []  # Инициализируется база пользователей.

    def __get_index(self, user_id: int) -> int:
        """
        Вспомогательная процедура для поиска индекса записи в репозитории по известному id.
        Нужна, так как репозиторий реализован в виде списка
        :param user_id: целочисленное значение id сущности
        :return: если сущность с таким id существует, то возвращает индекс, иначе возвращает -1
        """
        for i in range(len(self.__db)):
            if self.__db[i].id == user_id:
                return i
        return -1

    @measure_time
    def get(self, user_id: int) -> Entity:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param user_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность,
            иначе возвращает пустую сущность
        """
        for entity in self.__db:
            if entity.id == user_id:
                return entity
        return self.__factory.empty_entity

    @measure_time
    def list(self) -> list[Entity]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = self.__db
        if len(results) != 0:
            return results
        return []

    @measure_time
    def add(self, entity: Entity) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.__get_index(entity.id) == -1:
            self.__db.append(entity)
            return 0
        return -1

    @measure_time
    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория
        :param user_id: целочисленное значение id пользователя
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(user_id)
        if i != -1:
            del self.__db[i]
            return 0
        return -1

    @measure_time
    def update(self, entity: Entity) -> int:
        """
        Обновляет данные сущности в репозитории в соответствии с переданными параметрами
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(entity.id)
        if i != -1:
            self.__db[i] = entity
            return 0
        return -1


class RepositoryMySQL(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в базе данных MySQL.
    Используется доступ по логину и паролю
    Класс может быть создан при помощи фабрики RepositoryCreator в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryRAM.
    """

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        :param options: словарь параметров. Для данного репозитория используются параметры username, password
        :param fact: фабрика сущностей. Используется при необходимости создать сущность, возвращаемую из репозитория
        """
        self.__options = options  # Сохранить настройки
        self.__init_db()  # Инициализировать базу данных
        self.__factory = fact  # Сохранить фабрику сущностей
        self._cache = {}  # Инициализировать простой кэш

    def __get_db_connection(self) -> connect:
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
                database=DB_NAME)
        except Error as err:
            print(err)
            return None

    def __make_query(self, query: str, user_id=0, title="") -> list:
        """
        Вспомогательная процедура для создания запросов к базе данных
        Использует передачу именованных параметров для противостояния атакам SQL injection
        Если при вызове передан небезопасный запрос, то исключения не возникает
        :param query: строка запроса к базе, отформатированная в соответствии со стандартами MySQL
        :param user_id: целочисленное значение id сущности для передачи в качестве параметра в запрос
        :param title: строковое значение заголовка сущности для передачи в качестве параметра в запрос
        :return: возвращает ответ от базы данных.
        Это может быть список словарей с параметрами сущностей в случае запроса SELECT,
            либо пустая строка в других случаях
        Если запрос к базе возвращает исключение, то данная процедура возвращает []
        """
        try:
            conn = self.__get_db_connection()  # Создать подключение
            with conn.cursor(dictionary=True) as cursor:  # параметр dictionary указывает, что курсор возвращает словари
                cursor.execute(query, {'user_id': user_id, 'title': title})  # выполнить запрос безопасным образом
                results = cursor.fetchall()  # получить результаты выполнения
                cursor.close()  # вручную закрыть курсор
            conn.commit()  # вручную указать, что транзакции завершены
            conn.close()  # вручную закрыть соединение
            return results
        except Error as err:
            print(f"Error with db: {err}")
            return []

    def __init_db(self) -> int:
        """
        Инициализация базы данных
        :return: возвращает всегда 0, так как исключения обрабатываются в вызываемой процедуре __make_query()
        """
        self.__make_query(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")  # создать базу с именем DB_NAME, если не существует
        self.__make_query("DROP TABLE IF EXISTS users;")  # удаляем таблицу из предыдущих запусков
        # далее создать таблицу.
        #   id: целочисленное без автоматического инкремента
        #   title: строковое с максимальной длинной 255
        self.__make_query("""CREATE TABLE IF NOT EXISTS users (
                           id INT PRIMARY KEY,
                           title VARCHAR(255) NOT NULL);""")
        return 0

    def __clear_cache(self) -> None:
        """
        Clears cache. Use it on every DB-changing operation
        :return: None
        """
        self._cache = {}

    @measure_time
    def get(self, user_id: int) -> Entity:
        """
        Возвращает одного пользователя по id.
        Использует простой кэш на словаре.
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает сущность пользователя, иначе возвращает пустую сущность
        """
        key = ("get", user_id)
        if key in self._cache:
            results = self._cache[key]
        else:
            results = self.__make_query("SELECT * FROM users WHERE id = %(user_id)s", user_id=user_id)
            self._cache[key] = results

        if len(results) == 0:
            return self.__factory.empty_entity
        entity = results[0]
        return self.__factory.create(entity["id"], {"title": entity["title"]})

    @measure_time
    def list(self) -> list[Entity]:
        """
        Возвращает всех пользователей в базе
        :return: если репозиторий не пуст, то возвращает список c сущностями из него, иначе возвращает []
        """
        entities_list = self.__make_query("SELECT * FROM users")
        if len(entities_list) == 0:
            return []
        results = []
        for entity in entities_list:
            results.append(self.__factory.create(entity["id"], {"title": entity["title"]}))
        return results

    @measure_time
    def add(self, entity: Entity) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id == -1:
            self.__make_query("INSERT INTO users (id, title) VALUES (%(user_id)s, %(title)s);",
                              user_id=entity.id, title=entity.properties["title"])
            self.__clear_cache()
            return 0
        return -1

    @measure_time
    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория по id
        :param user_id: целочисленное значение id сущности
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get(user_id).id != -1:
            self.__make_query("DELETE FROM users WHERE id = %(user_id)s;", user_id=user_id)
            self.__clear_cache()
            return 0
        return -1

    @measure_time
    def update(self, entity: Entity) -> int:
        """
        Обновляет хранимую сущность в соответствии с переданным параметром
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает обновляет её и возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id != -1:
            self.__make_query("UPDATE users SET title = %(title)s WHERE id = %(user_id)s",
                              user_id=entity.id, title=entity.properties["title"])
            self.__clear_cache()
            return 0
        return -1


class AbstractRepositoryCreator(ABC):
    """
    Это интерфейс к фабрике репозиториев. Предполагает реализацию только одного классового метода create()
    """
    @classmethod
    @abstractmethod
    def create(cls, fact: AbstractFactory) -> AbstractRepository:
        raise NotImplementedError


class RepositoryCreator(AbstractRepositoryCreator):
    """
    Это класс-фабрика репозиториев. Он возвращает в качестве репозитория один из двух инстансов:
        RepositoryMySQL для хранения записей пользователей в MySQL базе данных или
        RepositoryRAM для хранения записей пользователей в оперативной памяти.
    Также класс умеет загружать настройки программы из файла при помощи метода __get_options()
    Единственный доступный извне метод - классовый метод create(), возвращающий выбранный репозиторий
    """
    @staticmethod
    def __get_options():
        """
        Вспомогательный статический метод.
        Считывает настройки программы из файла OPTIONS_FILE_PATH.
        :return: словарь с настройками
            repo_type: содержит имя класса, который будет создаваться этой фабрикой репозиториев. Возможные значения:
                RepositoryMySQL - хранит сущности в базе MySQL
                RepositoryRAM - хранит сущности в оперативной памяти
            username: логин для доступа к базе
            password: пароль для доступа к базе
        """

        options = {"use_db_repo": False, "username": None, "password": None}  # настройки по умолчанию

        try:
            json_file = open(OPTIONS_FILE_PATH)
            json_object = json.load(json_file)
            json_file.close()
        except OSError:
            print("Got exception while reading options from file")
            return options

        try:
            options["repo_type"] = json_object['repo_type']
            options["username"] = json_object['username']
            options["password"] = json_object['password']
        except KeyError:
            print(f"The file {OPTIONS_FILE_PATH} is not formatted correctly")

        return options

    @classmethod
    def create(cls, fact: AbstractFactory) -> AbstractRepository:
        """
        Выбирает тип используемого репозитория в зависимости от параметра repo_type, полученного из файла
        :param fact: фабрика сущностей; передаётся репозиторию
        :return: инстанс выбранного репозитория
        """
        options = cls.__get_options()
        repository_class = getattr(sys.modules[__name__], options["repo_type"])
        repository = repository_class(options, fact)
        print("Working with", repository)
        return repository

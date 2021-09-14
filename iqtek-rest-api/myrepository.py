from __future__ import annotations

from mysql.connector import connect, Error
import json

from myfactory import *


OPTIONS_FILE_PATH = "options.json"
DB_NAME = "sample_database"
REPOSITORY_CREATION_METHOD = "from-file"


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


class RepositoryRAM(AbstractRepository):
    """
    Этот класс обеспечивает взаимодействие с репозиторием, хранящимся в оперативной памяти.
    Он может быть создан при помощи RepositoryCreator в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryMySQL
    """

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        Формат репозитория: список сущностей Entity
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        :param fact: фабрика. Используется при необходимости создать сущность User, возвращаемую из репозитория
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__factory = fact  # Сохраняется фабрика
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

    def list(self) -> list[Entity]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        result = self.__db
        if len(result) != 0:
            return result
        return []

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
    Этот класс обеспечивает хранений сущностей Entity в базе данных MySQL.
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
        self.__options = options
        self.__init_db()
        self.__factory = fact

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

    def get(self, user_id: int) -> Entity:
        """
        Возвращает одного пользователя по id
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает сущность пользователя, иначе возвращает пустую сущность
        """
        result = self.__make_query("SELECT * FROM users WHERE id = %(user_id)s", user_id=user_id)
        if len(result) == 0:
            return self.__factory.empty_entity
        entity = result[0]
        return self.__factory.create(entity["id"], {"title": entity["title"]})

    def list(self) -> list[Entity]:
        """
        Возвращает всех пользователей в базе
        :return: если репозиторий не пуст, то возвращает список c сущностями из него, иначе возвращает []
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
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id == -1:
            self.__make_query("INSERT INTO users (id, title) VALUES (%(user_id)s, %(title)s);",
                              user_id=entity.id, title=entity.properties["title"])
            return 0
        return -1

    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория по id
        :param user_id: целочисленное значение id сущности
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get(user_id).id != -1:
            self.__make_query("DELETE FROM users WHERE id = %(user_id)s;", user_id=user_id)
            return 0
        return -1

    def update(self, entity: Entity) -> int:
        """
        Обновляет хранимую сущность в соответствии с переданным параметром
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает обновляет её и возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id != -1:
            self.__make_query("UPDATE users SET title = %(title)s WHERE id = %(user_id)s",
                              user_id=entity.id, title=entity.properties["title"])
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
    Это класс-фабрика. Он возвращает в качестве репозитория один из двух вариантов:
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
            use_db_repo: принимает значение True, если сущности хранятся в MySQL базе, иначе False
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

        options["use_db_repo"] = True if json_object['use_db_repo'] == "True" else False
        options["username"] = json_object['username']
        options["password"] = json_object['password']
        print(options)

        return options

    @classmethod
    def create(cls, fact: AbstractFactory) -> AbstractRepository:
        """
        Выбирает метод получения настроек для создания репозитория. Один реализованный метод - из файла.
        Использует вспомогательный метод __select_from_file() для выбора типа репозитория
        :param fact: фабрика сущностей; передаётся репозиторию
        :return: созданный репозиторий
        """
        if REPOSITORY_CREATION_METHOD == "from-file":
            options = cls.__get_options()
            repository = cls.__select_from_file(options, fact)
        else:
            repository = AbstractRepository()
        return repository

    @classmethod
    def __select_from_file(cls, options: dict, fact: AbstractFactory) -> AbstractRepository:
        """
        Вспомогательный метод для выбора типа репозитория в соответствии с настройками из файла
        :param options: словарь настроек для репозитория
        :param fact: фабрика сущностей; передаётся репозиторию
        :return: инстанс выбранного репозитория
        """
        if options["use_db_repo"]:
            repository = RepositoryMySQL(options, fact)
            print("Working with RepositoryMySQL")
        else:
            repository = RepositoryRAM(options, fact)
            print("Working with RepositoryRAM")
        return repository

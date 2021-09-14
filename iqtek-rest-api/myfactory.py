from __future__ import annotations
from abc import ABC, abstractmethod


# Factory for entities start
class TypeChecker:
    """
    Это дескриптор, проверяющий принадлежность значения переменной инстанса с именем name к типу value_type
    """
    def __init__(self, name, value_type):
        self.name = name
        self.value_type = value_type

    def __set__(self, instance, value):
        if isinstance(value, self.value_type):
            instance.__dict__[self.name] = value
        else:
            raise TypeError(f"'{self.name}' {value} must be {self.value_type}")

    def __get__(self, instance, class_):
        return instance.__dict__[self.name]


class DictChecker:
    """
    Это дескриптор, проверяющий принадлежность значения переменной инстанса с именем name к типу value_type
    """
    def __init__(self, dict_name, key_name):
        self.dict_name = dict_name
        self.key_name = key_name

    def __set__(self, instance, dict_value):
        if isinstance(dict_value, dict):
            if self.key_name in dict_value:
                instance.__dict__[self.dict_name] = dict_value
            else:
                raise TypeError(f"User init error. Key '{self.key_name}' must be in {self.dict_name} dictionary")
        else:
            raise TypeError(f"User init error. Given {self.dict_name} structure must be dictionary")

    def __get__(self, instance, class_):
        return instance.__dict__[self.dict_name]


class Entity(ABC):
    """
    Абстрактная сущность, от которой будут наследоваться конкретные сущности, такие как User
    Сущности будут создавать фабрикой. Храниться они будут в репозитории
    Entity предлагает конструктор по умолчанию, в котором сохраняются id сущности и словарь её параметров
    Метод get_dict() должен возвращать словарь, в котором записаны все параметры сущности, включая и её id.
    Он нужен, чтобы возвращать представление сущности через jsonify().
    """
    id = TypeChecker("id", int)
    properties = TypeChecker("properties", dict)

    def __init__(self, entity_id: int, properties: dict) -> None:
        self.id = entity_id
        self.properties = properties

    @abstractmethod
    def get_dict(self) -> dict:
        raise NotImplementedError


class User(Entity):
    """
    Конкретный класс, реализующий абстракцию Entity. Предназначен для хранения id и ФИО пользователей в репозитории
    """
    properties = DictChecker("properties", "title")

    def __init__(self, user_id: int, properties: dict) -> None:
        super().__init__(user_id, properties)

    def get_dict(self) -> dict:
        """
        Преобразовывает параметры сущности User в вид, подходящий для функции jsonify()
        :return: словарь с параметрами сущности User, включая и id
        """
        result = {"id": self.id}
        result.update(self.properties)
        return result


class AbstractFactory(ABC):
    """
    Интерфейс Абстрактной фабрики для создания сущностей Entity.
    Определяет абстрактные методы:
        create() для создания сущности с переданными параметрами;
        create_empty() для создания пустой сущности (для возврата из репозитория при ошибочных переданных значениях)
        get_factory_name() для возвращения имени фабрики (может потребоваться, чтобы дать имя таблице в базе данных)
    Определяет классовую переменную empty_entity, в которой хранится инстанс пустой сущности
        (чтобы не создавать многократно)
    """
    empty_entity: Entity

    @abstractmethod
    def create(self, entity_id: int, properties: dict) -> Entity:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create_empty(cls) -> Entity:
        raise NotImplementedError

    @abstractmethod
    def get_factory_name(self) -> str:
        raise NotImplementedError


class UserFactory(AbstractFactory):
    """
    Конкретная реализация абстрактный фабрики. Предназначена для работы с сущностями User
    """

    def __init__(self):
        """
        Инициализирует классовую переменную empty_entity.
        Она используется для возвращения несуществующих сущностей из фабрики или из репозитория
        """
        UserFactory.create_empty()

    def create(self, user_id: int, properties: dict) -> Entity:
        """
        Создаёт сущность User в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param properties: строковое значение ФИО пользователя
        :return: объект User с заполненными параметрами
        """
        entity = UserFactory.empty_entity
        try:
            entity = User(user_id, properties)
        except TypeError as e:
            print(e)
        return entity

    @classmethod
    def create_empty(cls) -> Entity:
        """
        Создаёт сущность User с пустым ФИО и id=-1 и сохраняет его в классовую переменную empty_entity.
        Такой id служит признаком несуществующей сущности
        :return: объект User с пустым ФИО и id=-1
        """
        entity = User(-1, {"title": ""})
        cls.empty_entity = entity
        return entity

    def get_factory_name(self) -> str:
        """
        Позволяет узнать имя фабрики. В данном случае это "user"
        :return: строковое значение имени фабрики
        """
        return "user"


if __name__ == "__main__":
    """
    Небольшой тест дескрипторов TypeChecker и DictChecker
    """
    factory = UserFactory()
    user = factory.create(1, {"tit": "des"})
    print(user.id, user.properties)
    user = factory.create(1, ["title", "des"])
    print(user.id, user.properties)
    user = factory.create("1", {"title": "des"})
    print(user.id, user.properties)
    user = factory.create(1, {"title": "des"})
    print("\nOk", user.id, user.properties)

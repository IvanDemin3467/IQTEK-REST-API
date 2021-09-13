from __future__ import annotations
from abc import ABC, abstractmethod


# Factory for entities start
class Entity(ABC):
    def __init__(self, entity_id: int, properties: dict) -> None:
        self.id = entity_id
        self.properties = properties

    @abstractmethod
    def get_dict(self) -> dict:
        pass


class User(Entity):
    """
    Конкретный класс, реализующий абстракцию Entity. Предназначен для хранения id и ФИО пользователей
    """
    def __init__(self, user_id: int, properties: dict) -> None:
        super().__init__(user_id, properties)

    def get_dict(self) -> dict:
        """
        Преобразовывает параметры сущности User в вид, подходящий для функции jsonify()
        :return: словарь с параметрами сущность User
        """
        result = {"id": self.id}
        result.update(self.properties)
        return result


class AbstractFactory(ABC):
    """
    Абстрактная фабрика для создания сущностей Entity
    """
    @abstractmethod
    def create(self, entity_id: int, properties: dict) -> Entity:
        raise NotImplementedError

    @abstractmethod
    def create_empty(self) -> Entity:
        raise NotImplementedError

    @abstractmethod
    def get_factory_name(self) -> str:
        raise NotImplementedError


class UserFactory(AbstractFactory):
    """
    Конкретная реализация абстрактный фабрики. Предназначена для работы с сущностями User
    """
    def create(self, user_id: int, properties: dict) -> Entity:
        """
        Создаёт сущность User в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param properties: строковое значение ФИО пользователя
        :return: объект User с заполненными параметрами
        """
        user = User(user_id, properties)
        return user

    def create_empty(self) -> Entity:
        """
        Создаёт сущность User с пустым ФИО и id=-1. Такой id служит признаком несуществующей сущности
        :return: объект User с пустым ФИО и id=-1
        """
        user = User(-1, {"title": ""})
        return user

    def get_factory_name(self) -> str:
        """
        Позволяет узнать имя фабрики. В данном случае это "user"
        :return: строковое значение имени фабрики
        """
        return "user"

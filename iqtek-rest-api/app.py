from __future__ import annotations

from flask import Flask, jsonify, request

from myrepository import *


"""
Начало работы REST API сервиса
"""
app = Flask(__name__)  # инициализация объекта, с которым сможет работать WSGI сервер
app.config['SECRET_KEY'] = 'gh5ng843bh68hfi4nfc6h3ndh4xc53b56lk89gm4bf2gc6ehm'  # произвольная случайная длинная строка
factory = UserFactory()  # инициализация фабрики сущностей пользователей
repo = RepositoryCreator.create(factory)  # инициализация репозитория


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
    entity = repo.get(user_id)
    if entity == factory.empty_entity:
        return "Rejected. No user with id=" + str(user_id), 404
    return jsonify(entity.get_dict()), 200


@app.route('/user', methods=['GET'])
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
    entity = factory.create(user_id, {'title': title})
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
    entity = factory.create(user_id, {'title': title})
    result = repo.update(entity)
    if result == -1:
        return "Rejected. No user with id=" + str(user_id), 404
    return 'Success. User updated', 204


if __name__ == '__main__':
    """
    Тестовый запуск сервиса. Активируется только при непосредственном запуске приложения.
    При запуске через WSGI-сервер этот блок игнорируется
    """
    """entity = factory.create(1, {'title': "qwe"})
    repo.add(entity)
    print(repo.get(1).get_dict())
    entity = factory.create(3, {'title': "rty"})
    repo.add(entity)
    print(repo.get(3).get_dict())

    entities_list = repo.list()
    result = []
    for entity in entities_list:
        result.append(entity.get_dict())
    print(result)

    entity = factory.create(3, {'title': "123"})
    repo.update(entity)
    entities_list = repo.list()
    result = []
    for entity in entities_list:
        result.append(entity.get_dict())
    print(result)"""

    app.run(host="127.0.0.1", port=80)

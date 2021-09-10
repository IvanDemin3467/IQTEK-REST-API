from requests import get, post, patch, delete

URL = "http://localhost:80/"


def show_all():
    """
    Simply gets all entries from service and prints status code (200 expected) and returned json
    :return: None
    """
    print("\nПолучить все записи")
    result = get(URL + 'users')
    print(result.status_code, result.text)


def sample_test(message, resource, fun):
    """
    Creates REST API request to service located at URL address
    :param message: a string to print before performing request (for user readability)
    :param resource: a string indicating a resource located in the service that is being requested
    :param fun: a function with which request is performed (get(), post(), patch() or delete() expected)
    :return: None
    """
    print("\n" + message)
    result = fun(URL + resource)
    print(result.status_code, result.text)


if __name__ == '__main__':

    post(URL + "user/1?Pyotr%20Pervy")
    post(URL + "user/2?Aleksandr%20Sergeevich%20Pushkin")
    show_all()

    # Successful

    sample_test("Получить одну запись с id=2", 'user/2', get)

    sample_test("Создать пользователя с именем '; DROP TABLE IF EXISTS users; --",
                "user/3?title=%27%3B+DROP+TABLE+IF+EXISTS+users%3B+--", post)  # SQL injection
    show_all()

    sample_test("Изменить запись с id=3", "user/3?title=Mikhail%20Vasilievich%20Lomonosov", patch)
    show_all()

    sample_test("Удалить запись с id=3", "user/3", delete)
    show_all()

    # Rejected

    sample_test("Получить несуществующую запись запись с id=3", "user/3", get)

    sample_test("Создать пользователя с id, который уже существует в базе", "user/2?title=Test", post)

    sample_test("Изменить пользователя, которого не существует в базе", "user/3?title=Test%20Title", patch)

    sample_test("Удалить пользователя, которого не существует в базе", "user/3", delete)

    delete(URL + 'user/2')  # delete all
    delete(URL + 'user/1')
    sample_test("Отобразить пустую базу", "users", get)

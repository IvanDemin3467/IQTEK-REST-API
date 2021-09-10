from requests import post, get, patch, delete

def show_all():
    print("\nПолучить все записи")
    result = get('http://localhost:80/users')
    print(result.json())

if __name__ == '__main__':

    # Successfull

    show_all()

    print("\nПолучить одну запись с id=2")
    result = get('http://localhost:80/user/2')
    print(result.json())

    print("\nСоздать пользователя с именем '; DROP TABLE IF EXISTS users; --")
    result = post('http://localhost:80/user/3?title=%27%3B+DROP+TABLE+IF+EXISTS+users%3B+--')  # SQL injection
    print(result.status_code)

    show_all()

    print("\nИзменить запись с id=3")
    result = patch('http://localhost:80/user/3?title=Mikhail%20Vasilevich%20Lomonosov')
    print(result.status_code)

    show_all()

    print("\nУдалить запись с id=3")
    result = delete('http://localhost:80/user/3')
    print(result.status_code)

    show_all()

    # Rejected

    print("\nПолучить несуществующую запись запись с id=3")
    result = get('http://localhost:80/user/3')
    print(result.text)

    print("\nСоздать пользователя с id, который уже существует в базе")
    result = post('http://localhost:80/user/2?title=Test')
    print(result.text)

    print("\nИзменить пользователя, которого не существует в базе")
    result = patch('http://localhost:80/user/3?title=Test%20Title')
    print(result.text)

    print("\nУдалить пользователя, которого не существует в базе")
    result = delete('http://localhost:80/user/3')
    print(result.text)

    print("\nОтобразить пустую базу")
    delete('http://localhost:80/user/2')  # delete all
    delete('http://localhost:80/user/1')
    result = get('http://localhost:80/users')
    print(result.text)

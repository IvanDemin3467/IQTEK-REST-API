# Задание
На любом фреймворке python (FastAPI, Flask и т.д.) реализовать REST API сервис, реализующий операции над сущностью User с полями - id, ФИО.

Сервис предполагает:
1. создание User,
2. изменение User, 
3. получение User по id,
4. удаление User.


Технические требования:

Необходимы несколько реализаций репозитория - в памяти и БД (mysql, postgress или иные). Реализация репозитория выбирается при инициализации приложения из конфиг файла, с указанием типа репозитория и его настройками (доступы).

Обязательно использование ООП и шаблонов проектирования "Фабрика", "Репозиторий"

## Результат

**Пример запроса на получение записи пользователя из базы**
```
curl http://localhost:80/user/2
```

**Пример запроса на получение всех записей пользователей из базы**
```
curl http://localhost:80/user
```

**Пример запроса на добавление записи пользователя в базу**
```
curl -X POST http://localhost:80/user/3?title=Mikhail%20Vasilevich%20Lomonosov
```

**Пример запроса на удаление записи пользователя из базы**
```
curl -X DELETE http://localhost:80/user/3
```

**Пример запроса на изменение записи пользователя в базе**
```
curl -X PATCH http://localhost:80/user/3?title=Aleksandr%20Sergeevich%20Pushkin
```

**Настройки**

Настройки приложения хранятся в файле options.json. Используются следующие параметры:
```
repo_type: содержит имя класса, который будет создаваться этой фабрикой репозиториев. Возможные значения:
    RepositoryMySQL - хранит сущности в базе MySQL
    RepositoryRAM - хранит сущности в оперативной памяти
username: логин для доступа к базе
password: пароль для доступа к базе
```
**Требования приложения**

Протестировано на mysql 8.0.26. На сервере My SQL требуется создание пользователя с именем и паролем, совпадающими с таковыми в файле options.txt 

*Используемые библиотеки*

flask==2.0.1

mysql-connector-python==8.0.26

**Модули**

/iqtek-rest-api/app.py - REST-API сервис, реализованный на Flask

/iqtek-rest-api/myfactory.py - Реализация шаблона фабрики

/iqtek-rest-api/myrepository.py - Реализация шаблона репозитория

/iqtek-rest-api/test/tests.py - Примеры тестов для проверки работоспособности сервиса

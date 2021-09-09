# Задание
На любом python фреймворке (FastAPI, Flask и т.д.) или без реализуйте REST API сервис, реализующий операции над сущностью User с полями - id, ФИО.

Сервис предполагает:


создание User, 


изменение User, 


получение по id,


удаление User.


Технические требования:

Необходимы несколько реализаций репозитория - в памяти и БД (mysql, postgress или иные). Реализация репозитория выбирается при инициализации приложения из конфиг файла, с указанием типа репозитория и его настройками (доступы).


Использование ООП

Особое внимание стоит обратить на следующие моменты:

Код должен быть написан понятно и аккуратно, с соблюдением табуляции и прочих элементов написания, без лишних элементов и функций, не имеющих отношения к функционалу тестового задания, снабжен понятными комментариями.

Читабельность и наличие элементарной архитектуры.
Чистота и оформление кода — не менее важный фактор. Код должен быть написан в едином стиле (желательно в рекомендуемом для конкретного языка). Также к чистоте относятся отсутствие копипаста и дублирования логики.

Тестовое задание должно быть представлено в следующем виде:

Ссылка на публичный репозиторий GitHub с исходным кодом.

Отправку результата оформить как pull request для пользователя iqtek

## Результат

**Пример запроса на получение записи пользователя из базы**
```
curl http://localhost:80/user/2
```

**Пример запроса на получение всех записей пользователей из базы**
```
curl http://localhost:80/users
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


**Требования приложения**

Протестировано на mysql 8.0.26

*Используемые библиотеки*

flask==2.0.1

mysql-connector-python==8.0.26

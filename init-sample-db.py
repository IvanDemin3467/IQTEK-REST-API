from mysql.connector import connect, Error
import app


# Create db with name app.DB_NAME using credentials from app
try:
    with connect(
            host="localhost",
            user=app.repo.options["username"],
            password=app.repo.options["password"]
            ) as connection:
        create_db_query = f"CREATE DATABASE {app.DB_NAME};"
        with connection.cursor() as cursor:
            cursor.execute(create_db_query)
            cursor.fetchall()
            cursor.close()
except Error as e:
    print(e)

# Create table "users". If exists -> drop and recreate
try:
    with connect(
            host="localhost",
            user=app.repo.options["username"],
            password=app.repo.options["password"],
            database=app.DB_NAME,
            ) as connection:
        query = """
            CREATE DATABASE sample_database;
            DROP TABLE IF EXISTS users;
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description VARCHAR(255) NOT NULL);
            DESCRIBE users;
            INSERT INTO users (title, description)
                VALUES ('Пётр Первый', 'Последний царь всея Руси');
            INSERT INTO users (title, description)
                VALUES ('Александр Сергеевич Пушкин', 'Великий русский поэт');
            SELECT * FROM users;
        """
        create_table_query = """
            DROP TABLE IF EXISTS users;
            """
        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            cursor.fetchall()
            cursor.close()

        create_table_query = """
                CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description VARCHAR(255) NOT NULL
                );
                """
        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            cursor.fetchall()
            cursor.close()

        connection.commit()
        connection.close()
except Error as e:
    print(e)

# prepopulate table
try:
    with connect(
            host="localhost",
            user=app.repo.options["username"],
            password=app.repo.options["password"],
            database=app.DB_NAME,
            ) as connection:
        prepopulate_table_query = """
                INSERT INTO users (id, title, description)
                VALUES (1, 'Пётр Первый', 'Последний царь всея Руси'),
                (2, 'Александр Сергеевич Пушкин', 'Великий русский поэт');
                """
        with connection.cursor() as cursor:
            cursor.execute(create_table_query)
            cursor.fetchall()
            cursor.close()
        connection.commit()
        connection.close()
except Error as e:
    print(e)

# check your creation
try:
    with connect(
            host="localhost",
            user=app.repo.options["username"],
            password=app.repo.options["password"],
            database=app.DB_NAME,
            ) as connection:
        query = "SELECT * FROM users;"
        with connection.cursor() as cursor:
            cursor.execute(query)
            print(cursor.fetchall())
            cursor.close()
        connection.commit()
        connection.close()
except Error as e:
    print(e)



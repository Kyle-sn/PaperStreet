import mysql.connector
import os


def get_previous_value(table, symbol, date):
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_table = table

    connection = mysql.connector.connect(
        host="localhost",
        user=db_user,
        password=db_password,
        database="my_database"
    )

    # query the most recent value before the given date
    query = f"""
    SELECT value 
    FROM {db_table}
    WHERE symbol = %s AND date < %s
    ORDER BY date DESC
    LIMIT 1;
    """

    cursor = connection.cursor()
    cursor.execute(query, (symbol, date))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else None
import mysql.connector

def connect_2_mysql(password):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password= password,
        database="itudb2320"
    )
    
    return db
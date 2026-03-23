import sqlite3

# Connect to database
db = sqlite3.connect('cyberguard.db')
cursor = db.cursor()

# Show all tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('=== DATABASE TABLES ===')
for table in tables:
    print(f'Table: {table[0]}')

# Show table structure
print('\n=== TABLE STRUCTURES ===')
for table in tables:
    table_name = table[0]
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    print(f'\n{table_name.upper()} TABLE:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')

db.close()
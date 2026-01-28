import sqlite3

conn = sqlite3.connect(r'C:\Users\WneQ\Desktop\wig\wig_data.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM companies')
count = c.fetchone()[0]
print(f'Companies with sectors: {count}')

c.execute('SELECT ticker, sector FROM companies LIMIT 15')
print('\nSample sectors:')
for row in c.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()

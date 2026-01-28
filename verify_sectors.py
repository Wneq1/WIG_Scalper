import sqlite3

# Check if sectors are properly saved
conn = sqlite3.connect(r'C:\Users\WneQ\Desktop\wig\wig_data.db')
c = conn.cursor()

# Count sectors by type
c.execute('''
    SELECT sector, COUNT(*) as count 
    FROM companies 
    GROUP BY sector 
    ORDER BY count DESC
''')

print("Sector distribution:")
print("-" * 40)
for row in c.fetchall():
    print(f"{row[0]:25} {row[1]:3} companies")

print("\n" + "=" * 40)
c.execute('SELECT COUNT(*) FROM companies')
total = c.fetchone()[0]
print(f"Total companies: {total}")

conn.close()

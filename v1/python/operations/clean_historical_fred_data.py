import pandas as pd

symbol = 'NASDAQCOM'

df = pd.read_csv(f'/home/kyle/{symbol}.csv')

# add a 'symbol' column populated with the relevant symbol
df.insert(1, 'symbol', symbol)

# populate 'id' by concatenating 'symbol' and 'date' in the 'symbol.date' for the DB primary key
df.insert(0, 'id', df['symbol'] + '.' + df['date'])

# replace any '.' in 'value' column with the previous day's value
df['value'] = df['value'].replace('.', pd.NA)
df['value'] = df['value'].fillna(method='ffill')

df.to_csv(f'/home/kyle/{symbol}_new.csv', index=False)

# next steps are to change to root and mv the new files to /var/lib/mysql-files/
# then run:  
# LOAD DATA INFILE '/var/lib/mysql-files/NASDAQCOM_new.csv' 
# INTO TABLE my_database.fred_data 
# FIELDS TERMINATED BY ',' 
# LINES TERMINATED BY '\n' 
# IGNORE 1 ROWS (id, date, symbol, value);


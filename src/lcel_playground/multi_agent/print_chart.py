import pandas as pd
import matplotlib.pyplot as plt

data = {
    'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    'Price': [0.93, 7.98, 756.73, 133.76, 129.63, 737.8, 3748.57, 1216.06, 2487.52, 2900]
}

df = pd.DataFrame(data)

plt.figure(figsize=(10, 5))
plt.plot(df['Year'], df['Price'], marker='o')
plt.title('Ethereum (ETH) Price History (2015-2024)')
plt.xlabel('Year')
plt.ylabel('Price (USD)')
plt.grid(True)
plt.savefig('./eth_price_history.png')
plt.show()
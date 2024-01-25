# INSTALL FOLLOWING LIBRARIES
# conda install conda-forge::yfinance
# conda install -c conda-forge charset-normalizer
# conda install anaconda::pandas
# conda install anaconda::openpyxl

# Import pandas and yfinance libraries
import pandas as pd
import yfinance as yf
import requests 
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import math


# Load excel file into pandas dataframe
df = pd.read_excel("/Users/soerenundkatjadoepke/Documents/Coding/Python_Projects/240121_PortfolioAnalyser/portfoliolist.xlsx")

# Define a function to get the current price of a symbol
def get_price(symbol, is_fx, alternativesource):
    # Try to get the price from yfinance
    try:
        # Get the ticker object
        ticker = yf.Ticker(symbol)
        # Get the historical data for the last day
        data = ticker.history(period="1d")
        # Check if the data frame is empty
        if data.empty:
            if not is_fx:
                # Try to get the price from the Targobank website
                url = alternativesource
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                try:
                    price_temp = soup.find('td', class_='price red').text.strip()
                    words = price_temp.split()
                    price = float(words[0].replace(",","."))
                    price_type = "Last Traded"
                    print(f"Price for {symbol} from Targobank website: {price}")
                except:
                    try:
                        price_temp = soup.find('td', class_='price green').text.strip()
                        words = price_temp.split()
                        price = float(words[0].replace(",","."))
                        price_type = "Last Traded"
                        print(f"Price for {symbol} from Targobank website: {price}")
                    except:
                        try:
                            price_temp = soup.find('td', class_='price').text.strip()
                            words = price_temp.split()
                            price = float(words[0].replace(",","."))
                            price_type = "Last Traded"
                            print(f"Price for {symbol} from Targobank website: {price}")
                        except:
                            price = None
                            price_type = "Fallback"
                            print(f"Price for {symbol}: fallback price will be used")
            else:
                price = None
                price_type = "Fallback"
                print(f"Price for {symbol}: fallback price will be used")
            # Print a message
            #print(f"No data available for {symbol}")
            #price_type = "Fallback"
            #price = None
        else:
            # Get the last closing price
            price = data["Close"].iloc[0]
            # Round the last closing price to two decimal places
            # last_close = round(last_close, 5)
            # Try to get the bid price from the ticker info
            try:
                if not is_fx:
                    bid_price = ticker.info["bid"]
                    # Round the bid price to two decimal places
                    # bid_price = round(bid_price, 5)
                    # Use the bid price as the current price
                    price = bid_price
                    price_type = "Bid"
                else:
                    ask_price = ticker.info["ask"]
                    # Round the ask price to two decimal places
                    # ask_price = round(bid_price, 5)
                    # Use the ask price as the current price
                    price = ask_price
                    price_type = "Ask"
            # If the bid or ask price is not available, use the last close price
            except KeyError:
                price_type = "Last Close"
    except:
        price = None
        price_type = "Fallback"
    return price, price_type

# Define a function to get the long name and short name of a symbol
def get_name(symbol):
    # Try to get the name from yfinance
    try:
        # Get the ticker object
        ticker = yf.Ticker(symbol)
        print(ticker.info)
        # Get the long name and short name
        longname = ticker.info['longName']
        shortname = ticker.info['shortName']
    except:
        longname = ""
        shortname = ""
    return longname, shortname

# Define a function to calculate the volatility of a symbol
def get_volatility(symbol, volatility_fallback):
    # Try to get the data from yfinance
    try:
        # Get the ticker object
        ticker = yf.Ticker(symbol)
        # define the end date as the last trading day before today
        end_date = datetime.today() - timedelta(days=1)
        # define the start date as 30 days before the end date
        start_date = end_date - timedelta(days=60)
        # download the stock data
        df = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        # calculate the daily returns
        df['returns'] = df['Adj Close'].pct_change()
        # calculate the 30-day rolling standard deviation of returns
        df['volatility'] = df['returns'].rolling(window=30).std()
        # calculate the annualized volatility
        annualized_volatility = df['volatility'].iloc[-1] * (252 ** 0.5)
        annualized_volatility_type = "Historical (30d)"
    except:
        annualized_volatility = volatility_fallback
        annualized_volatility_type = "Proxy (MSCI WORLD)"
    return annualized_volatility, annualized_volatility_type


# Cast columns for "Typ_Kurswert" and for "Typ_Wechselkurs" to String
df["Typ_Kurswert"] = df["Typ_Kurswert"].astype(str)
df["Typ_Wechselkurs"] = df["Typ_Wechselkurs"].astype(str)
df["Typ_Volatilitaet"] = df["Typ_Volatilitaet"].astype(str)

# Get fallback volatility (= volatility of the MSCI World index)
volatility_fallback, _ = get_volatility("^990100-USD-STRD", 0.0)
    
# Iterate through all rows of the dataframe
for i, row in df.iterrows():
    # Get the value from column "YahooFinanceSymbol"
    symbol = row["YahooFinanceSymbol"]
    # Get the value from column "SourceTargobank"
    alternativesource = row["SourceTargobank"]
    # Get the current price with the yfinance library
    price, price_type = get_price(symbol, False, alternativesource)
    # If the price is None, use the value from column "Kurs_Fallback"
    if price is None:
        price = row["Kurs_Fallback"]
    # Divide the current price by 100 if the value of the row in column "ProzentNotierung" is true
    if row["ProzentNotierung"]:
        price = price / 100
    # Put the current price in column "Kurswert"
    df.loc[i, "Kurswert"] = price
    # Put the type of the current price in column "Typ_Kurswert"
    df.loc[i, "Typ_Kurswert"] = price_type
    # Get the value from column "YahooFinanceFX"
    fx = row["YahooFinanceFX"]
    # Get the exchange rate with the yfinance library
    rate, rate_type = get_price(fx, True, "")
    # Put the exchange rate in column "Wechselkurs"
    df.loc[i, "Wechselkurs"] = rate
    # Put the type of the exchange rate in column "Typ_Wechselkurs"
    df.loc[i, "Typ_Wechselkurs"] = rate_type
    # Calculate the value for column "Wert" as the product of column "Stueck" and column "Kurswert" divided by column "Wechselkurs"
    df.loc[i, "Wert"] = row["Stueck"] * price / rate
    # Calculate the value for column "Wertentwicklung" as the difference between column "Wert" and column "Kaufwert_EUR"
    df.loc[i, "Wertentwicklung"] = df.loc[i, "Wert"] - df.loc[i, "Kaufwert_EUR"]
    # Get the volatility
    volatility, volatility_type = get_volatility(symbol, volatility_fallback)
    df.loc[i, "Volatilitaet"] = volatility
    df.loc[i, "Typ_Volatilitaet"] = volatility_type

# Export the dataframe to an excel file
df.to_excel("/Users/soerenundkatjadoepke/Documents/Coding/Python_Projects/240121_PortfolioAnalyser/portfoliolist_updated.xlsx")

# Create a new aggregated dataframe 
df_agg = df[['YahooFinanceSymbol', 'Wertpapier', 'Stueck', 'Kurswert', 'Wechselkurs', 'Wert', 'Wertentwicklung', 'Volatilitaet']].copy()
df_agg.rename(columns={'YahooFinanceSymbol': 'Symbol'}, inplace=True)
# Group by Symbol and aggregate the values
df_agg = df_agg.groupby(['Symbol']).agg({'Wertpapier': 'first', 'Kurswert': 'first', 'Wechselkurs': 'first', 'Stueck': 'sum', 'Wert': 'sum', 'Wertentwicklung': 'sum', 'Volatilitaet': 'first'}).reset_index()
df_agg['VaR1d'] = 1.645 * df_agg['Wert'] * df_agg['Volatilitaet'] * math.sqrt(1/252)

# blank lines
print("")
print("")
print("")
print("")
print("")
print("")
print("#################################################################################")
print("")
print("")

# Calculate the sum over all rows from column "Wert" and print it to the terminal
total_wert = df["Wert"].sum()
print(f"Wert (total):            {total_wert:,.2f}")
# sum up the values in column "Wert" with fallback prices
sum_wert_fallback = df.loc[df['Typ_Kurswert'] == 'Fallback', 'Wert'].sum()
print(f'                         (davon basierend auf Fallback-Preisen: {sum_wert_fallback:,.2f})')

# Calculate the sum over all rows of the column "Wertentwicklung" and print it to the terminal
total_wertentwicklung = df["Wertentwicklung"].sum()
print(f"Wertentwicklung (total): {total_wertentwicklung:,.2f}")
# sum up the values in column "Wertentwicklung" with fallback prices
sum_wertentwicklung_fallback = df.loc[df['Typ_Kurswert'] == 'Fallback', 'Wertentwicklung'].sum()
print(f'                         (davon basierend auf Fallback-Preisen: {sum_wertentwicklung_fallback:,.2f})')

# blank line
print("")

# Determine the top 5 positions based on Wert
df_Wert_Top = df_agg.nlargest(5, 'Wert')
df_Wert_Top['Anteil'] = df_Wert_Top['Wert']/total_wert
df_Wert_Top['kumulierter Anteil'] = df_Wert_Top['Anteil'].cumsum()
df_formatted_output = df_Wert_Top.copy()
df_formatted_output[['Wert']] = df_formatted_output[['Wert']].map(lambda x: '{:,.2f}'.format(x))
df_formatted_output[['Anteil', 'kumulierter Anteil']] = df_formatted_output[['Anteil', 'kumulierter Anteil']].map(lambda x: '{:,.1%}'.format(x))
print('Top 5 Positionen:')
print(df_formatted_output.loc[:, ['Symbol','Wertpapier','Wert', 'Anteil', 'kumulierter Anteil']])

# blank line
print("")

# Determine the top 5 positions based on positive Wertentwicklung
df_Wertentwicklung_Top = df_agg.nlargest(5, 'Wertentwicklung')
total_wertentwicklung_positive = df_agg[df_agg['Wertentwicklung'] >= 0]['Wertentwicklung'].sum()
df_Wertentwicklung_Top['Anteil'] = df_Wertentwicklung_Top['Wertentwicklung']/total_wertentwicklung_positive
df_Wertentwicklung_Top['kumulierter Anteil'] = df_Wertentwicklung_Top['Anteil'].cumsum()
df_formatted_output = df_Wertentwicklung_Top.copy()
df_formatted_output[['Wertentwicklung']] = df_formatted_output[['Wertentwicklung']].map(lambda x: '{:,.2f}'.format(x))
df_formatted_output[['Anteil', 'kumulierter Anteil']] = df_formatted_output[['Anteil', 'kumulierter Anteil']].map(lambda x: '{:,.1%}'.format(x))
print('Top 5 Gewinner:')
print(df_formatted_output.loc[:, ['Symbol','Wertpapier','Wertentwicklung', 'Anteil', 'kumulierter Anteil']])
print("")
print(f"Summe aller positiven Wertentwicklungen: {total_wertentwicklung_positive:,.2f}")

# blank line
print("")

# Determine the top 5 positions based on negative Wertentwicklung
df_Wertentwicklung_Bottom = df_agg.nsmallest(5, 'Wertentwicklung')
total_wertentwicklung_negative = df_agg[df_agg['Wertentwicklung'] < 0]['Wertentwicklung'].sum()
df_Wertentwicklung_Bottom['Anteil'] = df_Wertentwicklung_Bottom['Wertentwicklung']/total_wertentwicklung_negative
df_Wertentwicklung_Bottom['kumulierter Anteil'] = df_Wertentwicklung_Bottom['Anteil'].cumsum()
df_formatted_output = df_Wertentwicklung_Bottom.copy()
df_formatted_output[['Wertentwicklung']] = df_formatted_output[['Wertentwicklung']].map(lambda x: '{:,.2f}'.format(x))
df_formatted_output[['Anteil', 'kumulierter Anteil']] = df_formatted_output[['Anteil', 'kumulierter Anteil']].map(lambda x: '{:,.1%}'.format(x))
print('Top 5 Verlierer:')
print(df_formatted_output.loc[:, ['Symbol','Wertpapier','Wertentwicklung', 'Anteil', 'kumulierter Anteil']])
print("")
print(f"Summe aller negativen Wertentwicklungen: {total_wertentwicklung_negative:,.2f}")

# blank line
print("")

# Determine the top 10 positions based on VaR
df_VaR_Top = df_agg.nlargest(10, 'VaR1d')
df_formatted_output = df_VaR_Top.copy()
df_formatted_output[['VaR1d']] = df_formatted_output[['VaR1d']].map(lambda x: '{:,.0f}'.format(x))
df_formatted_output[['Volatilitaet']] = df_formatted_output[['Volatilitaet']].map(lambda x: '{:,.1%}'.format(x))
print('Top 10 Value-at-Risk Positionen:')
print(df_formatted_output.loc[:, ['Symbol','Wertpapier','VaR1d', 'Volatilitaet']])
print("")
print(f"Volatilität des MSCI World Index : {volatility_fallback:,.1%}")
print("(als Fallback für Positionen, bei denen keine Volatilität berechnet werden konnte)")

# blank lines
print("")
print("")

# Print the whole dataframe with all columns to the terminal
#print(df)
#print('Portfolio Detail:')
#print(df.loc[:, ['YahooFinanceSymbol','Wertpapier','Stueck', 'Kurswert', 'Typ_Kurswert', 'Wechselkurs', 'Volatilitaet', 'Typ_Volatilitaet', 'Wert', 'Wertentwicklung']])
df_formatted_output = df_agg.copy()
df_formatted_output[['Stueck', 'Wechselkurs']] = df_formatted_output[['Stueck', 'Wechselkurs']].map(lambda x: '{:,.4f}'.format(x))
df_formatted_output[['Kurswert', 'Wert', 'Wertentwicklung']] = df_formatted_output[['Kurswert', 'Wert', 'Wertentwicklung']].map(lambda x: '{:,.2f}'.format(x))
df_formatted_output[['Volatilitaet']] = df_formatted_output[['Volatilitaet']].map(lambda x: '{:,.1%}'.format(x))
print('Portfolio Detail:')
print(df_formatted_output.loc[:, ['Symbol','Wertpapier','Stueck', 'Kurswert', 'Wechselkurs', 'Wert', 'Wertentwicklung', 'Volatilitaet']])

# blank lines
print("")
print("")

      
### FOR FORMATTING OUTPUT
'''
import pandas as pd

# create a sample dataframe
df = pd.DataFrame({'Wert': [1000, 2000, 3000, 4000, 5000],
                   'Wertentwicklung': [1.2345, 2.3456, 3.4567, 4.5678, 5.6789],
                   'Name': ['John', 'Jane', 'Bob', 'Alice', 'Mike']})

# format the numbers with thousands separator and maximum two decimal places
formatted_df = df.copy()
formatted_df[['Wert', 'Wertentwicklung']] = formatted_df[['Wert', 'Wertentwicklung']].applymap(lambda x: '{:,.2f}'.format(x))
--> bei Prozentwerten: df['column_name'] = df['column_name'].applymap('{:.2%}'.format)

# display the formatted dataframe
print(formatted_df)
'''

### FOR TOP 5 POSITIVE AND NEGATIVE VALUES
'''
# get the top 5 highest positive values
top_5_positive = df.nlargest(5, 'Wertentwicklung')
# get the top 5 most negative values
top_5_negative = df.nsmallest(5, 'Wertentwicklung')
print(f'Top 5 highest positive values:\n{top_5_positive}\n')
print(f'Top 5 most negative values:\n{top_5_negative}')
'''

### CALCULATE VOLATILITY
'''
import yfinance as yf
from datetime import datetime, timedelta

# define the end date as the last trading day before today
end_date = datetime.today() - timedelta(days=1)
# define the start date as 30 days before the end date
start_date = end_date - timedelta(days=30)

# download the stock data
df = yf.download('AAPL', start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

# calculate the daily returns
df['returns'] = df['Adj Close'].pct_change()

# calculate the 30-day rolling standard deviation of returns
df['volatility'] = df['returns'].rolling(window=30).std()

# calculate the annualized volatility
annualized_volatility = df['volatility'].iloc[-1] * (252 ** 0.5)

print(f'The 30-day rolling annualized volatility of the stock is {annualized_volatility:.2%}.')
'''

''' alternative for vola for unassinged
import yfinance as yf
msci_world = yf.Ticker("^MSAWORLD")
print(f"The ticker for MSCI World is {msci_world.info['symbol']}.")
'''

''' and for bonds
Yes, there is a bond index that tracks the performance of US Treasury bonds with maturities between 3 and 5 years. It is called the S&P U.S. Treasury Bond 3-5 Year Index 1. The ticker symbol for this index is not publicly available, but you can use the iShares 3-7 Year Treasury Bond ETF (IEI) as a proxy to track the performance of US Treasury bonds with maturities between 3 and 5 years 23.

You can use the yfinance library to get the ticker symbol for IEI. Here is a sample code snippet that demonstrates how to do this:

Python

import yfinance as yf

iei = yf.Ticker("IEI")

print(f"The ticker symbol for IEI is {iei.info['symbol']}.")
'''
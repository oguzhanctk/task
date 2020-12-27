import pyodbc
import requests
import pandas as pd
import time
import functools

from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from pypfopt.cla import CLA
from pypfopt import objective_functions
import pypfopt.discrete_allocation as disc_alloc
from pypfopt.plotting import plot_efficient_frontier as ef_plot

def timer(func):
    """print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        t1 = time.perf_counter()
        ret = func(*args, **kwargs)
        t2 = time.perf_counter()
        print(f"elapsed time for {func.__name__!r}: {t2 - t1:.4f}s")
        return ret
    return wrapper_timer


@timer
def getSymbolsFromDatabase():
     server = "185.122.200.217\SQLEXPRESS"
     database = "MainDb"
     username = "sa"
     password = "Fidelio06"     
     conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER="+server+";DATABASE="+database+";UID="+username+";PWD="+ password
     sql_str = "SELECT SymbolName FROM Symbols"
     try:
          conn = pyodbc.connect(conn_str)
     except:
          print("something went wrong")
     cursor = conn.cursor()
     cursor.execute(sql_str)
     symbols = [row.SymbolName for row in cursor.fetchall()]     
     conn.close()
     return symbols

@timer
def httpRequestForSymbol(symbol, count):
     url = f"http://185.122.200.217:6778/Data/GetCandleData?symbol={symbol}&period=60&count={count}"
     r = requests.get(url)
     to_str = r.content.decode()
     to_raw_df = pd.read_json(to_str)
     if "open" in to_raw_df:
          to_df = to_raw_df.loc[:, ["open"]].rename(columns={"open" : symbol})
          return to_df
     else:
          empty_df = pd.DataFrame({symbol : [-1 for _i in range(count)]})
          return empty_df
@timer
def createDataFrame(symbols, count):
     first_symbol = symbols[0];
     df = httpRequestForSymbol(first_symbol, count)
     for _i in range(1, len(symbols)):
          temp = httpRequestForSymbol(symbols[_i], count)
          df = df.merge(temp, how="inner", left_index=True, right_index=True)
     return df

@timer
def calculateInvestment(limit=10, count=10, write_to_file=True, show_cla=False, tpv=20000):
     symbols = getSymbolsFromDatabase()
     prices = createDataFrame(symbols[:limit], count)
     mu = expected_returns.mean_historical_return(prices)
     S = risk_models.CovarianceShrinkage(prices).ledoit_wolf()
     ef = EfficientFrontier(mu, S, weight_bounds=(-1, 1))
     ef.add_objective(objective_functions.L2_reg)     
     ef.min_volatility()
     c_weights = ef.clean_weights()
     if write_to_file == True:
          ef.save_weights_to_file("weights.txt")
     if show_cla == True:
          cla = CLA(mu, S)
          ef_plot(cla)
     ef.portfolio_performance(verbose=True)
     latest_prices = disc_alloc.get_latest_prices(prices)
     allocation_minv, leftover = disc_alloc.DiscreteAllocation(c_weights, latest_prices, total_portfolio_value=tpv).lp_portfolio()
     return allocation_minv, leftover


          
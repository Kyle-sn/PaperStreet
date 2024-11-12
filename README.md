# PaperStreet Automated Trading System
## Overview
An automated trading system written primarily in java utilizing the Interactive Brokers TWS API. I started building it in January 2022 as a way to practice my java as well as to create my own personal trading system that I can use for personal strategies.

My goal was to successfully place a trade in my personal trading account using the automated trading system. I was able to do so in production on 2022-03-28.

I lack the know how to perform worthwhile quantitative research and so there is no strategy logic at the moment. My professional experience is in trading operations and supporting automated trading systems, which is why I am primarily focusing on infrastructure for this project.

## PaperStreet OMS Workflow (Java)
There are three main classes that need to run in this order:
##### MarketDataHandler
Connects to IBKR requesting market data for a particular contract.
##### PositionHandler
Connects to IBKR and does the following:
1. Listens for account updates for a specific account number.
2. Requests account summary information, such as margin info, buying power, cash balances, etc.
3. Requests position information. Requested initially at startup and then again only when positions change.
##### StrategyHandler
Connects to IBKR and attempts to place trades. This part of the OMS is currently being worked on.

As of November 2024, some trade parameters are hardcoded in `StrategyHandler::placeTrade`. The strategy parameters go through some pre-trade checks and then a market order is sent.

On the OMS side of things, I am currently working on introducing logic that will allow the tracking of more than one strategy and any trades and positions that are associated with each strategy. This will allow for intraday tracking of strategy trading as well as overnight tracking of positions for each strategy. 

My first iteration is going to assign the relevant positions to each strategies each morning. The next iteration will do a simple pro rata allocation to all production strategies. From here, it will be up to the strategies to manage the positions they receive each day. I dont think the pro-rata allocation will be optimal for low frequency trading, but the functionality would be nice to have.

## PaperStreet Research Environment (Python, SQL, Shell, Linux)
I have no experience as a researcher and so there is no active work being done on signal generation and strategy logic. Right now there are two sections to my research environment:
##### Backtesting
I have a simple template, which is utilizing [vectorbt](https://vectorbt.pro/documentation/fundamentals/). Although I do not have a background in math/stats, I do at some point plan to improve upon this backtesting environment in an attempt to improve my python and get some experience with various data analytics libraries like NumPy, Pandas, SciPy, and Scikit-learn.
##### Operations
This section is currently a work in progress. Right now I am working on data gathering via the [FRED](https://fred.stlouisfed.org/) API. I dont have much use for this data, but I am downloading it and storing it an an attempt to work on my python and SQL skills.

I am currently running daily cron jobs, which are executing python api requests via shell scripts. These python scripts are also uploading the relevant data to a MySQL database I have running on a Raspberry Pi 4 running Ubuntu. 

In addition to building more scripts to download and process data, I also plan to create some clean-up and other utility scripts to keep my Raspberry Pi in a clean, runnable state.
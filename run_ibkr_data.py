from research.session import Session


def main():
    with Session() as session:
        df = session.market_data.get_daily_bars("SPY")

    print("\n=== DATA ===")
    print(df.head())
    print(df.tail())


if __name__ == "__main__":
    main()

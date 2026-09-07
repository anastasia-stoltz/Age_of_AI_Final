import requests
import pandas as pd


def get_chart(date):
    url = (
        "https://raw.githubusercontent.com/"
        "mhollingshead/billboard-hot-100/main/date/"
        f"{date}.json"
    )

    response = requests.get(url)
    response.raise_for_status()

    chart = response.json()

    df = pd.DataFrame(chart["data"])
    df["chart_date"] = chart["date"]

    return df


# Four chart snapshots from each comparison year
dates = {
    1985: [
        "1985-04-06",
        "1985-07-06",
        "1985-10-05"
    ],
    1990: [
        "1990-04-07",
        "1990-07-07",
        "1990-10-06"
    ],
    1995: [
        "1995-04-08",
        "1995-07-08",
        "1995-10-07"
    ],
    2000: [
        "2000-04-08",
        "2000-07-08",
        "2000-10-07"
    ],
    2005: [
        "2005-04-09",
        "2005-07-09",
        "2005-10-08"
    ],
    2010: [
        "2010-04-10",
        "2010-07-10",
        "2010-10-09"
    ],
    2015: [
        "2015-04-11",
        "2015-07-11",
        "2015-10-10"
    ],
    2020: [
        "2020-04-11",
        "2020-07-11",
        "2020-10-10"
    ],
    2025: [
        "2025-04-05",
        "2025-07-05",
        "2025-10-04"
    ]
}


results = []

print("\nANATOMY OF A HIT — MULTI-WEEK TEST")
print("-----------------------------------")


for year, chart_dates in dates.items():

    hot100_weeks = []
    top10_weeks = []
    unique_artist_counts = []

    for date in chart_dates:

        chart = get_chart(date)

        hot100_weeks.append(
            chart["weeks_on_chart"].mean()
        )

        top10_weeks.append(
            chart.head(10)["weeks_on_chart"].mean()
        )

        unique_artist_counts.append(
            chart["artist"].nunique()
        )

        print(f"Loaded {date}")

    results.append({
        "year": year,
        "avg_weeks_hot100": round(
            sum(hot100_weeks) / len(hot100_weeks), 2
        ),
        "avg_weeks_top10": round(
            sum(top10_weeks) / len(top10_weeks), 2
        ),
        "avg_unique_artists": round(
            sum(unique_artist_counts) /
            len(unique_artist_counts), 2
        )
    })


results_df = pd.DataFrame(results)


print("\n-----------------------------------")
print("MULTI-WEEK SUMMARY")
print("-----------------------------------")

print(results_df.to_string(index=False))
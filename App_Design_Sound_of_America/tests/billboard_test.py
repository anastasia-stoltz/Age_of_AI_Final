import requests
import pandas as pd


def get_chart(date):
    url = f"https://raw.githubusercontent.com/mhollingshead/billboard-hot-100/main/date/{date}.json"

    response = requests.get(url)
    response.raise_for_status()

    chart = response.json()

    df = pd.DataFrame(chart["data"])
    df["chart_date"] = chart["date"]

    return df


# Pull one chart from two different eras
chart_1985 = get_chart("1985-07-06")
chart_2025 = get_chart("2025-07-05")


print("\n1985 Top 10")
print(
    chart_1985[
        ["song", "artist", "this_week", "peak_position", "weeks_on_chart"]
    ].head(10)
)


print("\n2025 Top 10")
print(
    chart_2025[
        ["song", "artist", "this_week", "peak_position", "weeks_on_chart"]
    ].head(10)
)


print("\nAVERAGE WEEKS ON CHART")

print(
    "1985:",
    round(chart_1985["weeks_on_chart"].mean(), 2)
)

print(
    "2025:",
    round(chart_2025["weeks_on_chart"].mean(), 2)
)
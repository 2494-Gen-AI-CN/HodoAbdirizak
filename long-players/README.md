# Grammy album lengths

This chart shows how long the Grammy Album of the Year winners are. It has one winner for each ceremony from 1977 to 2026.

## Run it

You need Python 3. Run these commands from this folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Then run:

```bash
.venv/bin/python grammy_album_lengths.py
```

This saves the chart as `album_lengths.png`.

## Files

- `albums.csv` has the year, album, artist and runtime for each winner.
- `grammy_album_lengths.py` makes the chart.
- `requirements.txt` has the libraries needed to run the script.

The line joins the winners in order. A few album covers are shown on the chart. If a cover can't be found, the script skips it and keeps going.

## Editing the list

You can change the rows in `albums.csv`. Leave the column names at the top. Runtime is in minutes, so `40.5` means 40 minutes and 30 seconds. The year is the ceremony year, which can be later than the album's release year.

The winners are listed in the [Grammy Album of the Year archive](https://www.grammy.com/awards/categories/album-of-the-year/). Runtimes are approximate and can vary by album edition. This chart only includes the winners.

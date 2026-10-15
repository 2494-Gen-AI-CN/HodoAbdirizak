import csv
import os
import sys
import time

import discogs_client
from dotenv import load_dotenv

load_dotenv()

TARGET_COUNT = 10  # test with 10 first; raise to 300 once ratings show up
REQUEST_DELAY = 1.1  # stay under Discogs' 60 requests/minute


class MissingToken(RuntimeError):
    pass


def create_client():
    token = os.getenv("DISCOGS_TOKEN")
    contact = os.getenv("DISCOGS_CONTACT", "long-players-contact")

    if not token:
        raise MissingToken("DISCOGS_TOKEN is missing. Check your .env file.")

    return discogs_client.Client(
        f"long-players/0.1 ({contact})",
        user_token=token,
    )


def get_rating(client, master_id):
    """Return average_rating for a master's main release."""
    try:
        master = client.master(int(master_id))
        master.refresh()
        time.sleep(REQUEST_DELAY)

        main_release_id = master.data.get("main_release")
        if not main_release_id:
            print(f"  no main_release for master {master_id}")
            return None, None

        release = client.release(int(main_release_id))
        release.refresh()
        time.sleep(REQUEST_DELAY)

        rating = (release.data.get("community") or {}).get("rating") or {}
        return rating.get("average")

    except Exception as e:
        print(f"  rating lookup failed for master {master_id}: {e!r}")
        return None, None


def get_top_albums():
    """Return the most-collected albums on Discogs with relevant album info (album, artist, year, genre, rating)."""
    client = create_client()
    albums = []

    results = client.search("", type="master", sort="have", sort_order="desc")
    results.per_page = 100

    max_pages = min(results.pages, 20)
    page_num = 1

    while len(albums) < TARGET_COUNT and page_num <= max_pages:
        page = results.page(page_num)
        if not page:
            break

        for result in page:
            data = result.data
            title = data.get("title", "")
            if " - " not in title:
                continue
            artist, album = title.split(" - ", 1)

            genres = data.get("genre") or []
            rating = get_rating(client, data.get("id"))

            albums.append({
                "album": album.strip(),
                "artist": artist.strip(),
                "year": data.get("year"),
                "genre": genres[0] if genres else "Unknown",
                "rating": rating
            })

            if len(albums) == TARGET_COUNT:
                break

        page_num += 1

    return albums


if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/albums_raw.csv"

    albums = get_top_albums()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["album", "artist", "year", "genre",
                        "rating"],
        )
        writer.writeheader()
        writer.writerows(albums)

    print(f"Saved {len(albums)} albums to {output_path}")
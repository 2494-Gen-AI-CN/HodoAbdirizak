from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import random
import webbrowser

ROUNDS_PER_GAME = 10
GAME_PAGE = Path(__file__).with_name("game.html")

# Each country has a display name and a two-letter flag image code.
COUNTRIES = [{'name': 'Afghanistan', 'code': 'af'},
 {'name': 'Albania', 'code': 'al'},
 {'name': 'Algeria', 'code': 'dz'},
 {'name': 'Andorra', 'code': 'ad'},
 {'name': 'Angola', 'code': 'ao'},
 {'name': 'Antigua and Barbuda', 'code': 'ag'},
 {'name': 'Argentina', 'code': 'ar'},
 {'name': 'Armenia', 'code': 'am'},
 {'name': 'Australia', 'code': 'au'},
 {'name': 'Austria', 'code': 'at'},
 {'name': 'Azerbaijan', 'code': 'az'},
 {'name': 'Bahamas', 'code': 'bs'},
 {'name': 'Bahrain', 'code': 'bh'},
 {'name': 'Bangladesh', 'code': 'bd'},
 {'name': 'Barbados', 'code': 'bb'},
 {'name': 'Belarus', 'code': 'by'},
 {'name': 'Belgium', 'code': 'be'},
 {'name': 'Belize', 'code': 'bz'},
 {'name': 'Benin', 'code': 'bj'},
 {'name': 'Bhutan', 'code': 'bt'},
 {'name': 'Bolivia', 'code': 'bo'},
 {'name': 'Bosnia and Herzegovina', 'code': 'ba'},
 {'name': 'Botswana', 'code': 'bw'},
 {'name': 'Brazil', 'code': 'br'},
 {'name': 'Brunei', 'code': 'bn'},
 {'name': 'Bulgaria', 'code': 'bg'},
 {'name': 'Burkina Faso', 'code': 'bf'},
 {'name': 'Burundi', 'code': 'bi'},
 {'name': 'Cabo Verde', 'code': 'cv'},
 {'name': 'Cambodia', 'code': 'kh'},
 {'name': 'Cameroon', 'code': 'cm'},
 {'name': 'Canada', 'code': 'ca'},
 {'name': 'Central African Republic', 'code': 'cf'},
 {'name': 'Chad', 'code': 'td'},
 {'name': 'Chile', 'code': 'cl'},
 {'name': 'China', 'code': 'cn'},
 {'name': 'Colombia', 'code': 'co'},
 {'name': 'Comoros', 'code': 'km'},
 {'name': 'Republic of the Congo', 'code': 'cg'},
 {'name': 'Costa Rica', 'code': 'cr'},
 {'name': "Côte d'Ivoire", 'code': 'ci'},
 {'name': 'Croatia', 'code': 'hr'},
 {'name': 'Cuba', 'code': 'cu'},
 {'name': 'Cyprus', 'code': 'cy'},
 {'name': 'Czechia', 'code': 'cz'},
 {'name': 'North Korea', 'code': 'kp'},
 {'name': 'Democratic Republic of the Congo', 'code': 'cd'},
 {'name': 'Denmark', 'code': 'dk'},
 {'name': 'Djibouti', 'code': 'dj'},
 {'name': 'Dominica', 'code': 'dm'},
 {'name': 'Dominican Republic', 'code': 'do'},
 {'name': 'Ecuador', 'code': 'ec'},
 {'name': 'Egypt', 'code': 'eg'},
 {'name': 'El Salvador', 'code': 'sv'},
 {'name': 'Equatorial Guinea', 'code': 'gq'},
 {'name': 'Eritrea', 'code': 'er'},
 {'name': 'Estonia', 'code': 'ee'},
 {'name': 'Eswatini', 'code': 'sz'},
 {'name': 'Ethiopia', 'code': 'et'},
 {'name': 'Fiji', 'code': 'fj'},
 {'name': 'Finland', 'code': 'fi'},
 {'name': 'France', 'code': 'fr'},
 {'name': 'Gabon', 'code': 'ga'},
 {'name': 'Gambia', 'code': 'gm'},
 {'name': 'Georgia', 'code': 'ge'},
 {'name': 'Germany', 'code': 'de'},
 {'name': 'Ghana', 'code': 'gh'},
 {'name': 'Greece', 'code': 'gr'},
 {'name': 'Grenada', 'code': 'gd'},
 {'name': 'Guatemala', 'code': 'gt'},
 {'name': 'Guinea', 'code': 'gn'},
 {'name': 'Guinea-Bissau', 'code': 'gw'},
 {'name': 'Guyana', 'code': 'gy'},
 {'name': 'Haiti', 'code': 'ht'},
 {'name': 'Honduras', 'code': 'hn'},
 {'name': 'Hungary', 'code': 'hu'},
 {'name': 'Iceland', 'code': 'is'},
 {'name': 'India', 'code': 'in'},
 {'name': 'Indonesia', 'code': 'id'},
 {'name': 'Iran', 'code': 'ir'},
 {'name': 'Iraq', 'code': 'iq'},
 {'name': 'Ireland', 'code': 'ie'},
 {'name': 'Italy', 'code': 'it'},
 {'name': 'Jamaica', 'code': 'jm'},
 {'name': 'Japan', 'code': 'jp'},
 {'name': 'Jordan', 'code': 'jo'},
 {'name': 'Kazakhstan', 'code': 'kz'},
 {'name': 'Kenya', 'code': 'ke'},
 {'name': 'Kiribati', 'code': 'ki'},
 {'name': 'Kuwait', 'code': 'kw'},
 {'name': 'Kyrgyzstan', 'code': 'kg'},
 {'name': 'Laos', 'code': 'la'},
 {'name': 'Latvia', 'code': 'lv'},
 {'name': 'Lebanon', 'code': 'lb'},
 {'name': 'Lesotho', 'code': 'ls'},
 {'name': 'Liberia', 'code': 'lr'},
 {'name': 'Libya', 'code': 'ly'},
 {'name': 'Liechtenstein', 'code': 'li'},
 {'name': 'Lithuania', 'code': 'lt'},
 {'name': 'Luxembourg', 'code': 'lu'},
 {'name': 'Madagascar', 'code': 'mg'},
 {'name': 'Malawi', 'code': 'mw'},
 {'name': 'Malaysia', 'code': 'my'},
 {'name': 'Maldives', 'code': 'mv'},
 {'name': 'Mali', 'code': 'ml'},
 {'name': 'Malta', 'code': 'mt'},
 {'name': 'Marshall Islands', 'code': 'mh'},
 {'name': 'Mauritania', 'code': 'mr'},
 {'name': 'Mauritius', 'code': 'mu'},
 {'name': 'Mexico', 'code': 'mx'},
 {'name': 'Micronesia', 'code': 'fm'},
 {'name': 'Monaco', 'code': 'mc'},
 {'name': 'Mongolia', 'code': 'mn'},
 {'name': 'Montenegro', 'code': 'me'},
 {'name': 'Morocco', 'code': 'ma'},
 {'name': 'Mozambique', 'code': 'mz'},
 {'name': 'Myanmar', 'code': 'mm'},
 {'name': 'Namibia', 'code': 'na'},
 {'name': 'Nauru', 'code': 'nr'},
 {'name': 'Nepal', 'code': 'np'},
 {'name': 'Netherlands', 'code': 'nl'},
 {'name': 'New Zealand', 'code': 'nz'},
 {'name': 'Nicaragua', 'code': 'ni'},
 {'name': 'Niger', 'code': 'ne'},
 {'name': 'Nigeria', 'code': 'ng'},
 {'name': 'North Macedonia', 'code': 'mk'},
 {'name': 'Norway', 'code': 'no'},
 {'name': 'Oman', 'code': 'om'},
 {'name': 'Pakistan', 'code': 'pk'},
 {'name': 'Palau', 'code': 'pw'},
 {'name': 'Palestine', 'code': 'ps'},
 {'name': 'Panama', 'code': 'pa'},
 {'name': 'Papua New Guinea', 'code': 'pg'},
 {'name': 'Paraguay', 'code': 'py'},
 {'name': 'Peru', 'code': 'pe'},
 {'name': 'Philippines', 'code': 'ph'},
 {'name': 'Poland', 'code': 'pl'},
 {'name': 'Portugal', 'code': 'pt'},
 {'name': 'Qatar', 'code': 'qa'},
 {'name': 'South Korea', 'code': 'kr'},
 {'name': 'Moldova', 'code': 'md'},
 {'name': 'Romania', 'code': 'ro'},
 {'name': 'Russia', 'code': 'ru'},
 {'name': 'Rwanda', 'code': 'rw'},
 {'name': 'Saint Kitts and Nevis', 'code': 'kn'},
 {'name': 'Saint Lucia', 'code': 'lc'},
 {'name': 'Saint Vincent and the Grenadines', 'code': 'vc'},
 {'name': 'Samoa', 'code': 'ws'},
 {'name': 'San Marino', 'code': 'sm'},
 {'name': 'Sao Tome and Principe', 'code': 'st'},
 {'name': 'Saudi Arabia', 'code': 'sa'},
 {'name': 'Senegal', 'code': 'sn'},
 {'name': 'Serbia', 'code': 'rs'},
 {'name': 'Seychelles', 'code': 'sc'},
 {'name': 'Sierra Leone', 'code': 'sl'},
 {'name': 'Singapore', 'code': 'sg'},
 {'name': 'Slovakia', 'code': 'sk'},
 {'name': 'Slovenia', 'code': 'si'},
 {'name': 'Solomon Islands', 'code': 'sb'},
 {'name': 'Somalia', 'code': 'so'},
 {'name': 'South Africa', 'code': 'za'},
 {'name': 'South Sudan', 'code': 'ss'},
 {'name': 'Spain', 'code': 'es'},
 {'name': 'Sri Lanka', 'code': 'lk'},
 {'name': 'Sudan', 'code': 'sd'},
 {'name': 'Suriname', 'code': 'sr'},
 {'name': 'Sweden', 'code': 'se'},
 {'name': 'Switzerland', 'code': 'ch'},
 {'name': 'Syria', 'code': 'sy'},
 {'name': 'Tajikistan', 'code': 'tj'},
 {'name': 'Tanzania', 'code': 'tz'},
 {'name': 'Thailand', 'code': 'th'},
 {'name': 'Timor-Leste', 'code': 'tl'},
 {'name': 'Togo', 'code': 'tg'},
 {'name': 'Tonga', 'code': 'to'},
 {'name': 'Trinidad and Tobago', 'code': 'tt'},
 {'name': 'Tunisia', 'code': 'tn'},
 {'name': 'Türkiye', 'code': 'tr'},
 {'name': 'Turkmenistan', 'code': 'tm'},
 {'name': 'Tuvalu', 'code': 'tv'},
 {'name': 'Uganda', 'code': 'ug'},
 {'name': 'Ukraine', 'code': 'ua'},
 {'name': 'United Arab Emirates', 'code': 'ae'},
 {'name': 'United Kingdom', 'code': 'gb'},
 {'name': 'United States', 'code': 'us'},
 {'name': 'Uruguay', 'code': 'uy'},
 {'name': 'Uzbekistan', 'code': 'uz'},
 {'name': 'Vanuatu', 'code': 'vu'},
 {'name': 'Vatican City', 'code': 'va'},
 {'name': 'Venezuela', 'code': 've'},
 {'name': 'Vietnam', 'code': 'vn'},
 {'name': 'Yemen', 'code': 'ye'},
 {'name': 'Zambia', 'code': 'zm'},
 {'name': 'Zimbabwe', 'code': 'zw'}]

score = 0
total = 0
current_country = None
answered = False


def make_question():
    global current_country, answered

    if total >= ROUNDS_PER_GAME:
        return {"finished": True, "score": score, "total": total}

    current_country = random.choice(COUNTRIES)
    other_countries = [country for country in COUNTRIES if country != current_country]
    choices = [current_country] + random.sample(other_countries, 3)
    random.shuffle(choices)
    answered = False

    return {
        "flag_code": current_country["code"],
        "choices": [country["name"] for country in choices],
        "score": score,
        "total": total,
    }


def check_answer(selected_name):
    global score, total, answered

    if current_country is None or answered:
        return {"error": "This question has already been answered."}

    answered = True
    total += 1
    correct = selected_name == current_country["name"]

    if correct:
        score += 1

    return {
        "correct": correct,
        "answer": current_country["name"],
        "score": score,
        "total": total,
        "finished": total == ROUNDS_PER_GAME,
    }


def reset_game():
    global score, total, current_country, answered
    score = 0
    total = 0
    current_country = None
    answered = False


class GameHandler(BaseHTTPRequestHandler):

    def send_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            page = GAME_PAGE.read_text(encoding="utf-8").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
        elif self.path == "/api/question":
            self.send_json(make_question())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/answer":
            length = int(self.headers.get("Content-Length", 0))
            request_text = self.rfile.read(length).decode("utf-8")
            request_data = json.loads(request_text)
            result = check_answer(request_data.get("country", ""))
            self.send_json(result)
        elif self.path == "/api/restart":
            reset_game()
            self.send_json({"restarted": True})
        else:
            self.send_response(404)
            self.end_headers()


def main():
    address = ("127.0.0.1", 0)
    server = HTTPServer(address, GameHandler)
    port = server.server_address[1]
    game_url = "http://127.0.0.1:" + str(port)
    print("Guess the Flag is running at " + game_url)
    print("Keep this window open while you play. Press Ctrl+C to stop.")
    webbrowser.open(game_url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGame server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

# Heti AI GitHub-válogatás – Gemini + Python fallback + Gmail

Minden pénteken 09:17-kor (Europe/Budapest) a GitHub Actions 10–15 releváns GitHub-repóról magyar nyelvű HTML, TXT és JSON jelentést készít, és Gmailen elküldi. A `DRY_RUN=true` kikapcsolja a levélküldést. A jelentések az Actions futtatás **Artifacts** részéből is letölthetők (30 napig).

## Működés

1. A GitHub Search API az elmúlt 8 napban aktív nyilvános repókat keres négy témában: coding agents/MCP, QA/Playwright, Unity/game dev és üzleti/RAG/finance.
2. Ha van `GEMINI_API_KEY`, a `GEMINI_MODEL` beállítás szerinti modellt kéri meg a magyar nyelvű, 10–15 elemű értékelésre (a jelenlegi alapérték és workflow-beállítás: `gemini-3.8-flash`). A kiválasztott repóneveket a kód a GitHub-találatokhoz ellenőrzi.
3. Ha nincs kulcs, a Gemini API kvótahibát ad, nem elérhető, vagy érvénytelen választ ad, a **Python fallback** determinisztikus, kategóriák között körbeforgó kiválasztást végez (alapból 12 elem). A fallback nem állítja, hogy AI-elemezte a repókat.
4. Mindkét mód előállítja a `reports/digest.html`, `reports/digest.txt`, `reports/selected.json` fájlokat. A JSON `engine` mezője `gemini` vagy `python`.

## Beállítás

1. Nyisd meg a [Google AI Studio API Keys](https://aistudio.google.com/api-keys) felületet, és hozz létre Gemini API-kulcsot olyan projektben, amely jogosult a Free Tierre.
2. GitHub → **Settings → Secrets and variables → Actions → New repository secret**: `GEMINI_API_KEY` = az API-kulcs értéke. Soha ne commitold vagy másold chatbe.
3. A GitHub Actions automatikusan biztosítja a `GITHUB_TOKEN` értéket. Az `OPENAI_API_KEY` nem szükséges; a levélküldéshez szükséges Gmail-beállításokat lent találod.
4. A Gemini ingyenes kvótája és a modellhozzáférés fiók- és projektfüggő; ellenőrizd az [AI Studio rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) oldalon. Free Tierben a beküldött tartalom a szolgáltatás fejlesztésére felhasználható; kizárólag nyilvános GitHub-metaadatokat küldünk.

## Tesztelés

GitHub → **Actions → Weekly AI GitHub digest → Run workflow**:

- `force_fallback=true`: Gemini nélkül generál jelentést, az ingyenes Python ágat teszteli; a levélküldést a `dry_run=true` kapcsolja ki.
- `force_fallback=false`: megpróbálja a Geminit, hiba vagy hiányzó kulcs esetén fallbackre vált.
- A futtatás után töltsd le az `ai-github-digest-<run_number>` artifactot.

Helyben:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
export GITHUB_TOKEN="$(gh auth token)"  # GitHub CLI-vel bejelentkezve
DRY_RUN=true FORCE_FALLBACK=true python scripts/digest.py
```

A `GITHUB_TOKEN`-t helyben ne írd be valódi értékkel a shell historyba; használj biztonságos környezeti változót vagy `.env` fájlt (gitignored).

## Kódszerkezet és felelősségek

Az alkalmazáskód az `ai_digest/` csomagban található. A `scripts/digest.py` vékony indítófájl, ezért a meglévő Actions-parancs változatlanul használható. A projekt gyökeréből a `python -m ai_digest` is ugyanazt a folyamatot indítja. Python 3.10 vagy újabb szükséges; a workflow Python 3.12-t használ.

| Fájl | Felelősség |
| --- | --- |
| `config/categories.json` | Kategóriák és GitHub-keresőkifejezések, a meglévő `CATEGORIES` struktúrában |
| `config/report_content.json` | Fallback-szövegek, kategóriánkénti példák, jelentéscímkék |
| `config/gemini_prompt.txt` | A Gemini rendszerutasítása |
| `ai_digest/models.py` | Adatszerződések: repók, jelentéselemek, ajánlások, szerkeszthető tartalom |
| `ai_digest/settings.py` | Futásidejű beállítások és környezeti változók beolvasása |
| `ai_digest/configuration.py` | Konfigurációs fájlok betöltése és szerkezetük ellenőrzése |
| `ai_digest/github.py`, `gemini.py`, `gmail.py` | Szolgáltatásonként elkülönített API-integrációk |
| `ai_digest/http.py` | Közös JSON HTTP-kérések |
| `ai_digest/selection.py` | Rangsorolás és kategóriák közötti kiegyensúlyozott kiválasztás |
| `ai_digest/fallback.py`, `generation.py` | Szabályalapú jelentésépítés, illetve AI/fallback döntés |
| `ai_digest/validation.py` | Jelentésséma és repo-hivatkozások ellenőrzése |
| `ai_digest/rendering.py`, `storage.py` | HTML/TXT formázás, illetve HTML/TXT/JSON fájlok mentése |
| `ai_digest/application.py` | A keresés → generálás → ellenőrzés → mentés → küldés folyamat |
| `ai_digest/cli.py` | Beállítások betöltése, konkrét szolgáltatások bekötése, hibakód kezelése |

Az SRP szerint a konfiguráció, az üzleti szabályok, a megjelenítés és a külső műveletek külön változtathatók. A függőségmegfordítást (DIP) a `run_digest` paraméterként kapott kereső-, generáló- és levélküldő függvényei biztosítják. Másik AI-szolgáltató vagy tesztbeli helyettesítő a folyamat átírása nélkül beköthető (OCP); ehhez nincs szükség közös ősosztályra.

A modulok importálása nem olvas `.env`-et vagy konfigurációs fájlt, és nem indít hálózati hívást. A CLI a projekt gyökeréhez viszonyítva tölti be a `.env` és `config/` tartalmát. A kategóriák sorrendje a fallback kiválasztási sorrendjét is meghatározza; új kategóriához a `fallback.examples` alatt adható saját példa. A szövegsablonok helyőrzői: `fallback.why` → `{category}`, `fallback.intro` → `{reason}`, `rendering.subject` → `{date}`.

A `tests/` a felelősségi körökhöz igazodik: konfiguráció, jelentésfeldolgozás, API-integrációk és teljes alkalmazásfolyamat. A tesztek helyettesítik a külső szolgáltatásokat, ideiglenes könyvtárba írnak, és nem küldenek valódi levelet.

## Fontos korlátok

- A GitHub Search `pushed` mezője nem garantál jelentős funkciófrissítést; a licenc metaadat nem jogi audit.
- Nincs korábbi hetek közti perzisztens deduplikáció. Ugyanaz a repo később ismét bekerülhet.
- A Python fallback kategóriák között egyenletesebb, de általános leírásokat ad; nem talál ki README-ben nem ellenőrzött funkciókat.
- Harmadik fél kódja nem fut. A GitHub-leírások nem utasítások.
- A `scripts/oauth_setup.py` helyi OAuth-beállító segédprogram; a workflow ezt nem futtatja, a levélküldéshez a beállított secreteket használja.
- Az időzített workflow a default branchből fut. Publikus repo inaktivitásakor a GitHub deaktiválhatja.


## Gmail-küldés (visszakapcsolva)

A heti GitHub Actions futás a Gemini-válogatás vagy Python fallback után automatikusan elküldi a teljes HTML + szöveges jelentést a `rob.pecz@gmail.com` címre. A jelentés az Actions Artifacts között továbbra is elérhető.

A **Settings → Secrets and variables → Actions** alatt szükséges: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`. A korábban beállított, érvényes OAuth-kulcsok újrahasználhatók. A `GEMINI_API_KEY` továbbra is szükséges a Gemini ághoz; nélküle automatikusan Python fallback fut.

Manuális teszt: Actions → Weekly AI GitHub digest → Run workflow → `force_fallback=false`, `dry_run=false`. A naplóban a `Gmail send confirmed; message ID:` sor jelzi az API-küldés visszaigazolását. A `dry_run=true` létrehozza az artifactokat, de nem küld levelet. Gemini-kvótahiba esetén a Python fallback eredményét küldi el. A Gmail- vagy OAuth-hiba nem némul el, a workflow sikertelen lesz, a jelentés artifactként megmarad.

A `force_fallback=true` **nem** kapcsolja ki az emailt; csak a Geminit kerüli meg. Titkos adatokat soha ne committolj a repositoryba.

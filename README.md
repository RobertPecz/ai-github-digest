# Heti AI GitHub-válogatás – Gemini + Python fallback + Gmail

Minden pénteken 09:17-kor (Europe/Budapest) a GitHub Actions 10–15 releváns GitHub-repóról magyar nyelvű HTML, TXT és JSON jelentést készít. **Ez a változat nem küld e-mailt.** A jelentések az Actions futtatás **Artifacts** részéből tölthetők le (30 napig).

## Működés

1. A GitHub Search API az elmúlt 8 napban aktív nyilvános repókat keres négy témában: coding agents/MCP, QA/Playwright, Unity/game dev és üzleti/RAG/finance.
2. Ha van `GEMINI_API_KEY`, a `gemini-2.5-flash-lite` modellt kéri meg a magyar nyelvű, 10–15 elemű értékelésre. A kiválasztott repóneveket a kód a GitHub-találatokhoz ellenőrzi.
3. Ha nincs kulcs, a Gemini API kvótahibát ad, nem elérhető, vagy érvénytelen választ ad, a **Python fallback** determinisztikus, kategóriák között körbeforgó kiválasztást végez (alapból 12 elem). A fallback nem állítja, hogy AI-elemezte a repókat.
4. Mindkét mód előállítja a `reports/digest.html`, `reports/digest.txt`, `reports/selected.json` fájlokat. A JSON `engine` mezője `gemini` vagy `python`.

## Beállítás

1. Nyisd meg a [Google AI Studio API Keys](https://aistudio.google.com/api-keys) felületet, és hozz létre Gemini API-kulcsot olyan projektben, amely jogosult a Free Tierre.
2. GitHub → **Settings → Secrets and variables → Actions → New repository secret**: `GEMINI_API_KEY` = az API-kulcs értéke. Soha ne commitold vagy másold chatbe.
3. A GitHub Actions automatikusan biztosítja a `GITHUB_TOKEN` értéket. A workflow nem használja az `OPENAI_API_KEY` vagy a Gmail-secreteket.
4. A Gemini ingyenes kvótája és a modellhozzáférés fiók- és projektfüggő; ellenőrizd az [AI Studio rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) oldalon. Free Tierben a beküldött tartalom a szolgáltatás fejlesztésére felhasználható; kizárólag nyilvános GitHub-metaadatokat küldünk.

## Tesztelés

GitHub → **Actions → Weekly AI GitHub digest → Run workflow**:

- `force_fallback=true`: Gemini nélkül generál jelentést, az ingyenes Python ágat teszteli.
- `force_fallback=false`: megpróbálja a Geminit, hiba vagy hiányzó kulcs esetén fallbackre vált.
- A futtatás után töltsd le az `ai-github-digest-<run_number>` artifactot.

Helyben:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests
export GITHUB_TOKEN="$(gh auth token)"  # GitHub CLI-vel bejelentkezve
FORCE_FALLBACK=true python scripts/digest.py
```

A `GITHUB_TOKEN`-t helyben ne írd be valódi értékkel a shell historyba; használj biztonságos környezeti változót vagy `.env` fájlt (gitignored).

## Fontos korlátok

- A GitHub Search `pushed` mezője nem garantál jelentős funkciófrissítést; a licenc metaadat nem jogi audit.
- Nincs korábbi hetek közti perzisztens deduplikáció. Ugyanaz a repo később ismét bekerülhet.
- A Python fallback kategóriák között egyenletesebb, de általános leírásokat ad; nem talál ki README-ben nem ellenőrzött funkciókat.
- Harmadik fél kódja nem fut. A GitHub-leírások nem utasítások.
- A `scripts/oauth_setup.py` korábbi Gmail-segédprogram megmaradhat a repóban, de ez a workflow nem használja, és nem küld e-mailt.
- Az időzített workflow a default branchből fut. Publikus repo inaktivitásakor a GitHub deaktiválhatja.


## Gmail-küldés (visszakapcsolva)

A heti GitHub Actions futás a Gemini-válogatás vagy Python fallback után automatikusan elküldi a teljes HTML + szöveges jelentést a `rob.pecz@gmail.com` címre. A jelentés az Actions Artifacts között továbbra is elérhető.

A **Settings → Secrets and variables → Actions** alatt szükséges: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`. A korábban beállított, érvényes OAuth-kulcsok újrahasználhatók. A `GEMINI_API_KEY` továbbra is szükséges a Gemini ághoz; nélküle automatikusan Python fallback fut.

Manuális teszt: Actions → Weekly AI GitHub digest → Run workflow → `force_fallback=false`, `dry_run=false`. A naplóban a `Gmail send confirmed; message ID:` sor jelzi az API-küldés visszaigazolását. A `dry_run=true` létrehozza az artifactokat, de nem küld levelet. Gemini-kvótahiba esetén a Python fallback eredményét küldi el. A Gmail- vagy OAuth-hiba nem némul el, a workflow sikertelen lesz, a jelentés artifactként megmarad.

A `force_fallback=true` **nem** kapcsolja ki az emailt; csak a Geminit kerüli meg. Titkos adatokat soha ne committolj a repositoryba.

# Heti AI GitHub-válogatás – GitHub Actions + Gmail API

Minden pénteken 09:17-kor (Europe/Budapest), magyar nyelvű HTML + szöveges e-mail 10–15 AI GitHub-repóról. Területek: AI agents/MCP, QA/Playwright, Unity/game dev, monetizálható eszközök/RAG/trading kutatás. A válogatást az OpenAI API fogalmazza meg a GitHub Search API valós metaadatai alapján. A GitHub API nem garantálja a projekt funkcióit; a leírások ellenőrzendők.

## Fontos: a ChatGPT Gmail-plugin NEM ad OAuth tokent a GitHub Actionsnek

A külön workflow-hoz saját Google Cloud OAuth Desktop Client és `gmail.send` scope szükséges. Ezt saját gépen egyszer kell engedélyezni. Nem kell hozzám elküldeni a kulcsokat vagy tokeneket.

## 1. Google Cloud + Gmail OAuth

1. Nyisd meg: https://console.cloud.google.com/ és hozz létre egy projektet (pl. `ai-github-digest`).
2. **APIs & Services → Library**: engedélyezd a **Gmail API**-t.
3. **Google Auth Platform → Branding / Audience / Data Access**: add meg az alkalmazás nevét és a saját e-mail címedet. Személyes Gmail esetén a felhasználótípus **External**. Add hozzá az engedélyt: `https://www.googleapis.com/auth/gmail.send` (kizárólag küldés; nem olvasás).
4. Ha **Testing** státuszban van az External app, add a `rob.pecz@gmail.com` címet a tesztfelhasználókhoz, de **figyelem: Testing módban a refresh token 7 nap után lejárhat!** A tartós heti futtatáshoz állítsd a publikálási státuszt **In production**-re, ha a Google lehetővé teszi. A Gmail-küldés érzékeny scope; a Google további ellenőrzési követelményeket írhat elő. A verifikációs képernyők személyes használatnál eltérhetnek; ismeretlen állapotot ne hagyj jóvá automatikusan.
5. **Google Auth Platform → Clients → Create client → Desktop app**. Töltsd le a JSON-t, és ezen projekt gyökerében nevezd el `credentials.json`-nak. A fájlt a `.gitignore` védi a véletlen commit ellen (de mindig ellenőrizd a `git status`-t).
6. Saját gépen, ebben a mappában:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/oauth_setup.py
```

7. Jelentkezz be a `rob.pecz@gmail.com` fiókba, engedélyezd a `gmail.send` jogot. A terminál kiírja a három értéket; ezeket **CSAK a GitHub Repository Secrets-be** másold.

**Biztonság:** a refresh token gyakorlatilag tartós levélküldési jogosultságot ad az alkalmazásnak. Soha ne commitold, ne tedd issue-ba vagy chatbe. Ha kiszivárgott, vond vissza a Google-fiókban.

## 2. OpenAI API

1. https://platform.openai.com/api-keys → hozz létre API-kulcsot.
2. Állíts be havi költségkeretet/usage alertet az API Platformon. **A ChatGPT Plus előfizetés nem azonos az OpenAI API-kredittel**: külön API-számlázás lehet szükséges.
3. A kód alapból `gpt-4.1-mini` modellt használ; a workflow `OPENAI_MODEL` env változójával módosítható. A modell-hozzáférés az API-fiókodtól függ.

## 3. GitHub repo és secrets

1. Hozz létre egy új **private** GitHub-repót (pl. `ai-github-digest`).
2. Másold fel a projekt fájljait a default branchre (ajánlott `main`). **NE töltsd fel** a `.env`, `credentials.json`, tokenek vagy `.venv` fájlokat.
3. **Settings → Secrets and variables → Actions → New repository secret** alatt hozd létre:

| Secret | Tartalom |
|---|---|
| `OPENAI_API_KEY` | Az OpenAI API kulcsod |
| `GMAIL_CLIENT_ID` | A helyi OAuth helper kimenete |
| `GMAIL_CLIENT_SECRET` | A helyi OAuth helper kimenete |
| `GMAIL_REFRESH_TOKEN` | A helyi OAuth helper kimenete |

A GitHub REST-kereséshez a beépített `GITHUB_TOKEN` elég, külön PAT nem kell. A workflow csak `contents: read` jogosultságot használ.

## 4. Tesztelés

A GitHub repo **Actions → Weekly AI GitHub digest → Run workflow** menüjében:

- **`test_email=true`**: kizárólag egy rövid Gmail API tesztlevelet küld. Ehhez nem szükséges OpenAI-kulcs, és AI-díjat sem okoz.
- **`dry_run=true`**: lekéri és kiválasztja a repókat, megírja a válogatást, és a **workflow Artifacts** közé feltölti a `digest.html`/`digest.txt`/`selected.json` fájlokat. **Nem küld e-mailt.**
- Mindkettő `false`: teljes workflow és Gmail API-s e-mail-küldés.

Ha egy API-hívás hibás, a workflow hibával leáll, és nem állítja, hogy elküldte a levelet. A Gmail sikeres válaszában szereplő message ID a workflow naplóba kerül.

## 5. Időzítés

`.github/workflows/weekly-digest.yml`:

```yaml
on:
  schedule:
    - cron: '17 9 * * 5'
      timezone: Europe/Budapest
```

Ez péntekenként **09:17 budapesti idő szerint**, automatikus téli/nyári időszámítással. A 09:00-s időpont a GitHub Actionsnél terhelt lehet; az időzítés nem másodperc-pontos. Ha pontosan 09:00-t szeretnél, módosítsd `'0 9 * * 5'`-re.

A GitHub csak a default branchen levő időzített workflow-t futtatja. Publikus repo esetén 60 nap inaktivitás után deaktiválhatja az ütemezést.

## Korlátok és biztonság

- A GitHub Search API `pushed` feltétellel keres friss aktivitást; nem feltétlenül újonnan indult projekteket. Nincs tartós előző heti állapot, így egy repó később ismét előkerülhet. A 10–15 elem tematikusan kiegyensúlyozott, amennyire a találatok engedik.
- Minden levél valós GitHub URL-t, csillagszámot, licencazonosítót (ha rendelkezésre áll), legutóbbi push dátumot, használati példát, üzleti lehetőséget és kockázatot tartalmaz. Az AI csak keresési metaadatot lát, nem auditál kódot vagy üzleti bevételt.
- A külső repo-leírások potenciálisan rosszindulatú szövegek. A prompt tiltja az utasításként kezelésüket, a kód csak engedélyezett repóneveket fogad el. Nem futtat harmadik fél kódját.
- A Google OAuth token visszavonásával a levélküldés leállítható. A Gmail API `gmail.send` scope önmagában nem tesz lehetővé levélolvasást.
- Az `EMAIL_FROM` címet a Google-fiókodhoz tartozó küldőként kell engedélyezni; jelenleg mindkettő `rob.pecz@gmail.com`.
- Ajánlott a korábban létrehozott ChatGPT heti repóválogatás kikapcsolása **csak azután**, hogy a GitHub Actions end-to-end tesztje sikeres, különben két párhuzamos heti válogatást kapsz.

## Hibaelhárítás

- `invalid_grant`: visszavont vagy lejárt refresh token; engedélyezd újra a helyi OAuth-folyamatot, ellenőrizd a Testing/In production státuszt.
- `403 insufficientPermissions`: rossz Google scope; az OAuth script kizárólag `gmail.send`-et kér.
- `401 OpenAI`: API-kulcs vagy API-számlázás/hozzáférés hibája.
- `GitHub search 403/429`: keresési rate limit; keresések újrapróbálása később.
- `Workflow not running`: alapértelmezett ág, Actions engedélyezés, repo aktivitás ellenőrzése.

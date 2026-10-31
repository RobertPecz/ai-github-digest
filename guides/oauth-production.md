# Gmail OAuth személyes használatra, saját domain nélkül

A választott beállítás a Google **személyes használati kivétele**: az alkalmazást az üzemeltető a saját Gmail-fiókjával használja. Ehhez nem kell saját domaint vásárolni vagy az alkalmazást Google-verifikációra beküldeni. A kivétel néhány, személyesen ismert felhasználó esetén is alkalmazható; az ellenőrizetlen alkalmazások felhasználói korlátja továbbra is érvényes.

Az **In production publishing státusz** és a **Google-verifikáció** külön beállítás. A személyes alkalmazás lehet In production státuszú és ellenőrizetlen. A Google OAuth-szabályzatában a production alkalmazásokra előírt domain- és ellenőrzési követelmények hatálya külön kizárja a személyes használatot. Ha az alkalmazás később nyilvános szolgáltatássá válik, újra kell vizsgálni ezeket a követelményeket.

## Google Cloud beállítása

1. Válaszd ki a meglévő OAuth-klienshez és a helyi `credentials.json` fájlhoz tartozó Cloud-projektet.
2. **Google Auth Platform → Audience:** a felhasználótípus maradjon **External**. A személyes Gmail-fiók nem Workspace Internal alkalmazás.
3. Az Audience oldalon kattints a **Publish app** gombra, és állítsd a publishing státuszt **In production** állapotra. Ez külön művelet a Branding oldal **Publish branding** gombjától.
4. **Data Access:** a program jogosultsága kizárólag `https://www.googleapis.com/auth/gmail.send` legyen.
5. Az alkalmazásnév és a kapcsolattartói e-mail maradjon valós. A személyes használati kivételhez nem kell külön jóváhagyási kérelmet beadni, saját domaint bekötni vagy brand-verifikációt indítani.
6. Az átállás után végezd el az alábbi egyszeri újraengedélyezést, majd frissítsd a GitHub Actions secretjeit.

Az OAuth-engedélyezéskor megjelenhet a **Google hasn't verified this app** figyelmeztetés. A saját alkalmazásodnál az **Advanced / Speciális → Go to … / Tovább …** lehetőséggel folytathatod, ha a Google ezt felajánlja. A személyes használati kivétel ezt a figyelmeztetést nem tünteti el.

Ezek beállítási lépések; az útmutató módosítása önmagában nem változtatja meg a Cloud-projektet vagy a GitHub secreteket. Ha a felület megakadályozza az átállást, a pontos hiba alapján kell tisztázni az okot.

## Meglévő bemutatkozó oldalak

A statikus bemutatkozó weboldal forrása a `docs/` könyvtár. Nem igényel buildet, JavaScriptet vagy saját háttérszolgáltatást. A repository GitHub Pages-beállítása: `master` ág, `/docs` forráskönyvtár.

Az alapértelmezett GitHub Pages-címen:

| Google Auth Platform mező | URL |
| --- | --- |
| Application home page | `https://robertpecz.github.io/ai-github-digest/` |
| Application privacy policy link | `https://robertpecz.github.io/ai-github-digest/privacy.html` |
| Application terms of service link | `https://robertpecz.github.io/ai-github-digest/terms.html` |

Ezek a weboldal címei, nem OAuth-visszahívási URL-ek. A helyi `scripts/oauth_setup.py` Desktop app típusú OAuth-klienssel működik.

Az oldalak tájékoztatásra továbbra is használhatók. A GitHub Pages-publikálás nem jelent Google-verifikációt, és nem feltétele a fent leírt személyes használati beállításnak.

## Egyszeri újraengedélyezés és refresh token cseréje

External / Testing állapotban a Gmail-jogosultsághoz adott engedély és refresh token 7 nap után lejár. Az In production státusz beállítása után kérj új tokent, hogy már ne a Testing korlátja vonatkozzon rá:

```bash
.venv/bin/python scripts/oauth_setup.py
```

Ez interaktív, helyi böngészős engedélykérés. A megfelelő Gmail-fiókkal hagyd jóvá a küldést. A segédprogram hitelesítő adatokat ír a helyi terminálra: ezeket kizárólag közvetlenül a repository **Settings → Secrets and variables → Actions** felületére másold, ne chatbe vagy naplófájlba.

Frissítendő secretek: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`. Az értékek ugyanahhoz az OAuth-klienshez tartozzanak. Production módban is visszavonható vagy más okból érvénytelenné válhat egy token; a státusz nem ígér korlátlan érvényességet.

A hitelesítés és a kézbesítés tényleges tesztje a heti workflow kézi futtatása `force_fallback=true`, `dry_run=false` beállítással. Ez valódi levelet küld a workflow-ban megadott címzettnek. A `dry_run=true` a jelentést ellenőrzi, de a Gmail OAuth-ot nem teszteli.

## Hivatalos útmutatók

- [Google OAuth branding és domainkövetelmények](https://support.google.com/cloud/answer/15549049?hl=en)
- [Audience és a Testing mód korlátai](https://support.google.com/cloud/answer/15549945?hl=en)
- [Sensitive scope ellenőrzés és személyes használati kivételek](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification)
- [Google OAuth-szabályzat és a személyes használat meghatározása](https://developers.google.com/identity/protocols/oauth2/policies)

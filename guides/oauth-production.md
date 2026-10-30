# Weboldal és Gmail OAuth production beállítás

A statikus bemutatkozó weboldal forrása a `docs/` könyvtár. Nem igényel buildet, JavaScriptet vagy saját háttérszolgáltatást. A repository GitHub Pages-beállítása: `master` ág, `/docs` forráskönyvtár.

## A három nyilvános oldal

Az alapértelmezett GitHub Pages-címen:

| Google Auth Platform mező | URL |
| --- | --- |
| Application home page | `https://robertpecz.github.io/ai-github-digest/` |
| Application privacy policy link | `https://robertpecz.github.io/ai-github-digest/privacy.html` |
| Application terms of service link | `https://robertpecz.github.io/ai-github-digest/terms.html` |

Ezek a weboldal címei, nem OAuth-visszahívási URL-ek. A helyi `scripts/oauth_setup.py` Desktop app típusú OAuth-klienssel működik.

**A Pages-publikálás önmagában nem jelent Google-ellenőrzést.** A Google saját, igazolt domainen kéri a production alkalmazás bemutatkozó oldalát. A `github.io` szolgáltatói cím nem helyettesíti a saját domain tulajdonjogának igazolását. A végleges Branding-beállításhoz a saját domainhez tartozó három URL-t használd.

## Saját domain bekötése

1. Válassz egy ténylegesen birtokolt domaint vagy aldomaint, például `digest.sajatdomain.hu` — ez itt csak példa.
2. A GitHub Pages domainellenőrzéséhez add hozzá a GitHub által kiadott TXT rekordot. Ez külön ellenőrzés a Google Search Console-tól.
3. A repository **Settings → Pages → Custom domain** mezőjében állítsd be a domaint. Ezután a DNS-szolgáltatónál az aldomain CNAME rekordja mutasson a `robertpecz.github.io` névre, repository-útvonal nélkül. Gyökérdomain esetén a GitHub dokumentációjában szereplő A/ALIAS/ANAME beállítás szükséges.
4. Várd meg a DNS-ellenőrzést és a tanúsítványt; kapcsold be az **Enforce HTTPS** lehetőséget.
5. A Google Search Console-ban a Cloud-projekt Owner vagy Editor Google-fiókjával igazold a domaint, például a kapott DNS TXT rekorddal. Ne használj kitalált ellenőrzőkódot.
6. Ellenőrizd a főoldalt és a két tájékoztató oldalt kijelentkezve is. A relatív linkek a saját domainen is működnek.

## Google Cloud

1. A helyi `credentials.json` fájlhoz tartozó Cloud-projektet válaszd ki. A fájlt ne tedd közzé.
2. **Google Auth Platform → Branding:** alkalmazásnév `AI GitHub Digest`; support e-mail az üzemeltető által figyelt cím; a saját domain szerepeljen az **Authorized domains** listában; add meg a végleges home/privacy/terms URL-eket.
3. **Data Access:** a program Google-jogosultsága kizárólag `https://www.googleapis.com/auth/gmail.send`. Ne bővítsd postaláda-olvasásra.
4. **Audience:** a saját, személyes Gmail-fiók használata általában External alkalmazást jelent. A **Publish app** állítja át a publishing státuszt **In production** állapotra. Ez nem azonos a Branding vagy a sensitive scope ellenőrzésének sikerével.
5. Ha csak az üzemeltető vagy néhány személyesen ismert felhasználó használja, vizsgáld meg a Google személyes használati kivételét. Ha ellenőrzés szükséges, a **Verification Center** tényleges kéréseit kövesd; kérhet indoklást és a jogosultság használatát bemutató videót is.

A domain és a felületen látható hiba ismerete nélkül nem állapítható meg, hogy a hiányzó branding, a Testing státusz, a token lejárata vagy más hitelesítési probléma akadályozza a futást.

## Lejárt refresh token cseréje

External / Testing állapotban a Gmail-jogosultsághoz kiadott refresh token 7 nap után lejárhat a Google tesztelési szabálya szerint. Ha a régi token lejárt, a production státusz beállítása után kérj újat:

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
- [GitHub Pages saját domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

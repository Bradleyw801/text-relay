# Text Relay by Brad White

An F-Droid repository for **Relay** and **Texts**, served from GitHub Pages. Relay runs on
the phone that keeps the SIM and Google Messages and forwards every text, RCS included.
Texts reads and answers them on the phone you carry, with or without Google services.

Scan the code with F-Droid (Settings, Repositories, +, Scan QR code) or any F-Droid client,
and both apps install and update from there.

<p align="center">
  <a href="https://bradleyw801.github.io/text-relay/"><img src="site/qr.png" width="300" alt="QR code that adds the Text Relay repository to F-Droid"></a>
</p>

Install page: https://bradleyw801.github.io/text-relay/

| | |
| --- | --- |
| Repository address | `https://bradleyw801.github.io/text-relay/repo` |
| Fingerprint | `9C5C5271C2EF7AA897B9EABC297F79DEBB8DFC533EDBAB1DC2C4C0C794287447` |

## Apps

| App | Package | Goes on |
| --- | --- | --- |
| Relay | `com.textrelay.relay` | The relay device: the phone with the SIM and Google Messages, left on Wi-Fi and a charger |
| Texts | `com.textrelay.texts` | The secondary device: the phone you carry, Google services optional |

Each app pairs with a one-time code made in the other (Texts: Settings, Pair the relay device;
Relay: Pair a phone with Texts). Scan its QR code with the new phone's camera, or type the code.
A code works once, within 15 minutes. Without F-Droid, the current builds are also at
https://bradleyw801.github.io/text-relay/relay.apk and
https://bradleyw801.github.io/text-relay/texts.apk, with their versions in `relay.json`
and `texts.json` next to them.

## Publishing a new version

Put the APK in `fdroid/incoming/`, by `git push` or with "Add file, Upload files" on
GitHub (up to 25 MB a file). Bigger files go in as pieces, which the workflow joins:

```
split -b 9000000 -d -a 2 Relay-0.6.apk Relay-0.6.apk.part
```

The "Publish repository" workflow vets every new build before it goes out. It must be
signed with the key pinned for that app in `fdroid/metadata/<package>.yml`
(`AllowedAPKSigningKeys`) and have a higher version code than the published build. A build
that passes replaces the old one, and the workflow signs a fresh index and deploys it with
the install page and the direct-download copies. A build that fails is deleted and the run
fails, with the reason on the run's page; everything else is still published. The workflow
can also be started by hand from the Actions tab.

Edit `fdroid/metadata/<package>.yml` only if the description should change. The name,
version and icon come from the APK and from `fdroid/metadata/<package>/en-US/icon.png`.

Phones that have the repository get the update on F-Droid's next refresh.

## Keys

The index is signed with a PKCS12 keystore (alias `textrelay`). It is committed only
encrypted, as `fdroid/keystore.p12.enc`; the workflow decrypts it with the
`FDROID_KEYSTORE_PASS` secret, which is also the keystore and key password:

```
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -in fdroid/keystore.p12.enc -out fdroid/keystore.p12 -pass env:FDROID_KEYSTORE_PASS
```

Keep the password outside GitHub as well. If it is lost, every phone has to remove and
re-add the repository under a new fingerprint.

Relay and Texts share one app signing key, kept with their source. The repository key only
signs the index; an update installs over the app on a phone only if it is signed with the
app key.

## Layout

```
fdroid/config.yml                 repository name, address, key settings (no secrets)
fdroid/keystore.p12.enc           index signing key, encrypted
fdroid/metadata/<package>.yml     name, summary, description, licence, pinned signing key
fdroid/metadata/<package>/en-US/icon.png
fdroid/repo/*.apk                 the apps
fdroid/incoming/                  new builds waiting to be vetted (normally empty)
site/                             install page and QR code
tools/intake.py                   vets new builds (run by the workflow)
licenses/                         licences of code the apps include
.github/workflows/publish.yml     vets, builds the index and deploys GitHub Pages
```

## Licences

Relay and Texts are Brad White's own apps and are not open source. Both include
Java-WebSocket, under the MIT licence in `licenses/Java-WebSocket.txt`. Relay also includes
ZXing's QR code library, under the Apache License 2.0 in `licenses/ZXing.txt`.

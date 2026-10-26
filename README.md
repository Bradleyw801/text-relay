# Text Relay (moved)

Relay and Texts are now called Paigr Relay and Paigr. They're published in
[Brad White's apps](https://bradleyw801.github.io/sidephone-apps/) with the rest of my apps. If you have this
repository in F-Droid, add that one instead to keep getting updates:

| | |
| --- | --- |
| Address | `https://bradleyw801.github.io/sidephone-apps/repo` |
| Fingerprint | `297A48B6E4BE5C0701771CE758E54D7885C3E342FFC46FE28247FA5038E1DAC6` |

Both apps are open source now, at [Bradleyw801/paigr](https://github.com/Bradleyw801/paigr).

This repository still serves Relay 0.6 and Texts 0.3 for phones that have it, but it won't get any new builds.

## How it's published

The "Publish repository" workflow signs the index and deploys it to GitHub Pages, with the page at
https://bradleyw801.github.io/text-relay/, whenever something in `fdroid/`, `site/` or `tools/` changes. It would
still check a build put in `fdroid/incoming/` against the signing key pinned in `fdroid/metadata/<package>.yml`, but
new builds go to Brad White's apps now.

The index is signed with a PKCS12 keystore (alias `textrelay`) that's only committed encrypted, as
`fdroid/keystore.p12.enc`. The workflow decrypts it with the `FDROID_KEYSTORE_PASS` secret, which is also the keystore
and key password:

```
openssl enc -d -aes-256-cbc -pbkdf2 -iter 600000 -md sha256 \
  -in fdroid/keystore.p12.enc -out fdroid/keystore.p12 -pass env:FDROID_KEYSTORE_PASS
```

Keep that password somewhere other than GitHub too. If it's lost, this repository can't be changed without every
phone that has it removing it and adding it again.

Relay 0.6 and Texts 0.3 came out before the apps were open source. Both include Java-WebSocket (MIT,
`licenses/Java-WebSocket.txt`), and Relay also includes ZXing (Apache 2.0, `licenses/ZXing.txt`).

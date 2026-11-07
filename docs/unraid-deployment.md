# Unraid deployment

Plants runs as one container. Keep its persistent app data on an Unraid user share and map that folder to `/app/data` in the container.

## Before the first install

1. In Unraid, create a Docker container using `ghcr.io/dhrandy/plants:latest` after the release workflow has published the image. The workflow currently publishes only after a successful test run on `main`; feature branches do not publish an image.
2. Set the container path `/app/data` to a host path such as `/mnt/user/appdata/plants`. This folder contains `plants.db`, `encyclopedia.db`, and uploaded photos. Keep it outside the container so recreating or updating the container preserves data.
3. Map host port `8653` to container port `8000` (TCP), and set `TZ` to your local IANA timezone, for example `Asia/Dhaka`.
4. If serving through an HTTPS reverse proxy, set `PLANTS_COOKIE_SECURE=true` and set `FORWARDED_ALLOW_IPS` to the proxy's address. Keep the container reachable only through that proxy when trusting forwarded headers.
5. Start the container, open `http://<unraid-host>:8653`, and create the first administrator account.

## Updating

1. Export a backup in **Settings → Backup → Export**, and stop the container before making a filesystem copy of its appdata folder. The export includes application data and photos; the folder copy also captures both SQLite databases.
2. Update to a published image only after the repository test/build workflow succeeds. Pull the new image and recreate the container with the same `/app/data` host mapping and environment settings.
3. On startup, Plants applies additive migrations to `encyclopedia.db`. Initialization keeps the household `plants.db` separate from the encyclopedia database and seeds reference content without replacing existing profile sections. Keep the backup until you have confirmed sign-in, plants, photos, and reference content after the update.

## Building from a feature branch

The current GitHub workflow does not publish feature-branch images. To try an unpublished branch, build its Dockerfile into a private tag on a machine with Docker, transfer/push that image to a registry Unraid can access, and select that exact tag in Unraid. Do not point Unraid at `latest` expecting it to contain feature-branch changes; `latest` is published from `main` only.

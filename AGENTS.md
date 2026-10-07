# Working on this repository

- Develop on `dev` unless the user explicitly requests another branch. Publish changes to `dev`; use a pull request from `dev` to `main` for releases. Do not push to `main` directly. Merge only when the user requests the release.
- Run the relevant checks before publishing changes. GitHub's `Backend checks` and `Frontend build` cover unit/content validation and compilation; they do not replace real registration, email, judge and browser integration checks on a development installation.
- Keep `.env`, `.env.production` and `.env.judge` out of Git. Keep development and production databases separate; do not run development seed or destructive volume commands on production data. Use migrations and a database backup for releases.

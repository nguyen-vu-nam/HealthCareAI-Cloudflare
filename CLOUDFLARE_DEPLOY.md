# Cloudflare deployment

Use [GITHUB_ACTIONS_DEPLOY.md](GITHUB_ACTIONS_DEPLOY.md).

The Windows machine is used for development. GitHub Actions runs Python Worker packaging and deployment on an Ubuntu runner. Pushes to `main` validate the project; production deployment requires a manual `workflow_dispatch` with `deploy=true`.

Do not deploy until D1 schema/migrations have been reviewed and applied, and required GitHub Actions secrets have been configured. Firebase Push and outbound AI Chat are not yet production-verified on Python Workers.

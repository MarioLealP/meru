# Meru - the home lab's container platform

The root of **Meru**, a small in-house container platform (CaaS) on k3s. Argo CD applies this repo to the cluster's
`argocd` namespace; everything else in Meru hangs off it. Changes go in through pull requests that the platform
owner merges - this repo decides what each part of the cluster may do, so nothing here merges on its own.

## What's here

- `projects/platform.yaml` - the platform's fence (an Argo CD AppProject): the parts this repo lists - CNPG,
  Zot, Reloader, ... - which install cluster-wide objects, so it is wide open.
- `projects/<app>.yaml` - one fence per app, `meru-<app>`: its Application may read only the app's own repo plus the
  shared [Nüwa](https://git.clockmost.com/Meru/nuwa) and [Sindri](https://git.clockmost.com/Meru/sindri) charts,
  and deploy only into the app's two namespaces, `<app>` and `<app>-build`, which it may also create. An app's repo
  can't reach another app's namespace or any platform namespace. An app with no fence file deploys nothing.
- `projects/app-kinds.yaml` - the object kinds every app fence allows, in one place (no Secrets: they come from
  OpenBao).

- `appsets/meru-apps.yaml` - finds the apps: every public repo in the `Meru` org with a `deploy/meru.yaml` gets one
  Application, `app-<repo>`, in its fence, deploying into the namespace named after the repo. `deploy/meru.yaml`
  holds `owner`, `chart` (the [nuwa-app](https://git.clockmost.com/Meru/nuwa) release the app was tested with),
  `build` (true: also its build namespace and Sindri runner) and, optionally, `buildLabels` (extra runner labels and
  the image their jobs run in - e.g. `sindri-check` for tests; never `sindri` itself, the only label whose jobs get
  the build keys), and `databaseClients` (other apps' namespaces that may reach this app's Postgres). Every
  namespace also gets Meru's baseline ([meru-baseline](https://git.clockmost.com/Meru/nuwa), pinned here): network
  policies closed by default, so only what the app's own policy names gets through. Argo never deletes what it
  generates: removing an app is a deliberate step.
- `appsets/meru-databases.yaml` - an app's database: a repo that also has `deploy/database/` gets a second
  Application, `app-<repo>-db`, in the same fence and namespace. Separate because the data must outlive every app
  deploy: it never prunes, and the database object itself should carry
  `argocd.argoproj.io/sync-options: Prune=false,Delete=false`. No ordering between the two - the app's migration
  retries until the database answers.

- `platform/<part>.yaml` - the platform's parts, one Argo CD Application each, all in the `platform` fence. An
  explicit list, never discovered: each part installs cluster-wide objects, so adding one is a reviewed change
  here. `scripts/check.sh` fails any Application here that isn't in the `platform` fence: CNPG and its Barman Cloud plugin (Postgres WAL archive + base backups), [Zot](https://git.clockmost.com/Meru/zot), Falco, Reloader (restarts a workload when
  its Secret changes), [Temporal](https://git.clockmost.com/Meru/temporal) and its database. Upstream charts come straight from their
  publishers; everything of ours from a `Meru/` repo.

## Adding an app

1. `projects/<app>.yaml` - copy an existing one, change the name, namespaces, repo and description.
2. Add it to `kustomization.yaml`.
3. `scripts/check.sh` - renders the repo, validates it, and fails if any app fence differs from that one shape.

Pod Security is Kubernetes' own: every app namespace is `restricted`, its build namespace `baseline` (rootless
BuildKit), Falco's `privileged`. CI signs every image with cosign, but nothing checks those signatures when a pod
starts yet.

## Names

Meru's parts carry mythology names; this is what each one does.

| name | role |
|---|---|
| Meru | the platform as a whole; this repo is its root (Argo CD fences, app discovery, platform parts) |
| Nüwa | app templates: the `nuwa-app` Helm chart every app deploys with, plus the new-repo templates (`nuwa-python`, `nuwa-static`, `nuwa-upstream`, `nuwa-binary`) |
| Sindri | app builds: the `sindri-build` chart - each app's build namespace and Gitea runner |
| Shikigami | orchestrator: turns an approved app request into a running app (repo, fence, keys, deploy), and retires it |
| Janus | request intake: takes app requests from the atlas and agents, hands approvals to Xolotl |
| Xolotl | merger: checks and merges Shikigami's trust PRs and approved requests |
| Thoth | CMDB: what exists, how it connects, how it got that way |
| Heimdall | scanner: tells Thoth what really runs in the cluster |
| Anubis | stuck-app reports: finds what is stuck in Thoth, reports it to Zabbix |
| Charon | retired-app cleanup: purges a retired app's namespaces, volumes and secrets after retention |
| Golem | test app: every onboarding step runs on it first |
| Homunculus | test app: hands-off onboarding and retirement |
| Kitsune | test app: approval through the atlas |
| Tanuki | test app: typed and generated secrets |
| Zot, Temporal | the image registry and the workflow engine (their own names) |

## License

MIT - see `LICENSE`.

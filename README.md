# Meru

The root of **Meru**, a small in-house container platform (CaaS) on k3s. Argo CD applies this repo to the cluster's
`argocd` namespace; everything else in Meru hangs off it. Changes go in through pull requests that the platform
owner merges - this repo decides what each part of the cluster may do, so nothing here merges on its own.

## What's here

- `projects/platform.yaml` - the platform's fence (an Argo CD AppProject): the parts this repo lists - Kyverno,
  CNPG, Zot, ... - which install cluster-wide objects, so it is wide open.
- `projects/<app>.yaml` - one fence per app, `meru-<app>`: its Application may read only the app's own repo plus the
  shared [Nüwa](https://git.clockmost.com/Meru/nuwa) and [Sindri](https://git.clockmost.com/Meru/sindri) charts,
  and deploy only into the app's two namespaces, `<app>` and `<app>-build`, which it may also create. An app's repo
  can't reach another app's namespace or any platform namespace. An app with no fence file deploys nothing.
- `projects/app-kinds.yaml` - the object kinds every app fence allows, in one place (no Secrets: they come from
  OpenBao).

Coming here next: the platform's list of parts, and the ApplicationSet that finds app repos - any public repo in the
`Meru` org with a `deploy/meru.yaml` - and gives each one an Application in its fence.

## Adding an app

1. `projects/<app>.yaml` - copy an existing one, change the name, namespaces, repo and description.
2. Add it to `kustomization.yaml`.
3. `scripts/check.sh` - renders the repo, validates it, and fails if any app fence differs from that one shape.

Its signing key and build exception go in [Meru/kyverno](https://git.clockmost.com/Meru/kyverno).

## License

MIT - see `LICENSE`.

"""Check every app fence (AppProject meru-<app>) in a rendered Meru/meru against the one shape an app may have.

An app's fence is trust: what it can deploy and where. So it must name only the app's own repo plus the shared
charts, only the app's own namespaces - its own, its build's, then any environments' <app>-<env> (D126) - and the shared
kinds list; anything more fails here. Which environments an app may have is its request's call, checked by Xolotl
before the fence merges; here only their shape.
"""

import re
import sys
from pathlib import Path

import yaml

CHARTS = ["https://git.clockmost.com/Meru/nuwa.git", "https://git.clockmost.com/Meru/sindri.git"]
SERVER = "https://kubernetes.default.svc"
KINDS = yaml.safe_load(Path(__file__).resolve().parent.parent.joinpath("projects/app-kinds.yaml").read_text())[0][
    "value"
]


ENVIRONMENT = re.compile(r"^[a-z][a-z0-9]{0,7}$")  # Shikigami's request format: an environment's name (D126)


def problems(project: dict) -> list[str]:
    app = project["metadata"]["name"].removeprefix("meru-")
    spec = project["spec"]
    # the environments are whatever namespaces the fence lists after the build's, if each is <app>-<valid name>
    listed = [d.get("namespace", "") for d in spec.get("destinations") or []]
    environments = [ns.removeprefix(f"{app}-") for ns in listed[2:]]
    bad = [ns for ns, env in zip(listed[2:], environments, strict=True) if ns == env or not ENVIRONMENT.match(env)]
    if bad or "build" in environments or len(environments) != len(set(environments)):
        return [f"destinations: {listed!r} - after {app} and {app}-build only {app}-<environment> namespaces"]
    namespaces = [app, f"{app}-build", *(f"{app}-{env}" for env in environments)]
    expected = {
        "description": spec.get("description"),
        "sourceRepos": [f"https://git.clockmost.com/Meru/{app}.git", *CHARTS],
        "destinations": [{"server": SERVER, "namespace": ns} for ns in namespaces],
        "clusterResourceWhitelist": [{"group": "", "kind": "Namespace", "name": ns} for ns in namespaces],
        "namespaceResourceWhitelist": KINDS,
    }
    found = [f"{key}: {spec.get(key)!r}" for key, value in expected.items() if spec.get(key) != value]
    found += [f"unexpected field {key}" for key in spec.keys() - expected.keys()]
    if not spec.get("description"):
        found.append("no description")
    return found


def main() -> None:
    docs = [doc for doc in yaml.safe_load_all(Path(sys.argv[1]).read_text()) if doc]
    fences = [doc for doc in docs if doc["kind"] == "AppProject" and doc["metadata"]["name"].startswith("meru-")]
    failed = False
    # Every Application listed here is a platform part: it belongs in the platform fence, never in default.
    for app in (doc for doc in docs if doc["kind"] == "Application"):
        if app["spec"].get("project") != "platform":
            print(f"Application {app['metadata']['name']}: project {app['spec'].get('project')!r}, not 'platform'")
            failed = True
    for fence in fences:
        for problem in problems(fence):
            print(f"{fence['metadata']['name']}: {problem}")
            failed = True
    if failed:
        sys.exit(1)
    print(f"{len(fences)} app fences ok")


if __name__ == "__main__":
    main()

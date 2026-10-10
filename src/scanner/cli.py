import argparse
import json
from pathlib import Path

from .policy import normalize_target, require_scope
from .storage import Store


def build_parser():
    parser = argparse.ArgumentParser(
        prog="scanner",
        description="Authorized terminal scanner scaffold.",
    )

    parser.add_argument(
        "--workspace",
        default=".scanner",
        help="Scanner workspace directory",
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    commands.add_parser("init")

    scope = commands.add_parser("scope")
    scope_commands = scope.add_subparsers(
        dest="scope_command",
        required=True,
    )

    scope_add = scope_commands.add_parser("add")
    scope_add.add_argument("target")
    scope_commands.add_parser("list")

    plan = commands.add_parser("plan")
    plan.add_argument(
        "--profile",
        choices=["web", "network"],
        default="web",
    )

    run = commands.add_parser("run")
    run.add_argument("--dry-run", action="store_true")

    commands.add_parser("status")

    report = commands.add_parser("report")
    report.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
    )

    return parser


def read_plan(plan_path):
    if not plan_path.exists():
        raise ValueError("No plan found. Run: scanner plan")

    return json.loads(plan_path.read_text(encoding="utf-8"))


def create_report(plan, output_format):
    if output_format == "json":
        return json.dumps(plan, indent=2) + "\n"

    lines = [
        "# Proposed assessment plan",
        "",
        "No live scans have been executed.",
        "",
    ]

    for job in plan["jobs"]:
        lines.append(
            f"- Target: `{job['target']}`"
            f" | Tool: `{job['tool']}`"
            f" | Approval required: `true`"
        )
        lines.append(f"  - Reason: {job['reason']}")

    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    store = Store(args.workspace)
    workspace = Path(args.workspace)
    plan_path = workspace / "plan.json"

    try:
        if args.command == "init":
            store.initialize()
            print(f"Workspace initialized: {workspace}")
            print("Live execution is disabled.")
            return

        if args.command == "scope":
            if args.scope_command == "add":
                target = normalize_target(args.target)
                store.add_target(target)
                print(f"Target recorded: {target}")
                print("Recording a target does not prove authorization.")
            else:
                targets = store.list_targets()

                if not targets:
                    print("No targets recorded.")
                else:
                    for target in targets:
                        print(target)

            return

        if args.command == "plan":
            targets = store.list_targets()

            if not targets:
                raise ValueError(
                    "Add an authorized target before creating a plan."
                )

            jobs = []

            for target in targets:
                jobs.append(
                    {
                        "target": target,
                        "tool": "nmap",
                        "reason": (
                            "Propose bounded service discovery before "
                            "service-specific checks."
                        ),
                    }
                )

            plan = {
                "profile": args.profile,
                "status": "proposed",
                "jobs": jobs,
            }

            workspace.mkdir(parents=True, exist_ok=True)
            plan_path.write_text(
                json.dumps(plan, indent=2),
                encoding="utf-8",
            )

            print(f"Saved {len(jobs)} proposed job(s).")
            print("No network requests were made.")
            return

        if args.command == "status":
            targets = store.list_targets()

            print(f"Scoped targets: {len(targets)}")
            print(f"Plan exists: {plan_path.exists()}")
            print("Live execution: disabled")
            return

        plan = read_plan(plan_path)

        if args.command == "run":
            if not args.dry_run:
                raise ValueError(
                    "Live execution is not implemented. "
                    "Use: scanner run --dry-run"
                )

            allowed_targets = store.list_targets()

            for job in plan["jobs"]:
                require_scope(job["target"], allowed_targets)
                print(
                    f"PROPOSED {job['tool']} -> {job['target']}"
                )
                print(f"  Reason: {job['reason']}")

            print("No scanner processes were started.")
            return

        extension = "json" if args.format == "json" else "md"
        report_path = workspace / f"report.{extension}"

        report_path.write_text(
            create_report(plan, args.format),
            encoding="utf-8",
        )

        print(f"Report saved: {report_path}")

    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        parser.exit(2, f"Error: {error}\n")

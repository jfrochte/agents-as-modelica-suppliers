"""Commission an agent: hand a task to an LLM agent in an isolated working directory.

    python src/commission.py experiments/task1 --harness claude --model claude-opus-5

The agent receives what a supplier receives and nothing else: the brief
(``task.md``), the data of the fitting and validation experiments, the files
that the task file lists under ``supplied``, and the framing instruction
(``frame.md``) as its prompt. It runs in a bubblewrap sandbox in which the
rest of the file system does not exist. Each run gets a directory under
``--out``; the delivery is what the agent leaves in its ``task/work/``.

Requirements, sign-in and options: src/README.md.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = Path("/project")
"""Where the sandbox shows the task and the Python environment, as in the study."""

ISSUED_ROLES = ("fit", "validation")
EFFORT = {"claude": "max", "codex": "max", "opencode": None}
"""Default reasoning setting per harness: the highest that the study's providers offered."""

BINARIES = {"claude": "claude", "codex": "codex", "opencode": "opencode"}
SYSTEM_DIRS = ("/usr", "/bin", "/sbin", "/lib", "/lib64", "/opt")

SELFTEST = r"""
failed=0
check() { if eval "$2" >/dev/null 2>&1; then echo "ok       $1"; else echo "MISSING  $1"; failed=1; fi; }
echo "working directory $(pwd): $(ls -A | tr '\n' ' ')"
echo "home: $(ls -A "$HOME" | tr '\n' ' ')"
echo "tasks visible: $(ls -A "$(dirname "$(pwd)")" | tr '\n' ' ')"
check "OpenModelica" "command -v omc"
printf 'print(String(loadModel(Modelica, {"4.1.0"})));\n' > /tmp/msl.mos
check "Modelica Standard Library 4.1.0" "omc /tmp/msl.mos | grep -q true"
check "Python with numpy, scipy, OMPython" "/project/.venv/bin/python -c 'import numpy, scipy, OMPython'"
check "network" "getent hosts openmodelica.org"
check "harness: $("$AGENT" --version 2>&1 | head -n 1)" "\"$AGENT\" --version"
exit $failed
"""


def issued_files(task_dir: Path, spec: dict) -> list[Path]:
    """The data files a supplier receives."""
    data = task_dir / "data"
    files = [data / f"{name}.csv" for name, e in spec["experiments"].items()
             if e["role"] in ISSUED_ROLES]
    for pattern in spec.get("supplied", ()):
        matched = sorted(data.glob(pattern))
        if not matched:
            raise FileNotFoundError(f"{task_dir}: no file matches supplied = {pattern!r}")
        files += matched
    missing = [f for f in files if not f.exists()]
    if missing:
        raise FileNotFoundError("missing data: " + ", ".join(map(str, missing)))
    return files


def brief(task_dir: Path, criterion: bool) -> str:
    """The brief, with the acceptance criterion inserted before the output package."""
    text = (task_dir / "task.md").read_text(encoding="utf-8")
    if not criterion:
        return text
    section = (HERE / "criterion.md").read_text(encoding="utf-8")
    marker = "## Required output package"
    if marker in text:
        return text.replace(marker, section + marker, 1)
    return text.rstrip("\n") + "\n\n" + section


def prepare(task_dir: Path, run: Path, spec: dict, criterion: bool) -> Path:
    """The agent's working directory: the brief, the issued data and an empty work/."""
    task = run / "task"
    (task / "data").mkdir(parents=True)
    (task / "work").mkdir()
    (task / "task.md").write_text(brief(task_dir, criterion), encoding="utf-8")
    for f in issued_files(task_dir, spec):
        shutil.copy2(f, task / "data" / f.name)
    return task


def agent_command(harness: str, executable: str, model: str, effort: str | None,
                  frame: str) -> list[str]:
    if harness == "claude":
        return [executable, "-p", frame, "--model", model, "--dangerously-skip-permissions",
                *(["--effort", effort] if effort else [])]
    if harness == "codex":
        return [executable, "exec", "--skip-git-repo-check",
                "--dangerously-bypass-approvals-and-sandbox", "-m", model, frame]
    return [executable, "run", "--auto", "-m", model,
            *(["--variant", effort] if effort else []), frame]


def sign_in(harness: str) -> tuple[list[str], Path | None]:
    """How the harness signs in: environment variables, or its login file.

    Stops with a message when the harness has no way to sign in.
    """
    home = Path.home()
    if harness == "claude":
        names = [v for v in ("CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY") if os.environ.get(v)]
        if not names:
            raise SystemExit("Claude Code needs CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`) "
                             "or ANTHROPIC_API_KEY in the environment")
        return names[:1], None
    if harness == "codex":
        if os.environ.get("OPENAI_API_KEY"):
            return ["OPENAI_API_KEY"], None
        login = home / ".codex" / "auth.json"
        if not login.exists():
            raise SystemExit("Codex needs OPENAI_API_KEY or a login (`codex login`)")
        return [], login
    login = home / ".local" / "share" / "opencode" / "auth.json"
    return [], login if login.exists() else None


def sandbox(run: Path, task: Path, inside: Path, harness: str, executable: str,
            model: str, effort: str | None, opencode_config: Path | None,
            extra_ro: list[str], login: Path | None) -> list[str]:
    """The bubblewrap arguments for one run."""
    home = Path.home()
    agent = run / "agent"
    agent.mkdir()
    args = ["bwrap"]
    for d in ("/usr", "/etc"):
        args += ["--ro-bind", d, d]
    for d in ("/bin", "/sbin", "/lib", "/lib64", "/opt"):
        args += ["--ro-bind-try", d, d]
    args += ["--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--tmpfs", "/run",
             "--ro-bind-try", "/run/systemd/resolve", "/run/systemd/resolve",
             "--tmpfs", str(home),
             "--ro-bind-try", str(home / ".openmodelica"), str(home / ".openmodelica")]
    # The Python environment appears at /project/.venv, where the framing
    # instruction says it is; a virtual environment needs its base interpreter.
    args += ["--ro-bind", sys.prefix, str(PROJECT / ".venv")]
    if sys.base_prefix != sys.prefix:
        args += ["--ro-bind", sys.base_prefix, sys.base_prefix]
    # The agent's own program, and nothing else of the home directory.
    real = Path(executable)
    if not str(real).startswith(SYSTEM_DIRS):
        args += ["--ro-bind", str(real.parent), str(real.parent)]
    for path in extra_ro:
        args += ["--ro-bind", path, path]
    args += ["--bind", str(task), str(inside)]

    if harness == "claude":
        (agent / "claude").mkdir()
        args += ["--bind", str(agent / "claude"), str(home / ".claude")]
    elif harness == "codex":
        codex = agent / "codex"
        codex.mkdir()
        config = f'[projects."{inside}"]\ntrust_level = "trusted"\n'
        if effort:
            config = f'model_reasoning_effort = "{effort}"\n\n' + config
        (codex / "config.toml").write_text(config, encoding="utf-8")
        args += ["--bind", str(codex), str(home / ".codex")]
        if login:
            # Codex renews its login in this file, so it is shown writable.
            (codex / "auth.json").touch()
            args += ["--bind", str(login), str(home / ".codex" / "auth.json")]
    else:
        # Configuration and sessions of this run, where OpenCode looks for them.
        config_dir = agent / "config" / "opencode"
        data_dir = agent / "share" / "opencode"
        config_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        if opencode_config:
            shutil.copy2(opencode_config, config_dir / "opencode.json")
        else:
            (config_dir / "opencode.json").write_text(json.dumps(
                {"$schema": "https://opencode.ai/config.json", "model": model}, indent=2))
        args += ["--bind", str(agent / "config"), str(home / ".config"),
                 "--bind", str(agent / "share"), str(home / ".local" / "share")]
        if login:
            (data_dir / "auth.json").touch()
            args += ["--ro-bind", str(login), str(home / ".local" / "share" / "opencode" / "auth.json")]

    args += ["--chdir", str(inside),
             "--unshare-pid", "--unshare-ipc", "--unshare-uts", "--hostname", "sandbox",
             "--die-with-parent"]
    return args


def environment(secrets: list[str], extra: dict[str, str]) -> dict[str, str]:
    """The environment of the sandbox: a few plain variables and the sign-in.

    It is passed to bubblewrap as its environment, not on its command line,
    where every process on the machine could read a token.
    """
    env = {name: os.environ[name] for name in ("PATH", "TERM", "LANG", *secrets)
           if os.environ.get(name)}
    return {**env, "HOME": str(Path.home()), **extra}


def version(command: list[str]) -> str:
    try:
        out = subprocess.run(command, capture_output=True, text=True, timeout=60)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except (OSError, IndexError, subprocess.TimeoutExpired):
        return "unknown"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Hand a task to an LLM agent in a sandbox.")
    parser.add_argument("task_dir")
    parser.add_argument("--harness", choices=sorted(BINARIES), required=True)
    parser.add_argument("--model", required=True,
                        help="model name as the harness expects it; OpenCode: provider/model")
    parser.add_argument("--effort", help="reasoning setting (default: claude max, codex max, "
                                         "opencode the provider's default)")
    parser.add_argument("--criterion", action="store_true",
                        help="add the acceptance criterion to the brief (tasks graded by the residual gate)")
    parser.add_argument("--out", default="runs", help="directory for the runs (default: runs)")
    parser.add_argument("--timeout", type=float, help="stop the agent after so many seconds")
    parser.add_argument("--opencode-config", type=Path, help="OpenCode configuration for your provider")
    parser.add_argument("--bind-ro", action="append", default=[], metavar="PATH",
                        help="a further directory the agent's program needs, shown read-only")
    parser.add_argument("--dry-run", action="store_true",
                        help="check the sandbox instead of starting the agent")
    args = parser.parse_args(argv)

    task_dir = Path(args.task_dir).resolve()
    with open(task_dir / "task.toml", "rb") as fh:
        spec = tomllib.load(fh)
    if args.criterion and spec.get("behaviour", "residual") != "residual":
        parser.error("the criterion states the residual gate; this task is graded otherwise")
    if subprocess.run(["bwrap", "--dev-bind", "/", "/", "true"], capture_output=True).returncode:
        raise SystemExit("bubblewrap cannot create a sandbox here; on Ubuntu 24.04 install "
                         "the AppArmor profile in src/apparmor-bwrap (see src/README.md)")
    found = shutil.which(BINARIES[args.harness])
    if not found:
        raise SystemExit(f"{BINARIES[args.harness]} is not installed")
    executable = os.path.realpath(found)
    effort = args.effort or EFFORT[args.harness]
    secrets, login = ([], None) if args.dry_run else sign_in(args.harness)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    label = re.sub(r"[^A-Za-z0-9._-]+", "-", args.model)
    run = Path(args.out).resolve() / f"{task_dir.name}_{args.harness}_{label}_{stamp}"
    run.mkdir(parents=True)
    task = prepare(task_dir, run, spec, args.criterion)
    inside = PROJECT / "tasks" / task_dir.name
    bwrap = sandbox(run, task, inside, args.harness, executable, args.model, effort,
                    args.opencode_config, args.bind_ro, login)
    frame = (HERE / "frame.md").read_text(encoding="utf-8")
    if args.dry_run:
        command = ["/bin/sh", "-c", SELFTEST]
        env = environment([], {"AGENT": executable})
    else:
        command = agent_command(args.harness, executable, args.model, effort, frame)
        env = environment(secrets, {})

    record = {
        "task": task_dir.name, "harness": args.harness, "model": args.model, "effort": effort,
        "criterion": args.criterion, "dry_run": args.dry_run,
        "harness_version": version([executable, "--version"]),
        "omc_version": version(["omc", "--version"]),
        "sign_in": secrets or ("login file" if login else "none"), "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "data": sorted(p.name for p in (task / "data").iterdir()),
    }
    print(f"run directory: {run}")
    with open(run / "stdout.log", "w") as out, open(run / "stderr.log", "w") as err:
        try:
            code = subprocess.run(bwrap + command, stdout=out, stderr=err, env=env,
                                  timeout=args.timeout).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    record.update(ended=datetime.datetime.now().isoformat(timespec="seconds"), exit_code=code,
                  delivered=sorted(str(p.relative_to(task / "work"))
                                   for p in (task / "work").rglob("*") if p.is_file()
                                   and "build" not in p.relative_to(task / "work").parts))
    (run / "commission.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if args.dry_run:
        print((run / "stdout.log").read_text(), end="")
        print((run / "stderr.log").read_text(), end="", file=sys.stderr)
        return 0 if code == 0 else 1
    print(f"agent ended with {code}; delivered: {', '.join(record['delivered']) or 'nothing'}")
    model = task / "work" / "model.mo"
    if model.exists():
        print(f"grade it: python -m acceptance.grade {args.task_dir} {model} "
              f"--report <the report in {task / 'work'}>")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# Commissioning an agent

`commission.py` hands a task to an LLM agent the way the study did. The agent
works alone in a sandbox, with the brief, the data it may fit on and the
framing instruction, and leaves a model and a report. The acceptance then
grades what it delivered.

```
python src/commission.py experiments/task1 --harness claude --model claude-opus-5
python -m acceptance.grade experiments/task1 runs/<run>/task/work/model.mo \
    --report runs/<run>/task/work/<report>
```

## What the agent sees

Inside the sandbox the agent finds its working directory
`/project/tasks/<task>` with

- `task.md`, the brief of the task,
- `data/`, the data of the fitting and validation experiments (on task 5 also
  the component characteristics),
- `work/`, empty, for its delivery,

and the Python environment that runs `commission.py` at `/project/.venv`.
OpenModelica with the Modelica Standard Library and the network are
available. Besides the system directories, the sandbox shows only, read-only,
the library directory `~/.openmodelica`, the directory of the harness's
program and the base installation of the Python environment. The test and
variant data, the reference model, this repository and the rest of your home
directory are not there. Its prompt is the framing instruction in `frame.md`, the text
printed in the appendix of the paper. Each run is a single attempt, with no
feedback during the run.

## Requirements

- Linux with [bubblewrap](https://github.com/containers/bubblewrap). Ubuntu
  24.04 blocks the user namespaces that bubblewrap needs; `apparmor-bwrap` is
  a profile that allows them for bubblewrap alone, with the instructions to
  install it at its top.
- OpenModelica with the Modelica Standard Library 4.1.0, as for the
  acceptance.
- A Python environment with numpy, scipy and OMPython. Run `commission.py`
  with it; the agent gets the same environment.
- The harness, installed and signed in:

| Harness | `--harness` | Sign-in | Reasoning setting |
|---|---|---|---|
| Claude Code | `claude` | `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) or `ANTHROPIC_API_KEY` | `--effort max` |
| Codex | `codex` | `OPENAI_API_KEY` or `codex login` | `model_reasoning_effort = "max"` |
| OpenCode | `opencode` | `opencode auth login`, or a provider of your own (below) | the provider's default; `--effort` sets a variant |

Only the sign-in of the chosen harness enters the sandbox.

## Options

| Option | Effect |
|---|---|
| `--criterion` | adds an acceptance criterion to the brief: the residual gate and the instruction to compare against it, repair and report a shortfall (`criterion.md`); only for tasks graded by the residual gate |
| `--effort` | another reasoning setting than the default above |
| `--timeout` | stops the agent after so many seconds; by default it runs until it ends |
| `--out` | where the run directories go, `runs/` by default |
| `--dry-run` | builds the same sandbox and checks, instead of starting the agent, that everything the agent needs is there |
| `--bind-ro PATH` | shows a further directory read-only, for a harness installed in an unusual place |
| `--opencode-config FILE` | an OpenCode configuration, for a provider of your own |

## An open-weight LLM on your own machine

OpenCode can drive any server with an OpenAI-compatible interface, such as
llama.cpp or vLLM serving Qwen3.8 (27.8 B). A configuration file names it:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "local/qwen3.8-27b",
  "provider": {
    "local": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "local server",
      "options": { "baseURL": "http://localhost:8080/v1" },
      "models": { "qwen3.8-27b": { "limit": { "context": 262144, "output": 32000 } } }
    }
  }
}
```

```
python src/commission.py experiments/task1 --harness opencode \
    --model local/qwen3.8-27b --opencode-config local.json
```

The sandbox shares the network of the machine, so the agent reaches the
server at `localhost`.

## What a run leaves

```
runs/<task>_<harness>_<model>_<time>/
  task/            the working directory; the delivery is in task/work/
  agent/           the agent's home for this run, with its transcript
  commission.json  what was started, with which versions, and how it ended
  stdout.log, stderr.log
```

`commission.py` copies no credentials into the run directory. The
transcript in `agent/` holds everything the agent read and wrote, so look
through it before you pass a run on.

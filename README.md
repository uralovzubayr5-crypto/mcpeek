# MCPeek

Audit the tool surface of a [Model Context Protocol](https://modelcontextprotocol.io) server.

MCPeek connects to a server over stdio, lists its tools, and flags the patterns that
turn into real incidents: descriptions that invite instruction override, unbounded string
parameters, high-impact verbs (`exec`, `shell`, `delete`) with no validation hints, and
tool-name collisions. It also diffs two server versions so a silent tool change cannot
slip into a deployment.

Built by [Zubayr Uralov](https://github.com/uralovzubayr5-crypto).

## Why

An MCP server *is* its tool descriptions: the model trusts whatever the description
says. A tool called `read_file` with a free-text `path` and a page of "always do X"
prose is a prompt-injection delivery mechanism. MCPeek makes that surface reviewable
in CI.

## Install

```sh
git clone https://github.com/uralovzubayr5-crypto/mcpeek
cd mcpeek
pip install -e .
```

## Usage

```sh
# audit a local stdio server
mcpeek audit -- python examples/mock_server.py

# write a markdown report for the PR
mcpeek audit --json -- python examples/mock_server.py > audit.json

# diff two versions of a server (catches tool renames / sneaky new params)
mcpeek diff old.json new.json
```

## Checks

| check | why it matters |
|---|---|
| unbounded string param | free-text input into a file/exec sink |
| high-impact param name | `path`, `cmd`, `query`, `url`, `delete…` need validation notes |
| unsafe description | "ignore", "always", "do not tell the user" → instruction override bait |
| duplicate tool name | client resolves to the wrong tool |
| missing `inputSchema` | nothing for the client to validate |

## Mock server

`examples/mock_server.py` is intentionally sloppy: it exposes a `run_shell` tool with an
unbounded `cmd` parameter and a chatty description. Point MCPeek at it in a training lab:

```
$ mcpeek audit -- python examples/mock_server.py
tool        findings
run_shell   3 findings
            - unbounded string param: cmd
            - high-impact param: cmd
            - description invites instruction override
read_file   1 finding
            - unbounded string param: path
```

## Ethics

Only audit servers you operate or have permission to test. The mock server is there so
you can practise safely.

## License

MIT

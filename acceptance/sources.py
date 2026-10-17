"""Source audit: where the signals that drive physical sources come from.

A source driven by a signal, such as a signal voltage, a torque source or a
force source, turns a signal into a physical flow. Every connection of such a
model conserves energy, but the model as a whole conserves it only when the
signal comes from outside: from the model input, a constant or a function of
time. A source driven from inside, by a sensor or by a physical variable of
the model, can create or destroy energy, and only a power balance over the
parts it couples can show whether it does. The audit lists every such source,
so that a reader knows where a balance is needed. It gives no verdict.

The audit reads the model through the compiler's interface (instance tree,
connections, modifiers, equations), not through patterns on the source text,
so that type names come fully qualified. An element is audited when it is an
instance of a library type outside Modelica.Blocks with at least one signal
input and at least one physical connector, such as a pin or a flange. Each of
its signal inputs is traced backwards:

* connections between signal ports, equations of the form x = expression,
  modifier bindings such as force(f = u) and declaration bindings are the
  edges;
* a block of Modelica.Blocks passes all its inputs on to its outputs, and the
  blocks of Modelica.Blocks.Sources are leaves (Constant: constant,
  RealExpression: its expression, any other: time);
* the leaves are the model input, constants (parameters, constants), time,
  sensors (an output of a library element outside Modelica.Blocks), physical
  variables (a variable of a physical library element used in an equation)
  and open ends (no driver, an implicit equation or an unknown name).

Each signal input falls into one category:

    input        only the model input, through connections, linear blocks
                 with constant factors and equations linear in one variable
    processed    the model input together with constants or time, or through
                 other blocks such as filters, tables or limiters
    independent  only constants and time
    inside       at least one sensor or physical variable: driven from inside
    open         at least one open end and no sensor or physical variable

Sources in the categories inside and open need a reading; those driven from
inside need a power balance over the parts they couple.

    python -m acceptance.sources experiments/task4 path/to/model.mo
"""
from __future__ import annotations

import re
import sys

from .bench import Bench, BenchError, load_task

BUILTIN = {"Real", "Integer", "Boolean", "String"}

LINEAR_BLOCKS = {
    "Modelica.Blocks.Math.Gain", "Modelica.Blocks.Math.Add", "Modelica.Blocks.Math.Add3",
    "Modelica.Blocks.Math.Feedback", "Modelica.Blocks.Math.Sum", "Modelica.Blocks.Math.MultiSum",
    "Modelica.Blocks.Math.MatrixGain", "Modelica.Blocks.Routing.RealPassThrough",
    "Modelica.Blocks.Routing.Replicator",
}
"""Blocks that pass the input on with constant factors only."""

KEYWORDS = {
    "der", "pre", "sin", "cos", "tan", "exp", "log", "log10", "sqrt", "abs", "sign", "max", "min",
    "smooth", "noEvent", "tanh", "sinh", "cosh", "atan", "atan2", "asin", "acos", "floor", "ceil",
    "integer", "homotopy", "if", "then", "else", "elseif", "and", "or", "not", "true", "false",
    "semiLinear", "delay", "initial", "terminal", "sample", "edge", "change", "reinit", "assert",
    "sum", "product", "size", "zeros", "ones", "fill", "cat", "transpose", "vector", "scalar",
    "mod", "rem", "div", "interval", "Integer", "Real", "end",
}
"""Built-in functions and keywords, which are not variables."""

CATEGORIES = ("input", "processed", "independent", "inside", "open")
MAX_DEPTH = 12        # nesting of delivered classes
MAX_TRACE = 60        # steps of a backward trace


def parse_om(text: str):
    """Parse a value returned by the compiler: {...} lists, "..." strings, atoms.

    The compiler's own parser in OMPython fails on some equation texts, so the
    audit reads the raw replies.
    """
    s, pos = text.strip(), 0

    def skip():
        nonlocal pos
        while pos < len(s) and s[pos] in " \t\r\n":
            pos += 1

    def value():
        nonlocal pos
        skip()
        if pos >= len(s):
            return None
        if s[pos] == "{":
            pos += 1
            items = []
            skip()
            if pos < len(s) and s[pos] == "}":
                pos += 1
                return items
            while True:
                items.append(value())
                skip()
                if pos < len(s) and s[pos] == ",":
                    pos += 1
                    continue
                if pos < len(s) and s[pos] == "}":
                    pos += 1
                    return items
                raise ValueError(f"cannot read compiler reply at {pos}: {s[pos:pos + 40]!r}")
        if s[pos] == '"':
            pos += 1
            chars = []
            while pos < len(s):
                if s[pos] == "\\" and pos + 1 < len(s):
                    chars.append(s[pos + 1])
                    pos += 2
                    continue
                if s[pos] == '"':
                    pos += 1
                    return "".join(chars)
                chars.append(s[pos])
                pos += 1
            raise ValueError("unterminated string in compiler reply")
        start, depth = pos, 0
        while pos < len(s) and (depth > 0 or s[pos] not in ",}"):
            if s[pos] in "([":
                depth += 1
            elif s[pos] in ")]":
                depth -= 1
            pos += 1
        return s[start:pos].strip()

    return value()


def is_delivered(typ: str) -> bool:
    """A class of the delivery rather than of the library or the language."""
    return not (typ.startswith("Modelica.") or typ in BUILTIN
                or typ.startswith("ModelicaServices") or typ.startswith("Complex"))


class Compiler:
    """Cached queries to the compiler session of a bench."""

    def __init__(self, omc):
        self.omc = omc
        self._restriction, self._ports, self._library_components = {}, {}, {}

    def value(self, expression: str):
        return parse_om(self.omc.sendExpression(expression, parsed=False))

    def restriction(self, typ: str) -> str:
        if typ in BUILTIN:
            return "builtin"
        if typ not in self._restriction:
            try:
                self._restriction[typ] = self.value(f"getClassRestriction({typ})") or "?"
            except Exception:
                self._restriction[typ] = "?"
        return self._restriction[typ]

    def components(self, cls: str) -> list[tuple]:
        """(type, name, variability, dimensions) of the components declared in a class."""
        found = []
        for c in self.value(f"getComponents({cls})") or ():
            if isinstance(c, list) and len(c) >= 9:
                found.append((c[0], c[1], c[8], c[11] if len(c) > 11 else []))
        return found

    def bases(self, cls: str) -> list[str]:
        count = int(self.value(f"getInheritanceCount({cls})") or 0)
        return [self.value(f"getNthInheritedClass({cls}, {k})") for k in range(1, count + 1)]

    def library_components(self, typ: str) -> list[tuple]:
        """All components of a library type, inherited ones included."""
        if typ not in self._library_components:
            found = []
            try:
                found += self.components(typ)
                for base in self.bases(typ):
                    if base:
                        found += self.library_components(base)
            except Exception:
                pass
            self._library_components[typ] = found
        return self._library_components[typ]

    def ports(self, typ: str) -> tuple[list, list, list]:
        """Signal inputs, signal outputs and physical connectors of a type."""
        if typ not in self._ports:
            inputs, outputs, physical = [], [], []
            for t, name, _, _ in self.library_components(typ):
                if t.endswith(("RealInput", "IntegerInput", "BooleanInput")):
                    inputs.append(name)
                elif t.endswith(("RealOutput", "IntegerOutput", "BooleanOutput")):
                    outputs.append(name)
                elif (self.restriction(t) in ("connector", "expandable connector")
                      and not t.startswith("Modelica.Blocks")):
                    physical.append(name)
            self._ports[typ] = (inputs, outputs, physical)
        return self._ports[typ]


def split_statements(text: str) -> list[str]:
    """An equation section as statements; if, for and when blocks stay whole."""
    t = re.sub(r"//[^\n]*", "", text)
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r'"(?:[^"\\]|\\.)*"', '""', t)
    statements, buffer, level = [], [], 0
    for piece in t.split(";"):
        st = piece.strip()
        if not st:
            continue
        if re.match(r"(if|for|when)\b", st):
            level += 1
        buffer.append(st + ";")
        if re.match(r"end\s+(if|for|when)\b", st):
            level -= 1
        if level <= 0:
            statements.append("\n".join(buffer))
            buffer, level = [], 0
    if buffer:
        statements.append("\n".join(buffer))
    return statements


class Network:
    """Instance tree, connections, bindings and equations of the model class."""

    def __init__(self, compiler: Compiler, top: str):
        self.compiler = compiler
        self.instances = {}    # path -> dict(type, delivered, restriction)
        self.variables = {}    # path -> variability of a variable
        self.signal_ports = {}  # path -> "in" or "out", for RealInput/RealOutput in delivered classes
        self.connections = []  # (a, b, scope)
        self.equations = []    # (text, scope, class)
        self.bindings = []     # (target, expression, scope)
        self.scope_names = {}  # scope -> names visible in it
        self.expand(top, "")

    def expand(self, cls: str, prefix: str, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            return
        c = self.compiler
        names = self.scope_names.setdefault(prefix, set())
        for base in c.bases(cls):
            if not base:
                continue
            if is_delivered(base):
                self.expand(base, prefix, depth + 1)
            elif not base.startswith("Modelica.Icons"):
                # the components of a library base class are visible in the scope
                for typ, name, _, _ in c.library_components(base):
                    names.add(name)
                    self.variables.setdefault(prefix + name, "libbase:" + typ)
        for typ, name, variability, _ in c.components(cls):
            path = prefix + name
            names.add(name)
            restriction = c.restriction(typ)
            if typ.endswith("RealInput") or typ.endswith("RealOutput"):
                self.signal_ports[path] = "in" if typ.endswith("Input") else "out"
            elif restriction in ("model", "block", "class"):
                delivered = is_delivered(typ)
                self.instances[path] = dict(type=typ, delivered=delivered, restriction=restriction)
                if delivered:
                    self.expand(typ, path + ".", depth + 1)
            elif restriction in ("connector", "expandable connector"):
                self.instances[path] = dict(type=typ, delivered=is_delivered(typ),
                                            restriction=restriction)
            else:
                self.variables[path] = variability
            try:
                modifiers = c.value(f'getComponentModifierNames({cls}, "{name}")') or []
            except Exception:
                modifiers = []
            for m in modifiers:
                try:
                    v = c.value(f"getComponentModifierValue({cls}, {name}.{m})")
                except Exception:
                    v = None
                if v not in (None, ""):
                    self.bindings.append((path + "." + m, v, prefix))
            if restriction in ("type", "builtin", "record") or typ.startswith("Modelica.Units"):
                try:
                    v = c.value(f"getComponentModifierValue({cls}, {name})")
                except Exception:
                    v = None
                if v not in (None, ""):
                    self.bindings.append((path, v, prefix))
        for k in range(1, int(c.value(f"getConnectionCount({cls})") or 0) + 1):
            a, b = c.value(f"getNthConnection({cls}, {k})")[:2]
            self.connections.append((prefix + a, prefix + b, prefix))
        # Whole equation sections: single equation items come back empty after
        # a comment.
        for k in range(1, int(c.value(f"getEquationCount({cls})") or 0) + 1):
            section = c.value(f"getNthEquation({cls}, {k})") or ""
            for e in split_statements(section):
                if not re.match(r"\s*connect\s*\(", e):
                    self.equations.append((e, prefix, cls))

    def classify(self, path: str) -> tuple[str, object]:
        """What a path names: a signal port, a variable, a library instance or a part of one."""
        p = re.sub(r"\[[^\]]*\]", "", path)
        if p in self.signal_ports:
            return "port_" + self.signal_ports[p], None
        if p in self.variables:
            v = self.variables[p]
            return ("constant", None) if v in ("parameter", "constant") else ("variable", v)
        if p in self.instances and not self.instances[p]["delivered"]:
            return "library_instance", self.instances[p]["type"]
        parts = p.split(".")
        for k in range(len(parts) - 1, 0, -1):
            head = ".".join(parts[:k])
            if head in self.instances and not self.instances[head]["delivered"]:
                typ = self.instances[head]["type"]
                inputs, outputs, _ = self.compiler.ports(typ)
                sub = parts[k]
                if k == len(parts) - 1 and sub in inputs:
                    return "library_input", (head, typ, sub)
                if k == len(parts) - 1 and sub in outputs:
                    return "library_output", (head, typ, sub)
                for _, name, variability, _ in self.compiler.library_components(typ):
                    if name == sub and variability in ("parameter", "constant"):
                        return "constant", None
                return "library_variable", (head, typ, ".".join(parts[k:]))
        return "unknown", None

    def references(self, expression: str, scope: str) -> tuple[list, list, bool]:
        """Variables an expression refers to, resolved in a scope; unknown names; use of time."""
        e = re.sub(r'"(?:[^"\\]|\\.)*"', "", expression)
        found, unknown, uses_time = [], [], False
        for m in re.finditer(r"(?<![\w.])([A-Za-z_]\w*(?:\[[^\]]*\])?"
                             r"(?:\.[A-Za-z_]\w*(?:\[[^\]]*\])?)*)(\s*\()?", e):
            name, call = m.group(1), m.group(2)
            base = re.sub(r"\[[^\]]*\]", "", name)
            first = base.split(".")[0]
            if call:
                continue        # a function call; its arguments are found on their own
            if base == "time":
                uses_time = True
                continue
            if base in KEYWORDS or re.match(r"^[0-9]", base):
                continue
            if first in self.scope_names.get(scope, set()):
                found.append(scope + name)
            elif first in ("Modelica", "SI", "pi", "Constants", "e_", "g_n") or base.startswith("Modelica."):
                continue
            else:
                unknown.append(base)
        return found, unknown, uses_time


SINGLE = re.compile(r"^\s*(-?)\s*\(?\s*([A-Za-z_]\w*(?:\[[^\]]*\])?"
                    r"(?:\.[A-Za-z_]\w*(?:\[[^\]]*\])?)*)\s*\)?\s*$")


def _plain(path: str) -> str:
    return re.sub(r"\[[^\]]*\]", "", path)


def _split_equation(text: str) -> tuple[str, str] | None:
    e = text.strip().rstrip(";").strip()
    e = re.sub(r'\s*"(?:[^"\\]|\\.)*"\s*$', "", e)
    depth = 0
    for k, ch in enumerate(e):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "=" and depth == 0 and e[k - 1:k] not in ("<", ">", "=", ":") and e[k + 1:k + 2] != "=":
            return e[:k], e[k + 1:]
    return None


class SignalGraph:
    """Which variable is driven by what: aliases, definitions and implicit uses."""

    def __init__(self, net: Network):
        self.net = net
        self.parent = {}
        self.definitions = {}  # node -> [(references, unknown, uses_time, text)]
        self.implicit = {}     # node -> [text]
        for a, b, _ in net.connections:
            self.union(_plain(a), _plain(b))
        for target, expression, scope in net.bindings:
            if net.classify(target)[0] == "constant":
                continue
            self.define(_plain(target), expression, scope, f"binding {target} = {expression}")
        for text, scope, _ in net.equations:
            self._equation(text.strip(), scope)

    def _equation(self, t: str, scope: str) -> None:
        net = self.net
        parts = None if re.match(r"(if|for|when)\b", t) else _split_equation(t)
        if parts is None:
            self._implicit(t, scope)
            return
        lhs, rhs = parts
        dl = re.match(r"^\s*der\s*\(\s*([\w.\[\]]+)\s*\)\s*$", lhs)
        dr = re.match(r"^\s*der\s*\(\s*([\w.\[\]]+)\s*\)\s*$", rhs)
        if dl or dr:
            x, other = (dl.group(1), rhs) if dl else (dr.group(1), lhs)
            rx, _, _ = net.references(x, scope)
            if rx:
                self.define(_plain(rx[0]), "der_integral(" + other + ")", scope, t)
                return
        ml, mr = SINGLE.match(lhs), SINGLE.match(rhs)
        if (ml and mr and ml.group(2) not in KEYWORDS and mr.group(2) not in KEYWORDS
                and ml.group(2) != "time" and mr.group(2) != "time"):
            rl, _, _ = net.references(ml.group(2), scope)
            rr, _, _ = net.references(mr.group(2), scope)
            if rl and rr:
                self.union(_plain(rl[0]), _plain(rr[0]))
                return
        if ml and ml.group(2) not in KEYWORDS:
            rl, _, _ = net.references(ml.group(2), scope)
            if rl:
                self.define(_plain(rl[0]), rhs, scope, t)
                return
        if mr and mr.group(2) not in KEYWORDS:
            rr, _, _ = net.references(mr.group(2), scope)
            if rr:
                self.define(_plain(rr[0]), lhs, scope, t)
                return
        self._implicit(t, scope)

    def _implicit(self, text: str, scope: str) -> None:
        for r in self.net.references(text, scope)[0]:
            self.implicit.setdefault(_plain(r), []).append(text)

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def define(self, node: str, expression: str, scope: str, text: str) -> None:
        refs, unknown, uses_time = self.net.references(expression, scope)
        self.definitions.setdefault(node, []).append(([_plain(r) for r in refs], unknown, uses_time, text))
        self.find(node)

    def members(self, node: str) -> list[str]:
        root = self.find(node)
        return sorted(k for k in list(self.parent) if self.find(k) == root) or [node]

    def trace(self, start: str, model_input: str = "u") -> dict:
        """Follow one signal input backwards to its leaves and categorise it."""
        net = self.net
        leaves, blocks, steps, visited = [], [], [], set()
        nonlinear = False

        def follow_definition(m, refs, unknown, uses_time, text, depth, label):
            nonlocal nonlinear
            steps.append(f"{label}: {text}")
            if unknown:
                leaves.append(("open", m, f"unknown names {unknown} in: {text}"))
            if uses_time:
                leaves.append(("time", m, text))
            live = [r for r in refs if net.classify(r)[0] != "constant"]
            if not live and not uses_time and not unknown:
                leaves.append(("constant", m, text))
            return live

        def visit(node, depth):
            nonlocal nonlinear
            node = _plain(node)
            root = self.find(node)
            if root in visited or depth > MAX_TRACE:
                return
            visited.add(root)
            members = self.members(node)
            drivers = []
            for m in members:
                kind, info = net.classify(m)
                if m == model_input and kind == "port_in":
                    drivers.append(("input", m, None))
                elif kind == "library_output":
                    drivers.append(("library_output", m, info))
                elif kind == "library_variable":
                    drivers.append(("physical", m, info))
                elif kind == "constant":
                    drivers.append(("constant", m, None))
                for d in self.definitions.get(m, ()):
                    drivers.append(("definition", m, d))
            if (not drivers and depth > 0 and len(members) == 1 and not self.implicit.get(node)
                    and net.classify(node)[0] == "library_input"
                    and net.classify(node)[1][1].startswith("Modelica.Blocks")):
                # An unconnected block input can only be a disabled conditional
                # input in a model that translates.
                steps.append("unconnected, taken as a disabled conditional input: " + node)
                return
            if not drivers:
                uses = [t for m in members for t in self.implicit.get(m, [])]
                leaves.append(("open", node, "no driver" + ("; implicit in: " + " | ".join(uses) if uses else "")))
                return
            if len([d for d in drivers if d[0] != "constant"]) > 1:
                steps.append(f"several drivers for {node}: {[(d[0], d[1]) for d in drivers]}")
            for kind, m, info in drivers:
                if kind in ("input", "constant"):
                    leaves.append((kind, m, None))
                elif kind == "physical":
                    leaves.append(("physical", m, f"{info[2]} in {info[1]}"))
                elif kind == "definition":
                    refs, unknown, uses_time, text = info
                    live = follow_definition(m, refs, unknown, uses_time, text, depth, "equation")
                    if len(live) > 1 or re.search(r"[A-Za-z_]\w*\s*\(", text.split("=", 1)[-1]):
                        nonlinear = True
                    for r in live:
                        visit(r, depth + 1)
                elif kind == "library_output":
                    head, typ, _ = info
                    if typ.startswith("Modelica.Blocks.Sources."):
                        short = typ.split(".")[-1]
                        if short == "Constant":
                            leaves.append(("constant", m, typ))
                        elif short == "RealExpression":
                            blocks.append(typ)
                            if head + ".y" in self.definitions:
                                for refs, unknown, uses_time, text in self.definitions[head + ".y"]:
                                    for r in follow_definition(m, refs, unknown, uses_time, text,
                                                               depth, "RealExpression"):
                                        visit(r, depth + 1)
                            else:
                                leaves.append(("constant", m, "RealExpression without y"))
                        else:
                            leaves.append(("time", m, typ))
                    elif typ.startswith("Modelica.Blocks."):
                        blocks.append(typ)
                        inputs, _, _ = net.compiler.ports(typ)
                        if not inputs:
                            leaves.append(("time", m, typ + " without input"))
                        for p in inputs:
                            visit(head + "." + p, depth + 1)
                    else:
                        leaves.append(("sensor", m, typ))

        visit(start, 0)
        kinds = {leaf[0] for leaf in leaves}
        if kinds & {"sensor", "physical"}:
            category = "inside"
        elif "open" in kinds or not kinds:
            category = "open"
        elif kinds == {"input"} and all(b in LINEAR_BLOCKS for b in blocks) and not nonlinear:
            category = "input"
        elif "input" in kinds:
            category = "processed"
        else:
            category = "independent"
        return {"category": category, "leaves": leaves, "blocks": blocks, "steps": steps}


def audit(bench: Bench) -> list[dict]:
    """Every signal input of a physical library element, with its category."""
    compiler = Compiler(bench.omc)
    net = Network(compiler, bench.model_class)
    graph = SignalGraph(net)
    found = []
    for path, instance in sorted(net.instances.items()):
        if instance["delivered"] or instance["type"].startswith("Modelica.Blocks"):
            continue
        inputs, _, physical = compiler.ports(instance["type"])
        if not inputs or not physical:
            continue
        for port in inputs:
            found.append({"element": path, "type": instance["type"], "input": port,
                          **graph.trace(path + "." + port, bench.task.input)})
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    task = load_task(argv[0])
    try:
        with Bench(argv[1], task) as bench:
            elements = audit(bench)
    except BenchError as e:
        print(f"cannot read the delivery ({e})", file=sys.stderr)
        return 1
    if not elements:
        print("no physical source is driven by a signal")
    for e in elements:
        print(f"{e['element']}.{e['input']:<12} {e['type'].removeprefix('Modelica.'):<45} {e['category']}")
        if e["category"] in ("inside", "open"):
            for kind, where, detail in e["leaves"]:
                if kind in ("sensor", "physical", "open"):
                    print(f"    {kind}: {where}" + (f" ({detail})" if detail else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

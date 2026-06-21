# Why I Built UCI

*by Leon Priest*

---

## The Problem Became Obvious

After building enough systems — runtimes, desktop apps, local AI tools, automation pipelines, service layers — a pattern becomes impossible to ignore.

Every time an AI agent needs to interact with software, someone reinvents the same wheel. A custom integration. A one-off wrapper. A bespoke handshake between the agent and the thing it needs to call. Works fine for that project. Falls apart the next time.

I didn't set out to build a protocol. I set out to stop doing the same work over and over. UCI became inevitable — the same way standard connectors became inevitable once you've untangled enough incompatible cables.

The question was never *whether* a standardised interface for AI agent capability invocation would exist. It was whether it would be built carefully or carelessly.

---

## What Was Missing

The existing approaches solve the easy problem — getting an AI agent to call a function. That part works.

What they don't solve is everything that happens around that call:

- Who authorised it?
- What was the risk level?
- Did anything unexpected happen?
- Can you prove what the agent did, and when?
- If something goes wrong, who is accountable?

These aren't edge cases. These are the questions every serious deployment eventually has to answer. Most existing approaches leave them entirely to the implementer — meaning they either get answered inconsistently, or not at all.

I wanted governance built in from day one. Not bolted on later. Not left as an exercise for the reader.

---

## Why Governance Matters

The world is a dangerous place. What you don't see happening may hurt you more than what you do.

That's not paranoia — it's operational reality. Silent failures. Unintended side effects. An agent calling a destructive action because nothing was in place to require confirmation. A sequence of low-risk-looking calls that adds up to something nobody intended.

The answer isn't to distrust AI agents. The answer is to build systems where the user always stays in control, and every execution is precise and intentional.

UCI is designed around that principle at every level:

- **Fail-closed by default.** If a capability isn't explicitly permitted, it doesn't run.
- **Risk is explicit.** Every action carries a declared risk level. High-risk actions require confirmation before they execute.
- **Audit is not optional.** Every invocation is recorded in a tamper-evident, chain-hashed log. Not for compliance theatre — because accountability matters.
- **Trust is earned, not assumed.** Nodes move through explicit trust states. Unknown. Discovered. Verified. Trusted. Restricted. Revoked. Each transition is deliberate.

These aren't features added for enterprise sales decks. They are the foundation. Everything else is built on top of them.

---

## Why Scout Exists

One of the biggest friction points in adopting any protocol is the blank page problem. You know you want to integrate — but where do you start? What does your existing codebase even expose? How do you map twenty services worth of routes, functions, and CLI commands into a governed capability manifest?

UCI Scout exists to remove that friction entirely.

Point it at any Python project. It reads the source — never executes it, never imports it, never touches a running process. Pure static analysis. It finds every HTTP route, every CLI command, every public function and service method, scores how naturally they map to UCI, and generates a ready-to-edit manifest scaffold.

The first time you run Scout against a codebase you've been working on for months and see it mapped out as UCI capabilities with inferred risk levels and execution modes — that's when the protocol stops being abstract and starts being real.

That moment was the design goal.

---

## Where This Goes

UCI is at v0.1. There is a lot of road ahead.

What I'm building toward is straightforward: UCI becomes the standard interface layer for AI agents interacting with software — for power users running local agent systems, for teams deploying governed internal platforms, for enterprise environments where audit and compliance aren't optional, and for individual developers who just want their tools to be callable by agents without giving up control.

The protocol is open. Apache 2.0. Independent. Not tied to any model provider, any cloud, any ecosystem. That's intentional. A standard that belongs to one company isn't really a standard.

If you're building agentic systems and you've felt the friction of doing governance, audit, and risk management from scratch every time — UCI is built for you.

If you want to see what it would look like for your existing Python project to be agent-ready — run Scout against it. The answer takes about thirty seconds.

---

*Leon Priest*
*github.com/7h3v01d*
*UCI Protocol v0.1 — Apache 2.0*

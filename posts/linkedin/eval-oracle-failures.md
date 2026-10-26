Your agent eval has bugs. Nobody is testing it.

The pattern: a team wires a public benchmark into its own pipeline. Scores look great. Then production comes in lower and everyone blames the model, the prompt, the data.

Almost nobody asks whether the grader was right.

A paper from Nanjing University of Science and Technology (October 2026) audited exactly this. The author plugged tau-bench, a tool-use benchmark, into a custom harness and ran 4,320 episodes. The benchmark's reward function resets the database to compute a ground-truth hash and never restores it. The benchmark's own runner is unaffected, because it never reads that state again. The author's harness did: it scored each episode after the session ended, so it read the reference solution's state instead of the agent's.

Result: 4,194 archived passes. Replay the recorded tool calls on a clean database and 2,883 survive. Measured success drops from 94.3% to 65.5%.

Same agent. Same tasks. Same tool calls. The only thing that changed was whether the grader was telling the truth.

What caught it was not a better model. It was five state invariants and three known-answer controls (grading must not change state, the reference solution must pass, an episode that does nothing must fail) run as tests against the grader. They flagged all seven defect classes the author injected.

Bugs like this do not announce themselves. They inflate a number everyone wants to believe.

*Take twenty passing runs from your last eval. Replay the logged tool calls on a clean environment and grade them again. How many still pass?*

If you have never done this, your success rate is a hypothesis.

What it doesn't prove: one benchmark, two task domains, one model provider. The bug lived in the author's integration, not in tau-bench's own runner. Simulated users, not people.

How many of your eval passes have you ever replayed?

Paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #AIEvaluation #AIAgents #MLOps

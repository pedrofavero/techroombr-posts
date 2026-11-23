Most multi-agent architectures I see in the field are org charts, not engineering decisions.

I see this in deployments all the time. One agent with tools handles the workflow well enough. Then the roadmap says "agentic". A planner gets added, then a router, then specialists. Token bill triples. Latency triples. Success moves two points, sometimes the wrong way.

Nobody asked the boring question first: are the first agent's skill and tool definitions any good?

A November 2026 paper from Amazon and the University of Washington ran the controlled test. Same model, same tasks, same tools, 13 enterprise-style SOPs, 2,124 tasks per arm. Four architectures, eight arms: single function-calling agent, skill-augmented agent, centralized orchestrator, triage swarm.

The single agent hit 67.4%. The coordinated designs spent 1.4 to 4.7 times the tokens and 2.6 to 5.8 times the latency for gains that were usually small, rarely significant. One multi-agent implementation lost to the single agent outright.

What moved the needle was the quality of the parts. Better skill definitions took the single agent to 73.1%. A redesigned orchestrator reached 75.6%, the only arm to beat the baseline significantly.

The architecture was never the lever. The implementation underneath was.

Before adding an agent, try this:

*Take your worst SOP. Rewrite the skill and tool definitions for the single agent only, then rerun the same eval. If that captures most of the gain, the orchestrator you were about to build is a cost, not a feature.*

What it doesn't prove: one benchmark with mock tools, one model family (the authors say so), and per-SOP success ranged from under 10% to near 100%, so averages hide a lot. Written at Amazon, so read the architecture advice with that in mind.

What is the most expensive agent you have seen added to a system that never needed it?

Paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #AIAgents #MultiAgentSystems #EnterpriseAI #LLM


Paper: https://arxiv.org/abs/2611.12953

The quality score on your agent dashboard is measuring your reviewers at least as much as your agent.

I see this in deployments all the time. A team ships a fix. The weekly human review score drops. Rollback talk, a late night reading transcripts. Then someone notices a stricter reviewer joined the rotation that week.

Nobody modeled the reviewers. The rubric was treated as ground truth. The people applying it were invisible.

A working paper by Liu Zhang and Mark Esposito (October 2026) puts numbers on this. They took 2,611 rubric-scored production interviews from a deployed voice-and-video interviewing agent, scored by overlapping human reviewers between March and August 2026.

Two reviewers scoring the same batches differed by 0.79 standard deviations on the composite index. When the reviewer mix changed, the raw trend went flat. After adjusting for who did the scoring and smoothing the batch estimates, evaluated reliability had risen by 0.53 standard deviations over the period. Interview-related support tickets fell about 10% a month relative to technical-issue tickets, which points the same way.

The agent was getting better. The measurement was hiding it.

So before your next review cycle, try this:

*Take ten transcripts your reviewers already scored this week. Have a second reviewer score them blind. If the gap between the two is bigger than the improvement you are trying to detect, your dashboard cannot see that improvement.*

What it doesn't prove: one agent, one company, three reviewers, and a preliminary working paper. The authors say the data do not identify a causal effect of evaluation on performance.

Has a reviewer change ever shown up on your dashboard as a model regression?

Paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #AIAgents #AIEvaluation #MLOps #HumanInTheLoop


Paper: https://arxiv.org/abs/2610.07003

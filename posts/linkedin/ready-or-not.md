Two agents scored 72.8% and 72.5% on the same enterprise task. To hit the reliability target, one needed humans to review 39% of its cases. The other, 30%.

That gap is from "READY or Not: Reliable Enterprise Agent Deployment" (Scale AI, with a co-author at Vanderbilt University Medical Center, September 2026). They ran 16 agent systems through 750 clinical-audit cases, 12,000 runs in total.

Finding 1: accuracy alone doesn't qualify an agent. READY asks: at a target reliability, which oversight policy is cheapest, and does it still hold on held-out data? The output is a "deployment profile": reliability with a confidence bound, human-review burden, operating cost, assumptions.

Finding 2: the oversight policy is a confidence threshold. The agent reports a confidence score; above it, accepted; below it, a human reviews. Tuned on 375 cases, frozen, then qualified on 375 held-out cases with a one-sided 95% lower bound.

Finding 3: at a 76% target, 15 of 16 systems qualify, with very different review rates. GPT-5.5 qualified at the lowest, 21.3%; Opus 5 at 22.4%. GLM-5.2 had the lowest rate of all (10.9%) and did not qualify. Gemini-3.1-Pro only qualified by sending 100% of cases to review.

In the field: this is the conversation I have with customers, and almost nobody prices it. The number that drives cost of ownership isn't accuracy, it's the review rate at the reliability the business will sign off on. Two models that look identical on a leaderboard can mean a 30% difference in human hours. So the acceptance criterion in the SOW should read "X% reliability at Y% review rate, qualified on held-out cases", not a benchmark score. And the agent's self-reported confidence becomes a production feature you have to monitor, because the whole policy rests on it.

What it doesn't prove: one workflow, one benchmark (CliniCARE-Bench), not live production. Every qualification assumes a 90% human-review success rate the paper doesn't measure. And Scale AI sells evaluation; read it with that in mind.

If you've deployed agents behind a confidence-gated review queue, did the threshold hold once real users showed up?

Paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #LLMAgents

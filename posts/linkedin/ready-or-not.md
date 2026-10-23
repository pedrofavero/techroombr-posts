Accuracy is the wrong number to put in the contract.

Two agents hit 72.8% and 72.5% on the same enterprise workflow. Practically identical. But to reach the reliability the business actually needed, one of them sent 39% of its cases to a human reviewer. The other, 30%.

That is a 30% difference in human hours, hiding behind a 0.3 point difference on the leaderboard.

The numbers come from "READY or Not", a September 2026 paper from Scale AI. They ran 16 agent systems through 750 clinical audit cases and asked a question I wish more buyers asked: not "how accurate is it?" but "at the reliability we need, how much oversight does it take, and does that hold on data it has never seen?"

Their answer is a confidence threshold. The agent scores its own confidence. Above the line, auto-accept. Below it, a human looks. Tune the line on half the cases, freeze it, qualify it on the other half with a 95% lower bound.

At a 76% target, 15 of the 16 systems qualified. The cheapest needed humans on 21% of cases. One only qualified by sending 100% of cases to review. Same benchmark, same target, completely different operating cost.

I see this in deployments all the time. The pilot gets approved on accuracy. The budget gets eaten by the review queue nobody modeled.

So before you sign off on an agent, try this:

*At the reliability we will actually accept, what percentage of cases will a human still have to touch, and who is paying for those hours?*

If nobody can answer, you don't have an evaluation yet. You have a demo.

What it doesn't prove: one workflow, one benchmark, not live production. The 90% human review success rate is assumed, not measured. And Scale AI sells evaluation. Read it with that in mind.

Have you ever had an agent's review rate blow up after launch?

Paper in the first comment.

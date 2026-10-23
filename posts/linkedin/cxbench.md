The agent closed the ticket. It also skipped a step the regulator requires.

That is the failure mode no dashboard shows. The task ends in the right state. The dispute got filed, the plan got changed, the refund went out. Green check. What the dashboard cannot see is that the required disclosure never happened, the customer never confirmed, or the steps ran in the wrong order.

In a bank, a telecom or an insurer, that is not a near miss. That is the violation.

A benchmark published this month puts a number on it. CXBench (University of Limerick, CUHK Shenzhen and others, with Genesys, October 2026) ran 7 models through 120 regulated customer-service tasks across banking, telecom, insurance, healthcare, utilities and government benefits. Each run was scored twice: did the final state come out right, and was the process compliant.

69% of runs got the outcome right. Only 13.8% got outcome and process right. Of the runs that passed on outcome, 80% had broken the process somewhere.

Two models tied on outcome at 77.5%. On outcome plus process, one scored 21.7% and the other 13.3%. Same leaderboard number, very different liability.

One more detail: when they handed a model the submit tool directly, instead of letting the runtime submit only after the customer confirmed, its compliant pass rate fell from 20.8% to 0.8%. Remove the checks tied to that rule and the gap almost vanishes (18.3% vs 20.8%). Call it a scoring artifact if you want. I read it as: the control that mattered lived in the workflow, not in the model.

So before you accept an agent for a regulated flow, try this:

*Pick ten runs that passed. Open the traces. Can you point to the exact lines where the disclosure, the consent and the confirmation happened, in that order?*

If you cannot, your acceptance test is measuring the wrong thing.

What it doesn't prove: synthetic business data, an LLM-simulated customer and an LLM judge (88% accuracy on calibration traces, not a held-out set). Six domains only. And a customer-experience vendor is a co-author. Read it with that in mind.

How are you testing process compliance today, or are you only checking the final state?

Paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #AIAgents #AIEvaluation #EnterpriseAI #Compliance

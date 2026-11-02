The prompt-injection detector you just bought was graded on a test it had already studied for.

The pattern: security asks for a guardrail before the agent ships. Someone picks the classifier with the best score on a public benchmark. It goes in front of the tool outputs. Everybody relaxes.

Nobody checks whether that score means anything for this agent and these tool outputs.

A paper from JAIST, "Passing the Test You Trained On" (October 2026), ran that check. The author replayed the ground-truth tool calls from AgentDojo and tau-bench with no LLM in the loop, so clean outputs were benign by construction, then ran 15 off-the-shelf detectors over them, Prompt Guard 2 included.

The detector that topped the BIPIA benchmark at 95% recall caught 2% of the AgentDojo injections at a 1% false-positive rate. Another caught 72% of injections on AgentDojo and 15% on tau-bench. Same detector, different agent. On benign tool outputs, false-positive rates ran from 0% to over 90%. A 90% false-positive rate is not a security control. It is an outage.

The explanation was the shape of the training data, not leaked attack strings. The BIPIA champion had been trained on BIPIA's own inputs. The detector whose public training data included injections planted inside tool responses held up on both agent benchmarks.

The leaderboard was never measuring your risk. It was measuring the detector's familiarity with the exam.

*Today, pull 500 benign tool outputs from your agent's logs and run them through your detector. How many does it block, and how many user tasks would that have killed?*

What it doesn't prove: both agent benchmarks are simulated, all attacks are static (adaptive attackers would hurt every detector), and it is a single-author preprint that skipped commercial API detectors.

Have you ever measured your guardrail's false-positive rate on your own traffic?

Paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #AIAgents #AISecurity #PromptInjection #LLM

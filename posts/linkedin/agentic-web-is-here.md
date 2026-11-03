Stop teaching your agent to click. Start asking who will let it in.

The pattern: a team demos a computer-use agent that logs into a supplier portal, scrolls, fills the form, submits. The demo lands. Then the portal ships a redesign, adds a CAPTCHA, or blocks the traffic. The agent goes blind on a Tuesday and nobody notices until Thursday.

I see this in deployments all the time. The agent was built for the web as it is, and the web is not standing still.

MIT Technology Review's "The agentic web is here" (Grace Huckins, November 2026) maps this well. Amazon blocked Meta's Muse agent soon after it launched in September. Resy reportedly blocked people using agents to book restaurants. The agents that ship run on connectors: Gmail, Instacart, a Stripe payment connector that keeps card numbers away from the model and asks a human before paying.

The research behind that split is a McGill and Mila position paper, "Build the web for agents, not agents for the web" (June 2025). On the browser route: DOM trees that can exceed 1 million tokens, and a rough estimate of 40 dollars for one 20-step task on GPT-4.1. Their proposal: an Agentic Web Interface the site owner designs for agents, standardized, safe, efficient to host.

Yes, screen agents keep improving. The article cites 73% on OSWorld 2.0 for OpenAI's GPT-6 Astra. Impressive, and still irrelevant the day the site decides you are a bot.

The agent was never the bottleneck. The permission to operate was.

*For the five sites your agent touches most, write down: is there an interface the owner sanctioned for agents? If not, what happens the day they block you?*

What it doesn't prove: the McGill paper is a position paper, no prototype, no empirical validation. The 73% is a benchmark, not production. The article is reporting, not a study.

Which site has already blocked one of your agents?

Article and paper in the first comment.

#ForwardDeployedEngineering #AIEngineering #AIAgents #AgenticWeb #ComputerUse #EnterpriseAI

from scheduled_agents import ScheduledAgents

sched_agents = ScheduledAgents()

print("Starting scheduled agents...")

# print("Running agent_crypto_sm_ws...")
# sched_agents.run_agent_crypto_sm_ws()

# print("Running agent_market_sm_ws...")
# sched_agents.run_agent_market_sm_ws()

print("Running agent_market_news_workflow...")
sched_agents.run_agent_market_news_workflow()

print("Running agent_crypto_news_ws...")
sched_agents.run_agent_crypto_news_ws()
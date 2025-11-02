from agents import IAgent


class AgentManager:
    def __init__(self):
        self._agents: dict[str, IAgent] = {}

    def register_agent(self, agent: IAgent):
        agent_name = agent.get_name()
        print(f"Registering agent: {agent_name}")
        self._agents[agent_name] = agent

    def dispatch(self, intent: dict) -> str:
        intent_type = intent.get("type")
        if not intent_type or intent_type == "unknown":
            return "I'm not sure what you mean."

        agent = self._agents.get(intent_type)
        if agent:
            return agent.execute(intent)

        print(f"WARNING: No agent registered for intent type '{intent_type}'")
        return "I'm not sure how to handle that request."

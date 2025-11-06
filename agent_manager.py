# agent_manager.py
import inspect
import logging
import pkgutil

from agents import IAgent

# Get a logger for this module
logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self._agents: dict[str, IAgent] = {}
        self.load_agents()

    def load_agents(self):
        """Dynamically discovers and registers all agent classes from the 'agents' package."""
        import agents
        logger.info("--- Discovering and loading agents ---")

        # The path to the 'agents' package
        package_path = agents.__path__

        for _, name, _ in pkgutil.iter_modules(package_path):
            # Skip the base_agent module
            if name == 'base_agent':
                continue

            try:
                # Import the module dynamically
                module = __import__(f"agents.{name}", fromlist=[""])

                # Find all classes in the module that are subclasses of IAgent
                for member_name, member_obj in inspect.getmembers(module):
                    if inspect.isclass(member_obj) and issubclass(member_obj, IAgent) and member_obj is not IAgent:
                        # Instantiate the agent and register it
                        agent_instance = member_obj()
                        self.register_agent(agent_instance)
            except Exception as e:
                logger.error(f"Failed to load agent from module '{name}': {e}", exc_info=True)

    def register_agent(self, agent: IAgent):
        agent_name = agent.get_name()
        if agent_name in self._agents:
            logger.warning(f"Agent '{agent_name}' is already registered. Overwriting.")
        logger.info(f"Registering agent: {agent_name}")
        self._agents[agent_name] = agent

    def dispatch(self, intent: dict) -> str:
        intent_type = intent.get("type")
        if not intent_type or intent_type == 'unknown':
            return "I'm not sure what you mean."

        agent = self._agents.get(intent_type)
        if agent:
            return agent.execute(intent)

        logger.warning(f"No agent registered for intent type '{intent_type}'")
        return "I'm not sure how to handle that request."

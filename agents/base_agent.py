from abc import ABC, abstractmethod


class IAgent(ABC):
    """Abstract base class defining the interface for all agents."""

    @abstractmethod
    def get_name(self) -> str:
        """Gets the unique name of the agent (e.g., 'calculation')."""
        pass

    @abstractmethod
    def execute(self, intent: dict) -> str:
        """
        Executes the action specified in the intent.
        :param intent: A dictionary containing details like action and parameters.
        :return: A string response for the user.
        """
        pass

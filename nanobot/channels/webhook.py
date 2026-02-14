"""Base channel for webhook-based integrations."""

from abc import abstractmethod
from typing import Any

from starlette.datastructures import Headers

from nanobot.channels.base import BaseChannel
from nanobot.bus.events import OutboundMessage


class WebhookChannel(BaseChannel):
    """
    Base class for channels that receive messages via webhooks.

    Subclasses should implement:
    - parse_webhook(): Parse incoming webhook data into message fields
    - send(): Send messages to the platform
    - start() / stop(): Manage webhook registration lifecycle
    """

    def __init__(self, config: Any, bus):
        """
        Initialize the webhook channel.

        Args:
            config: Channel-specific configuration.
            bus: The message bus for communication.
        """
        super().__init__(config, bus)
        self._webhook_enabled = getattr(config, "webhook_enabled", True)
        self._webhook_path = getattr(config, "webhook_path", None)

    @property
    def webhook_enabled(self) -> bool:
        """Check if webhook is enabled for this channel."""
        return self._webhook_enabled

    @property
    def webhook_path(self) -> str:
        """Get the webhook path for this channel.

        Returns:
            The configured webhook path, or default /webhook/{name}.
        """
        if self._webhook_path:
            return f"/webhook/${self._webhook_path}"
        return f"/webhook/{self.name}"
   
    @abstractmethod
    async def handle_webhook(self, header: Headers, data: dict[str, Any]) -> dict[str, Any]:
        """Handle incoming webhook data.

        This method parses the webhook data and forwards messages to the bus.

        Args:
            data: The incoming webhook data payload.

        Returns:
            A response dict to send back to the webhook caller.
        """
        pass

    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through this channel."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the channel and handle webhook registration."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the channel and clean up resources."""
        pass

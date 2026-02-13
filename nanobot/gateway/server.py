"""FastAPI server for nanobot gateway."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any

import asyncio
import uvicorn
from fastapi import FastAPI, Request
from loguru import logger

from nanobot.channels.base import BaseChannel
from nanobot.channels.webhook import WebhookChannel


class GatewayServer:
    """HTTP gateway server using FastAPI."""

    def __init__(
        self,
        config: Any,
        channels: dict[str, BaseChannel] | None = None,
        port: int = 18790,
        verbose: bool = False,

    ):
        """Initialize gateway server.

        Args:
            config: The nanobot config object.
            channels: Optional dict of channel instances for webhook registration.
            port: Port to listen on.
            verbose: Enable verbose logging.
        """
        self.config = config
        self.channels = channels or {}
        self._server = None  # uvicorn.Server instance
        self._dispatch_task: asyncio.Task | None = None
        self.port = port
        self.verbose = verbose
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Lifespan context manager for the app."""
            yield

        app = FastAPI(
            title="nanobot API",
            description="Personal AI Assistant API",
            version="0.1.0",
            lifespan=lifespan,
        )

        @app.get("/health")
        async def health_check() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "ok"}

        # Register webhook routes for channels that support it
        self._register_webhooks(app)

        return app

    def _register_webhooks(self, app: FastAPI) -> None:
        """Register webhook routes for WebhookChannel instances.

        Args:
            app: The FastAPI application instance.
        """
        for channel_name, channel in self.channels.items():
            if isinstance(channel, WebhookChannel) and channel.webhook_enabled:
                path = channel.webhook_path if channel.webhook_path is not None else channel_name

                path = f"/webhook/{path}"

                @app.post(path)
                async def webhook_handler(request: Request, ch=channel) -> dict[str, Any]:
                    """Handle incoming webhook requests."""
                    data = await request.json()
                    headers = request.headers
                    return await ch.handle_webhook(headers, data)

                logger.info(f"register webhook handler for channel: {channel_name}, webhook path: {path}")


    def stop(self) -> None:
        """Signal the server to stop."""
        if self._server:
            self._server.should_exit = True


    async def start_async(self) -> None:
        """Start the uvicorn server asynchronously."""
        config_instance = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info" if self.verbose else "warning",
        )
        self._server = uvicorn.Server(config_instance)
        await self._server.serve()
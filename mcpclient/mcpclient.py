"""
Run from the repository root:
    uv run examples/snippets/clients/streamable_basic.py
"""

import logging
import ssl
from typing import Any, Awaitable, Callable

import httpx
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP (Model Context Protocol) Client for interacting with MCP servers.

    This client provides a high-level interface for connecting to and interacting with
    MCP servers over HTTP. It supports authentication, TLS configuration, and provides
    methods for listing tools and executing scenarios.

    Example:
        Basic usage with self-signed certificates:
        >>> client = MCPClient("https://example.com", "your-api-key")
        >>> tools = await client.get_tools()

        With TLS verification enabled:
        >>> client = MCPClient("https://example.com", "your-api-key", verify_tls=True)
        >>> response = client.health_check()

        With category endpoint:
        >>> client = MCPClient("https://example.com", "your-api-key", category="job_management")
        >>> await client.run_a_scenario(my_scenario_func)

    Attributes:
        base_url (str): Base URL of the MCP server
        api_key (str): API key for authentication
        category (str | None): Optional category for MCP endpoint routing
        verify_tls (bool): Whether TLS certificate verification is enabled
        headers (dict): HTTP headers including authorization
    """

    def __init__(self, base_url: str, api_key: str, category: str | None = None, verify_tls: bool = False) -> None:
        """Initialize MCPLib client.

        Args:
            base_url: Base URL of the MCP server
            api_key: API key for authentication
            category: Optional category for MCP endpoint
            verify_tls: Whether to verify TLS certificates (default: False for self-signed certs)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.category = category
        self.verify_tls = verify_tls
        self.headers = {"Authorization": f"Bearer {api_key}"}


    def create_httpx_client_with_ssl(
        self,
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
        async_client: bool = True,
    ) -> httpx.AsyncClient | httpx.Client:
        """Create httpx client with configurable TLS verification.

        Args:
            headers: Optional HTTP headers to include in requests
            timeout: Optional timeout configuration
            auth: Optional authentication handler
            async_client: Whether to return AsyncClient (True) or sync Client (False)

        Returns:
            httpx.AsyncClient or httpx.Client depending on async_client parameter
        """
        # Create httpx client kwargs
        kwargs = {
            "follow_redirects": True,
        }

        # Configure TLS verification
        if not self.verify_tls:
            # Create SSL context that doesn't verify certificates (for self-signed certs)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            kwargs["verify"] = ssl_context
        # If verify_tls is True, use default verification (kwargs["verify"] not set)

        if timeout is None:
            kwargs["timeout"] = httpx.Timeout(30.0)
        else:
            kwargs["timeout"] = timeout

        if headers is not None:
            kwargs["headers"] = headers

        if auth is not None:
            kwargs["auth"] = auth

        return httpx.AsyncClient(**kwargs) if async_client else httpx.Client(**kwargs)


    def get_client(self) -> Any:
        """Get MCP streamable HTTP client."""
        return streamablehttp_client(
            f"{self.base_url}/{self.category}/mcp" if self.category else f"{self.base_url}/mcp",
            headers=self.headers,
            httpx_client_factory=self.create_httpx_client_with_ssl
        )


    def health_check(self) -> httpx.Response:
        """Check server health status."""
        with self.create_httpx_client_with_ssl(
            headers=self.headers,
            async_client=False,
        ) as client:
            response = client.get(f"{self.base_url}/api/v1/health")
            return response


    async def run_a_scenario(self, scenario_func: Callable[[ClientSession], Awaitable[Any]]) -> Any:
        """Run a custom scenario function with an initialized MCP session."""
        async with self.get_client() as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                logger.info("Running a scenario...")
                res = await scenario_func(session)
                logger.debug("Scenario result: %s", res)
                return res


    async def get_tools(self) -> list[types.Tool]:
        """Get available tools from the MCP server."""
        async def scenario_func(session: ClientSession):
            tools = await session.list_tools()
            logger.info("Available tools: %s", [tool.name for tool in tools.tools])
            return tools.tools
        return await self.run_a_scenario(scenario_func)

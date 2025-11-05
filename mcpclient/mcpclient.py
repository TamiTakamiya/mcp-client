"""
MCP Client Library - HTTP-based Model Context Protocol Client.

This module provides a high-level Python client for interacting with MCP
(Model Context Protocol) servers over HTTP. It supports both synchronous
and asynchronous operations, configurable TLS verification, and Bearer
token authentication.

Key Features:
    - Streamable HTTP transport for MCP communication
    - Bearer token authentication
    - Configurable TLS certificate verification
    - Category-based endpoint routing
    - Health check endpoint support
    - Custom scenario execution
    - Automatic HTTP connection cleanup

Example:
    Basic usage with async operations:
    >>> import asyncio
    >>> from mcpclient import MCPClient
    >>>
    >>> async def main():
    ...     client = MCPClient("https://server.com", "api-key")
    ...     tools = await client.get_tools()
    ...     print(f"Found {len(tools)} tools")
    >>>
    >>> asyncio.run(main())

Note:
    This library uses lazy client creation to prevent resource leaks.
    HTTP clients are created on-demand and automatically cleaned up.

Author: Tami Takamiya
Repository: https://github.com/TamiTakamiya/mcp-client
"""

import logging
import ssl
from typing import Any, Awaitable, Callable

import httpx
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client

# Configure module-level logger
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
        """Initialize MCP Client with server configuration.

        Creates a new MCPClient instance configured for the specified MCP server.
        The client uses lazy initialization - HTTP connections are created on-demand
        when methods are called, not during initialization.

        Args:
            base_url: Base URL of the MCP server (e.g., "https://example.com")
            api_key: API key for Bearer token authentication
            category: Optional category for endpoint routing (e.g., "job_management").
                     If provided, requests go to {base_url}/{category}/mcp
            verify_tls: Whether to verify TLS certificates. Set to False for
                       self-signed certificates (default), True for production

        Example:
            >>> # For development with self-signed certs
            >>> client = MCPClient("https://dev-server.com", "dev-key")
            >>>
            >>> # For production with valid certificates
            >>> client = MCPClient("https://prod.com", "key", verify_tls=True)
            >>>
            >>> # With category routing
            >>> client = MCPClient("https://server.com", "key", category="jobs")
        """
        # Store server configuration
        self.base_url = base_url
        self.api_key = api_key
        self.category = category
        self.verify_tls = verify_tls

        # Prepare authentication headers with Bearer token
        self.headers = {"Authorization": f"Bearer {api_key}"}


    def create_httpx_client_with_ssl(
        self,
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
        async_client: bool = True,
    ) -> httpx.AsyncClient | httpx.Client:
        """Create HTTP client with configurable TLS verification settings.

        This method creates an httpx HTTP client configured with the instance's
        TLS verification settings. It supports both async and synchronous clients
        and can be customized with headers, timeout, and authentication.

        When verify_tls is False (default), the client disables certificate
        verification and hostname checking, allowing connections to servers
        with self-signed certificates. When True, standard TLS verification
        is performed.

        Args:
            headers: Optional HTTP headers to include in requests. If None,
                    no custom headers are added (authentication headers should
                    be added separately)
            timeout: Optional timeout configuration. If None, defaults to
                    30 seconds for all operations
            auth: Optional authentication handler for httpx
            async_client: If True, returns AsyncClient for async operations.
                         If False, returns synchronous Client

        Returns:
            httpx.AsyncClient: Async HTTP client if async_client=True
            httpx.Client: Synchronous HTTP client if async_client=False

        Note:
            The client is configured to automatically follow HTTP redirects.
        """
        # Initialize base httpx client configuration
        kwargs = {
            "follow_redirects": True,  # Auto-follow 301/302 redirects
        }

        # Configure TLS verification based on instance settings
        if not self.verify_tls:
            # Disable certificate verification for self-signed certificates
            # WARNING: This makes connections vulnerable to MITM attacks
            # Only use in development or with trusted internal servers
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False  # Don't verify hostname
            ssl_context.verify_mode = ssl.CERT_NONE  # Don't verify certificate
            kwargs["verify"] = ssl_context
        # If verify_tls is True, httpx uses default verification (secure)

        # Configure request timeout (default: 30 seconds)
        if timeout is None:
            kwargs["timeout"] = httpx.Timeout(30.0)
        else:
            kwargs["timeout"] = timeout

        # Add custom headers if provided
        if headers is not None:
            kwargs["headers"] = headers

        # Add authentication handler if provided
        if auth is not None:
            kwargs["auth"] = auth

        # Return appropriate client type based on async_client parameter
        return httpx.AsyncClient(**kwargs) if async_client else httpx.Client(**kwargs)


    def get_client(self) -> Any:
        """Create and return MCP streamable HTTP client.

        Creates a new streamable HTTP client configured for MCP communication.
        This client handles bidirectional streaming required by the MCP protocol.
        The client is created fresh on each call (lazy initialization) and should
        be used within an async context manager.

        Returns:
            Streamable HTTP client configured for the MCP endpoint

        Example:
            >>> async with client.get_client() as (read, write, _):
            ...     async with ClientSession(read, write) as session:
            ...         await session.initialize()
            ...         # Use session...

        Note:
            The endpoint URL is constructed as:
            - With category: {base_url}/{category}/mcp
            - Without category: {base_url}/mcp
        """
        # Construct MCP endpoint URL based on category configuration
        mcp_url = (
            f"{self.base_url}/{self.category}/mcp"
            if self.category
            else f"{self.base_url}/mcp"
        )

        # Create streamable HTTP client with custom TLS settings
        return streamablehttp_client(
            mcp_url,
            headers=self.headers,
            httpx_client_factory=self.create_httpx_client_with_ssl
        )


    def health_check(self) -> httpx.Response:
        """Perform synchronous health check on the MCP server.

        Sends a GET request to the server's health check endpoint to verify
        the server is running and accessible. This is a synchronous operation
        suitable for startup checks or monitoring.

        Returns:
            httpx.Response: HTTP response from the health endpoint.
                          Status code 200 indicates healthy server.

        Example:
            >>> client = MCPClient("https://server.com", "api-key")
            >>> response = client.health_check()
            >>> if response.status_code == 200:
            ...     print("Server is healthy")

        Note:
            This method uses a synchronous HTTP client and will block
            until the request completes or times out (30 seconds default).
        """
        # Create synchronous HTTP client with authentication headers
        with self.create_httpx_client_with_ssl(
            headers=self.headers,
            async_client=False,  # Use synchronous client
        ) as client:
            # Send GET request to health endpoint
            response = client.get(f"{self.base_url}/api/v1/health")
            return response


    async def run_a_scenario(self, scenario_func: Callable[[ClientSession], Awaitable[Any]]) -> Any:
        """Execute a custom scenario function with an initialized MCP session.

        This method provides a high-level interface for executing custom MCP
        workflows. It handles client creation, session initialization, and
        proper cleanup automatically. The provided scenario function receives
        an initialized MCP session and can call any MCP tools or operations.

        Args:
            scenario_func: An async function that takes a ClientSession and
                          returns any value. The session is initialized and
                          ready to use when the function is called.

        Returns:
            Any: The return value from the scenario function

        Example:
            >>> async def my_scenario(session: ClientSession):
            ...     # List available tools
            ...     tools = await session.list_tools()
            ...     # Call a specific tool
            ...     result = await session.call_tool("tool_name", {})
            ...     return result
            >>>
            >>> result = await client.run_a_scenario(my_scenario)

        Note:
            The MCP client and session are automatically cleaned up when
            the scenario completes, preventing resource leaks.
        """
        # Create MCP client and establish bidirectional streams
        async with self.get_client() as (read_stream, write_stream, _):
            # Create MCP session from streams
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the MCP session (required before any operations)
                await session.initialize()

                # Log scenario execution
                logger.info("Running a scenario...")

                # Execute the user-provided scenario function
                res = await scenario_func(session)

                # Log result for debugging
                logger.debug("Scenario result: %s", res)

                return res


    async def get_tools(self) -> list[types.Tool]:
        """Retrieve list of available tools from the MCP server.

        Queries the MCP server for all available tools and returns them as a list.
        Tools represent callable operations or functions exposed by the MCP server.

        Returns:
            list[types.Tool]: List of Tool objects, each containing:
                - name: Tool identifier
                - description: What the tool does
                - inputSchema: JSON schema for tool arguments

        Example:
            >>> client = MCPClient("https://server.com", "key")
            >>> tools = await client.get_tools()
            >>> for tool in tools:
            ...     print(f"Tool: {tool.name}")
            ...     print(f"Description: {tool.description}")

        Note:
            This is a convenience method that wraps run_a_scenario() with
            a predefined scenario for listing tools.
        """
        async def scenario_func(session: ClientSession):
            """Internal scenario to list tools from the server."""
            # Query server for available tools
            tools = await session.list_tools()

            # Log available tool names for debugging
            logger.info("Available tools: %s", [tool.name for tool in tools.tools])

            # Return the list of tool objects
            return tools.tools

        # Execute the tool listing scenario
        return await self.run_a_scenario(scenario_func)

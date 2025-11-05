"""
Integration tests for MCPClient with MCP servers.

This test suite validates the MCPClient library's ability to:
- Connect to MCP servers over HTTP
- Perform health checks
- List available tools
- Execute complex multi-step scenarios

Environment Variables Required:
    SERVER_URL: Base URL of the MCP server (e.g., "https://example.com")
    API_KEY: API key for authentication

Usage:
    # Run all tests
    uv run --env-file=.env pytest tests/test_mcpserver.py

    # Run specific test
    uv run --env-file=.env pytest tests/test_mcpserver.py::test_health_check -v

Note:
    These are integration tests that require a live MCP server.
    Tests will be skipped if environment variables are not set.
"""

import asyncio
import json
import os
import pytest
from mcp import ClientSession

from mcpclient import MCPClient


@pytest.fixture
def server_config():
    """Pytest fixture to validate and provide server configuration.

    Retrieves SERVER_URL and API_KEY from environment variables and validates
    that both are set. If either is missing, the test is automatically skipped.

    Returns:
        tuple[str, str]: A tuple containing (server_url, api_key)

    Raises:
        pytest.skip: If SERVER_URL or API_KEY environment variables are not set
    """
    server_url = os.environ.get("SERVER_URL")
    api_key = os.environ.get("API_KEY")

    # Skip test if configuration is missing
    if not server_url or not api_key:
        pytest.skip("SERVER_URL and API_KEY environment variables must be set")

    return server_url, api_key


def test_health_check(server_config):
    """Test the MCP server health check endpoint.

    This synchronous test verifies that:
    1. MCPClient can be instantiated with server credentials
    2. The health_check() method successfully connects to the server
    3. The server responds with HTTP 200 status

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - HTTP response status code is 200
    """
    server_url, api_key = server_config

    # Create client without category for base health check
    mcp_lib = MCPClient(server_url, api_key)

    # Call health check endpoint
    response = mcp_lib.health_check()

    # Verify server is healthy
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_job_management_get_tools(server_config):
    """Test retrieving available tools from the job_management category.

    This async test validates that:
    1. MCPClient can connect to a category-specific endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected job management tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required job management tools are available:
            * controller.job_templates_list
            * controller.job_templates_launch_create
            * controller.jobs_read
            * controller.jobs_stdout_read
    """
    server_url, api_key = server_config

    # Create client with job_management category
    mcp_lib = MCPClient(server_url, api_key, category="job_management")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential job management tools are available
    assert 'controller.job_templates_list' in tool_names
    assert 'controller.job_templates_launch_create' in tool_names
    assert 'controller.jobs_read' in tool_names
    assert 'controller.jobs_stdout_read' in tool_names


@pytest.mark.asyncio
async def test_job_management_read_write_use_case(server_config):
    """Test a complete job management workflow: list, launch, monitor, and retrieve output.

    This comprehensive integration test validates an end-to-end job management scenario:
    1. List all job templates and find "Demo Job Template"
    2. Launch a job using the found template
    3. Poll job status until completion (with 3-minute timeout)
    4. Retrieve and verify job output

    This test demonstrates the MCPClient's ability to:
    - Execute custom scenarios with the run_a_scenario() method
    - Call multiple MCP tools in sequence
    - Handle asynchronous operations and timeouts
    - Process JSON responses from tool calls

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - Job templates exist on the server
        - "Demo Job Template" is found
        - Job launches successfully
        - Job completes within 3 minutes
        - Job output contains expected content
        - All tool calls return without errors

    Raises:
        AssertionError: If job doesn't complete within timeout or expected data is missing
    """
    server_url, api_key = server_config

    # Create client for job_management category
    mcp_lib = MCPClient(server_url, api_key, category="job_management")

    async def scenario_func(session: ClientSession):
        """Custom scenario function to execute the complete job workflow."""

        # Step 1: List job templates and find the Demo Job Template
        # This queries the Ansible Automation Platform for available job templates
        res = await session.call_tool(
            name="controller.job_templates_list",
            arguments={
                "version": "v2"
            },
        )
        # Verify the tool call succeeded
        assert not res.isError
        assert res.content and len(res.content) > 0

        # Parse JSON response
        o = json.loads("".join(res.content[0].text))
        assert o["count"] > 0

        # Search for the "Demo Job Template" in results
        demo_job_template = None
        for job_template in o["results"]:
            if job_template["name"] == "Demo Job Template":
                demo_job_template = job_template
                break

        # Verify we found the required template
        assert demo_job_template is not None, "Demo Job Template not found on server"

        # Step 2: Launch a job using the Demo Job Template
        # This creates a new job instance from the template
        res = await session.call_tool(
            name="controller.job_templates_launch_create",
            arguments = {
                "version": "v2",
                "id": demo_job_template["id"],
                "requestBody": {},
            }
        )
        # Verify job launch succeeded
        assert not res.isError
        assert res.content and len(res.content) > 0

        # Parse the launched job details
        job_launched = json.loads("".join(res.content[0].text))
        assert job_launched["name"] == "Demo Job Template"

        # Step 3: Poll job status until completion (with timeout protection)
        # Jobs can take time to execute, so we poll every 3 seconds
        job_complete = False
        max_attempts = 60  # 60 attempts * 3 seconds = 3 minutes max wait
        attempts = 0

        while not job_complete and attempts < max_attempts:
            # Query job status
            res = await session.call_tool(
                name="controller.jobs_read",
                arguments={
                    "version": "v2",
                    "id": job_launched["id"],
                }
            )
            assert not res.isError
            assert res.content and len(res.content) > 0

            # Parse job status
            o = json.loads("".join(res.content[0].text))

            # Check if job completed successfully
            if o["status"] == "successful":
                job_complete = True
                # Verify job is associated with correct template
                assert o["job_template"] == demo_job_template["id"]
            else:
                # Job still running, wait before next poll
                attempts += 1
                await asyncio.sleep(3)  # Wait 3 seconds between checks

        # Ensure job completed within timeout
        assert job_complete, f"Job did not complete within timeout (waited {max_attempts * 3} seconds)"

        # Step 4: Retrieve and verify job output
        # This gets the stdout from the completed job
        res = await session.call_tool(
            name="controller.jobs_stdout_read",
            arguments={
                "version": "v2",
                "id": job_launched["id"],
            }
        )
        # Verify output retrieval succeeded
        assert not res.isError
        assert res.content and len(res.content) > 0

        # Parse job output
        o = json.loads("".join(res.content[0].text))

        # Verify expected content in job output
        # "PLAY [Hello World Sample]" is from the Demo Job Template playbook
        assert "PLAY [Hello World Sample]" in o["content"]

        return

    # Execute the scenario and wait for completion
    await mcp_lib.run_a_scenario(scenario_func)


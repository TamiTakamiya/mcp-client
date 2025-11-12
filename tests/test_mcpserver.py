"""
Integration tests for MCPClient with MCP servers.

This test suite validates the MCPClient library's ability to:
- Connect to MCP servers over HTTP
- Perform health checks
- List available tools
- Execute complex multistep scenarios

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
async def test_inventory_management_get_tools(server_config):
    """Test retrieving available tools from the inventory_management category.

    This async test validates that:
    1. MCPClient can connect to the inventory_management category endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected inventory management tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required inventory management tools are available:
            * controller.inventories_list
            * controller.hosts_list
            * controller.hosts_variable_data_read
    """
    server_url, api_key = server_config

    # Create client with inventory_management category
    mcp_lib = MCPClient(server_url, api_key, category="inventory_management")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential inventory management tools are available
    assert 'controller.inventories_list' in tool_names
    assert 'controller.hosts_list' in tool_names
    assert 'controller.hosts_variable_data_read' in tool_names


@pytest.mark.asyncio
async def test_system_monitoring_get_tools(server_config):
    """Test retrieving available tools from the system_monitoring category.

    This async test validates that:
    1. MCPClient can connect to the system_monitoring category endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected system monitoring tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required system monitoring tools are available:
            * gateway.status_retrieve
            * gateway.activitystream_list
            * gateway.activitystream_retrieve
    """
    server_url, api_key = server_config

    # Create client with system monitoring
    mcp_lib = MCPClient(server_url, api_key, category="system_monitoring")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential system monitoring tools are available
    assert 'gateway.status_retrieve' in tool_names
    assert 'gateway.activitystream_list' in tool_names
    assert 'gateway.activitystream_retrieve' in tool_names


@pytest.mark.asyncio
async def test_user_management_get_tools(server_config):
    """Test retrieving available tools from the user_management category.

    This async test validates that:
    1. MCPClient can connect to the user_management category endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected user management tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required user management tools are available:
            * gateway.users_list
            * gateway.users_create
            * gateway.users_retrieve
            * gateway.users_destroy
    """
    server_url, api_key = server_config

    # Create client with user management
    mcp_lib = MCPClient(server_url, api_key, category="user_management")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential user management tools are available
    assert 'gateway.users_list' in tool_names
    assert 'gateway.users_create' in tool_names
    assert 'gateway.users_retrieve' in tool_names
    assert 'gateway.users_destroy' in tool_names


@pytest.mark.asyncio
async def test_security_compliance_get_tools(server_config):
    """Test retrieving available tools from the security_compliance category.

    This async test validates that:
    1. MCPClient can connect to the security_compliance category endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected security compliance tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required security compliance tools are available:
            * controller.credentials_list
            * controller.credential_types_list
            * controller.credential_types_read
            * controller.credential_types_delete
    """
    server_url, api_key = server_config

    # Create client with security compliance
    mcp_lib = MCPClient(server_url, api_key, category="security_compliance")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential security compliance tools are available
    assert 'controller.credentials_list' in tool_names
    assert 'controller.credential_types_list' in tool_names
    assert 'controller.credential_types_read' in tool_names
    assert 'controller.credential_types_delete' in tool_names


@pytest.mark.asyncio
async def test_platform_configuration_get_tools(server_config):
    """Test retrieving available tools from the platform_configuration category.

    This async test validates that:
    1. MCPClient can connect to the platform_configuration category endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected platform configuration tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required platform configuration tools are available:
            * controller.notification_templates_list
            * controller.notification_templates_create
            * controller.notification_templates_read
            * controller.notification_templates_update
            * controller.notification_templates_delete
    """
    server_url, api_key = server_config

    # Create client with platform configuration
    mcp_lib = MCPClient(server_url, api_key, category="platform_configuration")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential platform configuration tools are available
    assert 'controller.notification_templates_list' in tool_names
    assert 'controller.notification_templates_create' in tool_names
    assert 'controller.notification_templates_read' in tool_names
    assert 'controller.notification_templates_update' in tool_names
    assert 'controller.notification_templates_delete' in tool_names


@pytest.mark.asyncio
async def test_developer_testing_get_tools(server_config):
    """Test retrieving available tools from the developer_testing category.

    This async test validates that:
    1. MCPClient can connect to the developer_testing category endpoint
    2. The get_tools() method successfully lists available tools
    3. Expected developer testing tools are present in the response

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - At least one tool is returned
        - Required developer testing tools are available:
            * controller.workflow_job_templates_launch_create
            * controller.workflow_jobs_list
            * controller.workflow_jobs_read
            * controller.workflow_jobs_workflow_nodes_list
    """
    server_url, api_key = server_config

    # Create client with developer_testing category
    mcp_lib = MCPClient(server_url, api_key, category="developer_testing")

    # Retrieve available tools
    tools = await mcp_lib.get_tools()

    # Verify we got tools back
    assert len(tools) > 0

    # Extract tool names for validation
    tool_names = [tool.name for tool in tools]

    # Verify essential developer testing tools are available
    assert 'controller.workflow_job_templates_launch_create' in tool_names
    assert 'controller.workflow_jobs_list' in tool_names
    assert 'controller.workflow_jobs_read' in tool_names
    assert 'controller.workflow_jobs_workflow_nodes_list' in tool_names



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
        o = json.loads(res.content[0].text)
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
        job_launched = json.loads(res.content[0].text)
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
            o = json.loads(res.content[0].text)

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
        o = json.loads(res.content[0].text)

        # Verify expected content in job output
        # "PLAY [Hello World Sample]" is from the Demo Job Template playbook
        assert "PLAY [Hello World Sample]" in o["content"]

        return

    # Execute the scenario and wait for completion
    await mcp_lib.run_a_scenario(scenario_func)


@pytest.mark.asyncio
async def test_inventory_management_read_only_use_case(server_config):
    """Test a complete inventory management workflow: list inventories, hosts, and retrieve host variables.

    This comprehensive integration test validates an end-to-end inventory management scenario:
    1. List all inventories and find "Demo Inventory"
    2. List all hosts and find "localhost"
    3. Retrieve and verify variable data for the localhost host

    This test demonstrates the MCPClient's ability to:
    - Execute read-only inventory queries with the run_a_scenario() method
    - Navigate through hierarchical inventory data (inventories -> hosts -> variables)
    - Handle multiple sequential tool calls
    - Process and validate JSON responses

    Args:
        server_config: Pytest fixture providing (server_url, api_key) tuple

    Asserts:
        - Inventories exist on the server
        - "Demo Inventory" is found
        - Hosts exist on the server
        - "localhost" host is found
        - Host variable data is successfully retrieved
        - Host configuration matches expected values (ansible_connection, ansible_python_interpreter)
        - All tool calls return without errors

    Raises:
        AssertionError: If expected inventories, hosts, or variables are not found
    """
    server_url, api_key = server_config

    # Create client for inventory_management category
    mcp_lib = MCPClient(server_url, api_key, category="inventory_management")

    async def scenario_func(session: ClientSession):
        """Custom scenario function to execute the complete inventory workflow."""

        # Step 1: List inventories and find the Demo Inventory
        # This queries the Ansible Automation Platform for available inventories
        res = await session.call_tool(
            name="controller.inventories_list",
            arguments={
                "version": "v2"
            },
        )
        # Verify the tool call succeeded
        assert not res.isError
        assert res.content and len(res.content) > 0

        # Parse JSON response
        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        # Search for the "Demo Inventory" in results
        demo_inventory = None
        for inventory in o["results"]:
            if inventory["name"] == "Demo Inventory":
                demo_inventory = inventory
                break

        # Verify we found the required inventory
        assert demo_inventory is not None, "Demo Inventory not found on server"

        # Step 2: List hosts and find localhost
        # This queries all hosts configured in the platform
        res = await session.call_tool(
            name="controller.hosts_list",
            arguments={
                "version": "v2"
            },
        )
        # Verify the tool call succeeded
        assert not res.isError
        assert res.content and len(res.content) > 0

        # Parse JSON response
        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        # Search for the "localhost" host in results
        localhost = None
        for host in o["results"]:
            if host["name"] == "localhost":
                localhost = host
                break

        # Verify we found the required host
        assert localhost is not None, "localhost not found on server"

        # Step 3: Retrieve variable data for the localhost host
        # This gets the Ansible variables configured for this specific host
        res = await session.call_tool(
            name="controller.hosts_variable_data_read",
            arguments={
                "version": "v2",
                "id": localhost["id"],
            },
        )
        # Verify the tool call succeeded
        assert not res.isError
        assert res.content and len(res.content) > 0

        # Parse JSON response containing host variables
        o = json.loads(res.content[0].text)

        # Verify expected Ansible configuration variables
        # ansible_connection should be "local" for localhost
        assert o["ansible_connection"] == "local"
        # ansible_python_interpreter should use the playbook's Python interpreter
        assert o["ansible_python_interpreter"] == "{{ ansible_playbook_python }}"

        return

    # Execute the scenario and wait for completion
    await mcp_lib.run_a_scenario(scenario_func)


@pytest.mark.asyncio
async def test_system_monitoring_read_only_use_case(server_config):
    server_url, api_key = server_config

    mcp_lib = MCPClient(server_url, api_key, category="system_monitoring")

    async def scenario_func(session: ClientSession):
        res = await session.call_tool(
            name="gateway.status_retrieve",
            arguments={},
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert len(o["services"]) > 0

        gateway = None
        controller = None
        for service in o["services"]:
            if service["service_name"] == "gateway":
                gateway = service
            elif service["service_name"] == "controller":
                controller = service
        assert gateway is not None
        assert gateway["status"] == "good"
        assert controller is not None
        assert controller["status"] == "good"

        res = await session.call_tool(
            name="gateway.activitystream_list",
            arguments={
                "page": 1,
                "page_size": 1,
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o
        assert len(o["results"]) == 1
        result = o["results"][0]

        res = await session.call_tool(
            name="gateway.activitystream_retrieve",
            arguments={
                "id": result["id"],
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        content = res.content[0]
        assert content.type == "text"
        assert len(content.text) > 0

        return

    await mcp_lib.run_a_scenario(scenario_func)


@pytest.mark.asyncio
async def test_user_management_read_write_use_case(server_config):
    server_url, api_key = server_config

    # *gateway.users_list
    # *gateway.users_create
    # *gateway.users_retrieve
    # *gateway.users_destroy

    mcp_lib = MCPClient(server_url, api_key, category="user_management")

    async def scenario_func(session: ClientSession):
        res = await session.call_tool(
            name="gateway.users_list",
            arguments={},
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        count = o["count"]
        assert count > 0

        users = json.loads(res.content[0].text)["results"]
        for user in users:
            if user["username"] == "testuser123":
                res = await session.call_tool(
                    name="gateway.users_destroy",
                    arguments={
                        "id": user["id"],
                    },
                )
                assert not res.isError
                assert res.content and len(res.content) > 0
                break

        res = await session.call_tool(
            name="gateway.users_create",
            arguments={
                "requestBody": {
                    "username": "testuser123",
                    "email": "testuser123@localhost",
                    "password": "password123",
                    "is_superuser": False,
                    "is_platform_auditor": False,
                },
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        user = json.loads(res.content[0].text)

        res = await session.call_tool(
            name="gateway.users_retrieve",
            arguments={
                "id": user["id"],
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        user_retrieved = json.loads(res.content[0].text)
        assert user_retrieved["username"] == "testuser123"

        res = await session.call_tool(
            name="gateway.users_destroy",
            arguments={
                "id": user["id"],
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        return

    await mcp_lib.run_a_scenario(scenario_func)


@pytest.mark.asyncio
async def test_security_compliance_only_use_case(server_config):
    server_url, api_key = server_config

    mcp_lib = MCPClient(server_url, api_key, category="security_compliance")

    async def scenario_func(session: ClientSession):
        res = await session.call_tool(
            name="controller.inventories_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        demo_inventory = None
        for inventory in o["results"]:
            if inventory["name"] == "Demo Inventory":
                demo_inventory = inventory
                break

        assert demo_inventory is not None, "Demo Inventory not found on server"

        res = await session.call_tool(
            name="controller.hosts_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        localhost = None
        for host in o["results"]:
            if host["name"] == "localhost":
                localhost = host
                break

        assert localhost is not None, "localhost not found on server"

        res = await session.call_tool(
            name="controller.hosts_variable_data_read",
            arguments={
                "version": "v2",
                "id": localhost["id"],
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)

        assert o["ansible_connection"] == "local"
        assert o["ansible_python_interpreter"] == "{{ ansible_playbook_python }}"

        return

    await mcp_lib.run_a_scenario(scenario_func)


@pytest.mark.asyncio
async def test_platform_configuration_read_only_use_case(server_config):
    server_url, api_key = server_config

    mcp_lib = MCPClient(server_url, api_key, category="platform_configuration")

    async def scenario_func(session: ClientSession):
        res = await session.call_tool(
            name="controller.inventories_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        demo_inventory = None
        for inventory in o["results"]:
            if inventory["name"] == "Demo Inventory":
                demo_inventory = inventory
                break

        assert demo_inventory is not None, "Demo Inventory not found on server"

        res = await session.call_tool(
            name="controller.hosts_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        localhost = None
        for host in o["results"]:
            if host["name"] == "localhost":
                localhost = host
                break

        assert localhost is not None, "localhost not found on server"

        res = await session.call_tool(
            name="controller.hosts_variable_data_read",
            arguments={
                "version": "v2",
                "id": localhost["id"],
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)

        assert o["ansible_connection"] == "local"
        assert o["ansible_python_interpreter"] == "{{ ansible_playbook_python }}"

        return

    await mcp_lib.run_a_scenario(scenario_func)


@pytest.mark.asyncio
async def test_developer_testing_read_only_use_case(server_config):
    server_url, api_key = server_config

    mcp_lib = MCPClient(server_url, api_key, category="platform_configuration")

    async def scenario_func(session: ClientSession):
        res = await session.call_tool(
            name="controller.inventories_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        demo_inventory = None
        for inventory in o["results"]:
            if inventory["name"] == "Demo Inventory":
                demo_inventory = inventory
                break

        assert demo_inventory is not None, "Demo Inventory not found on server"

        res = await session.call_tool(
            name="controller.hosts_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)
        assert o["count"] > 0

        localhost = None
        for host in o["results"]:
            if host["name"] == "localhost":
                localhost = host
                break

        assert localhost is not None, "localhost not found on server"

        res = await session.call_tool(
            name="controller.hosts_variable_data_read",
            arguments={
                "version": "v2",
                "id": localhost["id"],
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0

        o = json.loads(res.content[0].text)

        assert o["ansible_connection"] == "local"
        assert o["ansible_python_interpreter"] == "{{ ansible_playbook_python }}"

        return

    await mcp_lib.run_a_scenario(scenario_func)

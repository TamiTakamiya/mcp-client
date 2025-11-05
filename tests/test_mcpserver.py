import asyncio
import json
import os
import pytest
from mcp import ClientSession

from mcpclient import MCPClient


@pytest.fixture
def server_config():
    """Fixture to validate and provide server configuration."""
    server_url = os.environ.get("SERVER_URL")
    api_key = os.environ.get("API_KEY")

    if not server_url or not api_key:
        pytest.skip("SERVER_URL and API_KEY environment variables must be set")

    return server_url, api_key


def test_health_check(server_config):
    server_url, api_key = server_config
    mcp_lib = MCPClient(server_url, api_key)
    response = mcp_lib.health_check()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_job_management_get_tools(server_config):
    server_url, api_key = server_config
    mcp_lib = MCPClient(server_url, api_key, category="job_management")
    tools = await mcp_lib.get_tools()

    assert len(tools) > 0

    tool_names = [tool.name for tool in tools]
    assert 'controller.job_templates_list' in tool_names
    assert 'controller.job_templates_launch_create' in tool_names
    assert 'controller.jobs_read' in tool_names
    assert 'controller.jobs_stdout_read' in tool_names


@pytest.mark.asyncio
async def test_job_management_read_write_use_case(server_config):
    server_url, api_key = server_config
    mcp_lib = MCPClient(server_url, api_key, category="job_management")

    async def scenario_func(session: ClientSession):
        # 1. Get the ID for the Demo Job Template
        res = await session.call_tool(
            name="controller.job_templates_list",
            arguments={
                "version": "v2"
            },
        )
        assert not res.isError
        assert res.content and len(res.content) > 0
        o = json.loads("".join(res.content[0].text))
        assert o["count"] > 0
        demo_job_template = None
        for job_template in o["results"]:
            if job_template["name"] == "Demo Job Template":
                demo_job_template = job_template
                break
        assert demo_job_template is not None

        # 2. Launch a job using the Demo Job Template
        res = await session.call_tool(
            name="controller.job_templates_launch_create",
            arguments = {
                "version": "v2",
                "id": demo_job_template["id"],
                "requestBody": {},
            }
        )
        assert not res.isError
        assert res.content and len(res.content) > 0
        job_launched = json.loads("".join(res.content[0].text))
        assert job_launched["name"] == "Demo Job Template"

        # 3. Wait until the job completes (with timeout)
        job_complete = False
        max_attempts = 60  # 60 attempts * 3 seconds = 3 minutes max wait
        attempts = 0

        while not job_complete and attempts < max_attempts:
            res = await session.call_tool(
                name="controller.jobs_read",
                arguments={
                    "version": "v2",
                    "id": job_launched["id"],
                }
            )
            assert not res.isError
            assert res.content and len(res.content) > 0
            o = json.loads("".join(res.content[0].text))
            if o["status"] == "successful":
                job_complete = True
                assert o["job_template"] == demo_job_template["id"]
            else:
                attempts += 1
                await asyncio.sleep(3)

        assert job_complete, f"Job did not complete within timeout (waited {max_attempts * 3} seconds)"

        # 4. Get job output
        res = await session.call_tool(
            name="controller.jobs_stdout_read",
            arguments={
                "version": "v2",
                "id": job_launched["id"],
            }
        )
        assert not res.isError
        assert res.content and len(res.content) > 0
        o = json.loads("".join(res.content[0].text))
        assert "PLAY [Hello World Sample]" in o["content"]

        return

    await mcp_lib.run_a_scenario(scenario_func)


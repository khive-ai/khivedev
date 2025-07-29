agent_config = ".khive/agents/analyst"
REPO = "/Users/lion/projects/khivedev"
CC_WORKSPACE = ".khive/workspaces"
FLOW_NAME = "memory_mcp_flow0"


from pathlib import Path
from typing import Literal

from lionagi import iModel
from lionagi.utils import create_path

AgentRole = Literal[
    "orchestrator",
    "analyst",
    "architect",
    "auditor",
    "commentator",
    "critic",
    "implementer",
    "innovator",
    "researcher",
    "reviewer",
    "strategist",
    "tester",
    "theorist",
]

CONTEXT = """
- memory mcp: archives/references/memory
- lion-cognition: crates/lion-cognition
"""

planning_prompt = """
🎯 **Memory MCP Migration - Flow 0: Pain Point Validation**

Task: Create 4 specialized validation instructions for parallel execution.

**Context**: Migrating Python Memory MCP to Rust with lion-cognition architecture. 
Current MCP has 10 critical pain points that need validation and test specifications.

**Critical Pain Points**:
1. ID Management: Short IDs from search don't work with update/forget
2. API Inconsistency: Different response formats across tools
3. Search Issues: Empty queries random, topic filtering broken
4. No Duplicate Detection: Same content saved multiple times
5. Namespace Confusion: Automatic but invisible isolation
6. Update Broken: Rarely works due to ID issues
7. Type Rigidity: Only 4 types, no custom types
8. Metadata Limits: JSON strings only, no querying
9. Performance Issues: Hidden limits, no bulk ops
10. Poor DX: Bad errors, no debugging tools

**Required Output**: Generate 4 validation instructions as `instruct_models` as
part of a structured response in your result message:

1. **Pain Point Validator**: Reproduce each pain point with test cases
2. **Test Suite Creator**: Create pytest suite defining expected behavior
3. **User Journey Mapper**: Document real-world usage patterns  
4. **Performance Baseline**: Establish current metrics vs PostgreSQL targets

Each instruction should:
- Be actionable for parallel execution
- Include lion-cognition integration context
- Specify deliverable formats (pytest files, metrics, docs)
- Address PostgreSQL + pgvector migration needs
- Create executable specifications defining success

Glance through the key files, and then Generate the 4 specialized validation instructions.
"""

synthesis_prompt = """
**Flow 0 Synthesis: Pain Point Validation Results**

Synthesize findings from 4 parallel validators into:

1. **Validated Pain Points Report**
   - Each pain point with severity (1-10) and test cases
   - Business impact assessment

2. **Test Suite Status** 
   - Pytest test count and categories
   - Coverage of 10 pain points

3. **User Journey Specifications**
   - Real-world scenarios with success criteria
   - Common failure modes

4. **Performance Baselines**
   - Current metrics vs PostgreSQL targets
   - Migration benchmarks

5. **Quality Gate Results**
   - [ ] All 10 pain points have tests
   - [ ] Test suite runs and documents behavior
   - [ ] Performance baselines established  
   - [ ] User journeys cover 80% usage

Output: Structured summary with next steps for Flow 1. 
written down as md file under /Users/lion/projects/lionkhive/flows/knowledge_graph_migration/
"""


def create_cc(
    flow_name: str,
    role: AgentRole,
    agent_suffix: str = "",
    model: str = "sonnet",
    verbose_output: bool = True,
    auto_finish: bool = False,
):
    """Create Claude Code model instance for LionAGI operations."""

    params = {"permission_mode": "acceptEdits"}
    if role == "orchestrator":
        params["permission_mode"] = "bypassPermissions"

    elif role not in ["tester", "reviewer", "architect", "implementer"]:
        params["ws"] = f"{CC_WORKSPACE}/{flow_name}/{role}{agent_suffix}"
        params["add_dir"] = "../../../../"
        text = Path(
            f"{REPO}/{CC_WORKSPACE}/agents/{role}/.claude/settings.json"
        ).read_text()
        fp = create_path(
            directory=f"{REPO}/{CC_WORKSPACE}/{flow_name}/{role}{agent_suffix}/.claude",
            filename="settings.json",
            file_exist_ok=True,
        )
        fp.write_text(text)

        # text = Path(
        #     f"{REPO}/{CC_WORKSPACE}/agents/{role}/.claude/.mcp.json"
        # ).read_text()
        # fp = create_path(
        #     directory=f"{REPO}/{CC_WORKSPACE}/{flow_name}/{role}{agent_suffix}",
        #     filename=".mcp.json",
        #     file_exist_ok=True,
        # )
        # fp.write_text(text)

    return iModel(
        provider="claude_code",
        endpoint="query_cli",
        model=model,
        api_key="dummy_api_key",
        verbose_output=verbose_output,
        cli_display_theme="dark",
        auto_finish=auto_finish,
        repo=REPO,
        **params,
    )


async def main():
    try:
        orc_cc = create_cc(
            role="orchestrator",
            flow_name=FLOW_NAME,
            auto_finish=True,
            model="sonnet",
        )

        from lionagi import Branch, Builder, Session
        from lionagi.fields import Instruct

        orchestrator = Branch(
            name=f"{FLOW_NAME}_orchestrator",
            chat_model=orc_cc,
            parse_model=orc_cc,
            use_lion_system_message=True,
            system_datetime=True,
        )

        session = Session(default_branch=orchestrator)
        builder = Builder(FLOW_NAME)

        from lionagi.fields import LIST_INSTRUCT_FIELD_MODEL

        # phase 1: Initial context digestion and Orchestration Planning
        root = builder.add_operation(
            "operate",
            instruct=Instruct(
                instruction=planning_prompt,
                context=CONTEXT,
                guidance=(
                    "You are allowed with only one round of orchestration planning for current flow, "
                    "attempt to return a list in `orchestration_plans` will result in an error, and "
                    "require re-parsing the output."
                ),
            ),
            reason=True,
            field_models=[LIST_INSTRUCT_FIELD_MODEL],
        )

        builder.visualize("🧪 Flow 0: Pain Point Validation - Phase 1: Planning")

        # Execute the initial operation to get orchestration plans
        result = await session.flow(builder.get_graph())

        instruct_models = result["operation_results"][root].instruct_models

        roles = ["tester", "critic", "analyst", "researcher"]
        research_nodes = []
        for idx, instruct in enumerate(instruct_models):
            node = builder.add_operation(
                "communicate",
                depends_on=[root],
                instruction=instruct.model_dump_json(),
                chat_model=create_cc(flow_name=FLOW_NAME, role=roles[idx]),
            )
            research_nodes.append(node)

        builder.visualize("🧪 Flow 0: Pain Point Validation - Phase 2: Research Nodes")
        result = await session.flow(builder.get_graph())

        # Phase 3: Synthesis
        synthesis = builder.add_aggregation(
            "communicate",
            source_node_ids=research_nodes,
            branch=orchestrator,
            instruction=synthesis_prompt,
        )

        builder.visualize("🧪 Flow 0: Pain Point Validation - Phase 3: Synthesis")
        # Execute synthesis operation
        print("⚡ Executing complete Flow 0 validation...")
        result3 = await session.flow(builder.get_graph())
        result_synthesis = result3["operation_results"][synthesis]

        print("🎉 Flow 0 Complete!")
        print("=" * 60)
        print(result_synthesis)
        print("=" * 60)

        return result_synthesis

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import anyio

    anyio.run(main)

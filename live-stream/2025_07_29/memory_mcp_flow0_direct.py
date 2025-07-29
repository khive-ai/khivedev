#!/usr/bin/env python3
"""
Memory MCP Migration - Flow 0: Pain Point Validation
Direct LionAGI implementation using fan_out_in pattern
"""

import asyncio
from lionagi import Branch, Builder, Session
from lionagi.fields import Instruct

from utils import OrchestrationPlanField, create_cc, create_cc_branch, get_branch_summary_from_operation

FLOW_NAME = "memory_mcp_flow0"
CONTEXT = """
- memory mcp: /Users/lion/projects/lionkhive/archives/references/memory
- lion-cognition: /Users/lion/projects/lionkhive/archives/references/lion-cognition
"""


# Flow 0 Orchestrator Prompt
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

async def main():
    try:
        orc_cc = create_cc(
            role="orchestrator",
            flow_name=FLOW_NAME,
            auto_finish=True,
            model="opus",
        )
        orchestrator = Branch(
            name=f"{FLOW_NAME}_orchestrator",
            chat_model=orc_cc,
            parse_model=orc_cc,
            use_lion_system_message=True,
            system_datetime=True,
        )

        session = Session(default_branch=orchestrator)
        builder = Builder(FLOW_NAME)
        
        # phase 1: Initial context digestion and Orchestration Planning
        root = builder.add_operation(
            "operate",
            instruct=Instruct(
                instruction=planning_prompt,
                context=CONTEXT,
                guidance=(
                    "You are allowed with only one round of orchestration planning for current flow, "
                    "attempt to return a list in `orchestration_plans` will result in an error, and "
                    "require re-parsing the output. You must consult with `uv run khive plan [context]` "
                    "to get the task agent compositions suggestions and analysis, which you need to provide"
                    "more than sufficient context for planner to understand the task."
                ),
            ),
            reason=True,
            field_models=[OrchestrationPlanField],
        )

        builder.visualize("🧪 Flow 0: Pain Point Validation - Phase 1: Planning")

        # Execute the initial operation to get orchestration plans
        result = await session.flow(builder.get_graph())

        plan = result["operation_results"][root].orchestration_plans
        for a in plan.agent_requests:
            print(f"Agent: {a.compose_request.role}, Domains: {a.compose_request.domains}, Context: {a.compose_request.context}")
            print(f"- Instruction: {a.instruct.instruction}")

        # phase 2: Add operations for each agent request
        research_nodes = []
        for idx, item in enumerate(plan.agent_requests):
            if idx > 5:
                print(f"⚠️ Skipping instruction {idx} as it exceeds the limit")
                break
            
            instruct = item.instruct
            compose_request = item.compose_request
            node = builder.add_operation(
                "communicate",
                depends_on=[root], 
                branch=await create_cc_branch(
                    compose_request=compose_request,
                    flow_name=FLOW_NAME,
                    session=session,
                ),
                instruction="Perform task, make sure you report all your work in the result message",
                context={
                    "task_instruction": instruct.instruction,
                    "common_background": plan.common_background,
                    "agent_specific_context": instruct.context,
                },
                guidance=(
                    f"{instruct.guidance}"
                    f"{' with deepthink and multi perspective reflection' if instruct.reason else ''}"
                    f"{' with batch tool for parallel execution' if instruct.action_strategy == 'concurrent' else ''}"
                ).strip(),
            )
            research_nodes.append(node)

        # Execute the parallel validation tasks
        builder.visualize("🧪 Flow 0: Pain Point Validation - Phase 2")
        await session.flow(builder.get_graph())

        additional_context = []
        for node in research_nodes:
            summary = get_branch_summary_from_operation(session, node, builder.get_graph())
            additional_context.append(summary)

        # Phase 3: Synthesis
        synthesis = builder.add_aggregation(
            "communicate",
            source_node_ids=research_nodes,
            branch=orchestrator,
            context=additional_context,
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
    asyncio.run(main())

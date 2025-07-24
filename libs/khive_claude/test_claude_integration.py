#!/usr/bin/env python3
"""
Test script to demonstrate khive_claude monitoring system integration with Claude Code.

This script simulates Claude Code hook calls to verify the monitoring system works.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_hook_integration():
    """Test all hook scripts with simulated Claude Code calls."""
    
    print("🧪 Testing khive_claude monitoring system integration")
    print("=" * 60)
    
    hooks_dir = Path(__file__).parent / "src" / "khive_claude" / "hooks"
    
    # Test data for different hook types
    test_cases = [
        {
            "hook": "pre_command.py",
            "input": {
                "session_id": "test_session_001",
                "tool_input": {
                    "command": "ls -la /tmp"
                }
            }
        },
        {
            "hook": "post_command.py", 
            "input": {
                "session_id": "test_session_001",
                "tool_name": "Bash",
                "tool_input": {
                    "command": "ls -la /tmp"
                },
                "tool_output": "total 8\ndrwxrwxrwt  10 root  wheel  320 Jul 24 16:19 .\ndrwxr-xr-x   6 root  admin  192 Jun 24 17:08 .."
            }
        },
        {
            "hook": "pre_edit.py",
            "input": {
                "session_id": "test_session_001",
                "tool_input": {
                    "file_path": "/tmp/test_file.py",
                    "old_string": "def old_function():",
                    "new_string": "def new_function():"
                }
            }
        },
        {
            "hook": "post_edit.py",
            "input": {
                "session_id": "test_session_001", 
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "/tmp/test_file.py"
                },
                "tool_output": "Successfully replaced 1 occurrence of 'def old_function():' with 'def new_function():'"
            }
        },
        {
            "hook": "prompt_submitted.py",
            "input": {
                "session_id": "test_session_001",
                "tool_input": {},
                "metadata": {
                    "prompt": "Help me debug this Python function",
                    "user": "tester"
                }
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        hook_path = hooks_dir / test_case["hook"]
        
        if not hook_path.exists():
            print(f"❌ Hook not found: {hook_path}")
            continue
            
        print(f"🔧 Testing {test_case['hook']}...")
        
        try:
            # Run hook script with test input
            process = subprocess.run(
                [sys.executable, str(hook_path)],
                input=json.dumps(test_case["input"]),
                text=True,
                capture_output=True,
                timeout=10
            )
            
            if process.returncode == 0:
                try:
                    result = json.loads(process.stdout)
                    print(f"   ✅ Success: {result}")
                    results.append({"hook": test_case["hook"], "status": "success", "result": result})
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON output: {process.stdout}")
                    results.append({"hook": test_case["hook"], "status": "warning", "output": process.stdout})
            else:
                print(f"   ❌ Failed (exit {process.returncode}): {process.stderr}")
                results.append({"hook": test_case["hook"], "status": "failed", "error": process.stderr})
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout: Hook took longer than 10 seconds")
            results.append({"hook": test_case["hook"], "status": "timeout"})
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({"hook": test_case["hook"], "status": "exception", "error": str(e)})
    
    print("\n📊 Test Summary:")
    print("-" * 40)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    total_count = len(results)
    
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count > 0:
        print("\n🎉 Monitoring system is working! Hook events should appear in database.")
        print("   Run 'uv run python -m khive_claude.cli status' to see logged events.")
    
    return results

async def test_database_events():
    """Check recent events in database."""
    print("\n🗄️  Checking database for recent events...")
    
    try:
        from khive_claude.hooks.hook_event import HookEvent
        
        events = await HookEvent.get_recent(limit=5)
        print(f"📊 Found {len(events)} recent events")
        
        for event in events[-3:]:  # Show last 3
            print(f"   📝 {event.content.get('event_type', 'unknown')} - {event.content.get('tool_name', 'unknown')}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")

async def main():
    """Main test function."""
    print("🚀 Starting khive_claude integration test\n")
    
    # Test hook scripts
    hook_results = await test_hook_integration()
    
    # Check database
    await test_database_events()
    
    # Final status
    print("\n🏁 Integration test complete!")
    print("\n💡 Next Steps:")
    print("   1. Start monitoring: uv run python -m khive_claude.cli server")
    print("   2. Start dashboard: uv run python -m khive_claude.cli dashboard")  
    print("   3. Configure Claude Code to use these hook scripts")
    
    return hook_results

if __name__ == "__main__":
    asyncio.run(main())
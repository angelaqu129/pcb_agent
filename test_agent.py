"""
Quick test script for PCB Agent

Tests the agent with a simple prompt without running the full workflow.
"""

import asyncio
import os
from pathlib import Path
from pcb_agent import PCBAgent


async def test_agent_setup():
    """Test agent initialization and configuration."""
    print("🧪 Testing PCB Agent Setup")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("DEDALUS_API_KEY")
    if not api_key:
        print("❌ DEDALUS_API_KEY not found in environment")
        print("   Create a .env file with:")
        print("   DEDALUS_API_KEY=your-api-key")
        return False
    else:
        print(f"✅ API key found: {api_key[:10]}...")
    
    # Check required files
    required_files = [
        "allow_list.json",
        "prompt1.txt",
        "prompt2_instructions.txt"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            return False
    
    # Check KiCAD library path
    lib_path = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/")
    if lib_path.exists():
        print(f"✅ KiCAD library found")
    else:
        print(f"⚠️  KiCAD library not found at default location")
        print(f"   Update symbol_lib_path in agent initialization")
    
    # Try to initialize agent
    try:
        agent = PCBAgent(verbose=True)
        print(f"✅ Agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


async def test_simple_prompt():
    """Test agent with a very simple prompt."""
    print("\n🧪 Testing Simple Prompt")
    print("=" * 60)
    
    agent = PCBAgent(verbose=True)
    
    # Use a very simple prompt
    user_prompt = "Create a basic esp32 circuit board"
    
    print(f"Prompt: {user_prompt}")
    print("Running agent... (this may take 30-60 seconds)")
    print()
    
    result = await agent.generate_schematic(user_prompt)
    
    print()
    print("=" * 60)
    print("Test Results:")
    print(f"  Status: {result['status']}")
    
    if result["status"] == "success":
        print(f"  ✅ Workflow completed successfully!")
        print(f"  Components: {len(result['components'])}")
        print(f"  Nets: {len(result['nets'])}")
    else:
        print(f"  ❌ Workflow failed: {result.get('error')}")
    
    return result


async def main():
    """Run all tests."""
    print("PCB Agent Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Setup
    setup_ok = await test_agent_setup()
    
    if not setup_ok:
        print("\n⚠️  Setup test failed. Fix issues before running workflow test.")
        return
    
    # Test 2: Ask user if they want to run the workflow test
    print("\n" + "=" * 60)
    response = input("Run full workflow test? (y/n): ")
    
    if response.lower() == 'y':
        await test_simple_prompt()
    else:
        print("Skipped workflow test.")
    
    print("\n✨ Tests complete!")


if __name__ == "__main__":
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(main())

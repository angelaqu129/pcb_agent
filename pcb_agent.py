"""
Cursor PCB - Automated Agent System

Orchestrates Phases 1-5 of PCB schematic generation using Dedalus SDK.
Stops after llm_output2.json is generated (before wire drawing).
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os

from dedalus_labs import AsyncDedalus, DedalusRunner

# Import existing schematic functions
from schematic import (
    place_from_llm_output,
    add_pin_outs,
    clear_schematic,
)

load_dotenv()


class PCBAgent:
    """Main agent orchestrating PCB schematic generation workflow."""
    
    def __init__(
        self,
        allow_list_path: str = "allow_list.json",
        symbol_lib_path: str = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",
        prompt1_path: str = "prompt1.txt",
        prompt2_instructions_path: str = "prompt2_instructions.txt",
        verbose: bool = False,
        log_file: str = "pcb_agent.log"
    ):
        """
        Initialize PCB Agent.
        
        Args:
            allow_list_path: Path to component allowlist JSON
            symbol_lib_path: Path to KiCAD symbol library directory
            prompt1_path: Path to Phase 1 LLM instructions
            prompt2_instructions_path: Path to Phase 5 LLM instructions
            verbose: Enable verbose logging
            log_file: Path to log file (set to None to disable file logging)
        """
        self.allow_list_path = Path(allow_list_path)
        self.symbol_lib = Path(symbol_lib_path)
        self.prompt1_path = Path(prompt1_path)
        self.prompt2_instructions_path = Path(prompt2_instructions_path)
        self.verbose = verbose or os.getenv("PCB_AGENT_VERBOSE") == "1"
        self.log_file = Path(log_file) if log_file else None
        
        # Clear log file at start of new session
        if self.log_file:
            self.log_file.write_text("")  # Clear previous logs
        
        # Initialize Dedalus client
        api_key = os.getenv("DEDALUS_API_KEY")
        if not api_key:
            raise ValueError(
                "DEDALUS_API_KEY not found. "
                "Set it in .env file or environment variable."
            )
        
        self.client = AsyncDedalus(api_key=api_key)
        self.runner = DedalusRunner(self.client)
        
        self.log("PCBAgent initialized")
    
    def log(self, message: str, phase: Optional[int] = None):
        """Log message if verbose mode enabled."""
        if self.verbose:
            from datetime import datetime
            
            # Format log message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prefix = f"[Phase {phase}]" if phase else "[Agent]"
            log_message = f"{prefix} {message}"
            full_log = f"[{timestamp}] {log_message}"
            
            # Print to terminal
            print(log_message)
            
            # Write to log file if enabled
            if self.log_file:
                try:
                    with self.log_file.open("a", encoding="utf-8") as f:
                        f.write(f"{full_log}\n")
                except Exception as e:
                    # Don't crash if logging fails, just print error
                    print(f"[Warning] Failed to write to log file: {e}")
    
    async def generate_schematic(
        self,
        user_prompt: str,
        schematic_path: str = "/Users/angelaqu/Desktop/test/test.kicad_sch",
        model: str = "openai/gpt-5.2"
    ) -> Dict[str, Any]:
        """
        Run complete workflow from user prompt to netlist generation.
        
        Phases executed:
        1. Component selection (LLM)
        2. Component placement (Python)
        3. Pin mapping (Python)
        4. Prompt generation (Python)
        5. Netlist generation (LLM)
        
        Args:
            user_prompt: Natural language circuit description
            schematic_path: Output path for KiCAD schematic file
            model: LLM model to use (default: Claude Sonnet)
        
        Returns:
            Dictionary with status, components, nets, and file paths
        """
        sch_path = Path(schematic_path)
        clear_schematic(sch_path)
        try:
            # ============================================================
            # STAGE 0: Component Filtering (Fast LLM)
            # ============================================================
            self.log("Pre-filtering components from allowlist", phase=0)
            filtered_allowlist = await self._stage0_filter_components(
                user_prompt
            )
            self.log(
                f"Filtered to {len(filtered_allowlist)} relevant components "
                f"(from {self._get_total_components()} total)",
                phase=0
            )
            
            # ============================================================
            # PHASE 1: Component Selection (LLM with filtered list)
            # ============================================================
            self.log("Starting component selection with filtered list", phase=1)
            llm_output1 = await self._phase1_component_selection(
                user_prompt, model, filtered_allowlist
            )
            
            # Save llm_output1.json
            output1_path = Path("llm_output1.json")
            with output1_path.open("w", encoding="utf-8") as f:
                json.dump(llm_output1, f, indent=2)
            self.log(f"Saved {output1_path}", phase=1)
            
            # ============================================================
            # PHASE 2: Component Placement (Python)
            # ============================================================
            self.log("Placing components in schematic", phase=2)
            place_from_llm_output(sch_path, self.symbol_lib, llm_output1)
            self.log(f"Components placed in {sch_path}", phase=2)
            
            # ============================================================
            # PHASE 3: Pin Mapping (Python)
            # ============================================================
            self.log("Extracting pin information from libraries", phase=3)
            llm_output1_with_pins = add_pin_outs(self.symbol_lib, llm_output1)
            
            # Save llm_output1_with_pins.json
            output1_pins_path = Path("llm_output1_with_pins.json")
            with output1_pins_path.open("w", encoding="utf-8") as f:
                json.dump(llm_output1_with_pins, f, indent=2)
            self.log(f"Saved {output1_pins_path}", phase=3)
            
            # ============================================================
            # PHASE 4: Prompt Generation (Python)
            # ============================================================
            self.log("Generating prompt for netlist LLM", phase=4)
            prompt2_path = self._phase4_generate_prompt(llm_output1_with_pins)
            self.log(f"Saved {prompt2_path}", phase=4)
            
            # ============================================================
            # PHASE 5: Netlist Generation (LLM)
            # ============================================================
            self.log("Generating netlist connections", phase=5)
            llm_output2 = await self._phase5_netlist_generation(
                prompt2_path, model
            )
            
            # Save llm_output2.json
            output2_path = Path("llm_output2.json")
            with output2_path.open("w", encoding="utf-8") as f:
                json.dump(llm_output2, f, indent=2)
            self.log(f"Saved {output2_path}", phase=5)
            
            # ============================================================
            # PHASE 6: Wire Drawing (Python)
            # ============================================================
            self.log("Drawing wires between pins", phase=6)
            self._phase6_draw_wires(sch_path, llm_output1_with_pins, llm_output2)
            self.log(f"Wires drawn in {sch_path}", phase=6)
            
            # ============================================================
            # COMPLETE - Return results
            # ============================================================
            self.log("Workflow complete! All 6 phases finished.")
            
            return {
                "status": "success",
                "phases_completed": 6,
                "components": llm_output1_with_pins.get("symbols", []),
                "nets": llm_output2.get("nets", []),
                "files": {
                    "schematic": str(sch_path),
                    "output1": str(output1_path),
                    "output1_with_pins": str(output1_pins_path),
                    "prompt2": str(prompt2_path),
                    "output2": str(output2_path)
                },
                "message": "Complete schematic generated with components and wires!"
            }
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Workflow failed. Check logs for details."
            }
    
    def _get_total_components(self) -> int:
        """Get total number of components in allowlist."""
        with self.allow_list_path.open("r", encoding="utf-8") as f:
            allow_list_data = json.load(f)
        return len(allow_list_data.get("allowlist", []))
    
    async def _stage0_filter_components(
        self,
        user_prompt: str,
        filter_model: str = "openai/gpt-4o"
    ) -> List[Dict[str, Any]]:
        """
        Stage 0: Pre-filter components using fast LLM.
        
        Args:
            user_prompt: User's circuit description
            filter_model: Fast model for filtering (default: gpt-4o-mini)
        
        Returns:
            Filtered list of relevant components
        """
        # Load full allowlist
        with self.allow_list_path.open("r", encoding="utf-8") as f:
            allow_list_data = json.load(f)
        
        full_allowlist = allow_list_data.get("allowlist", [])
        
        # Build filtering prompt
        filter_prompt = f"""You are a component selector for PCB design.

Task: Select ONLY the components needed for this circuit from the allowlist.

User Request: "{user_prompt}"

Available Components:
{json.dumps(full_allowlist, indent=2)}

Instructions:
1. Analyze the user request carefully
2. Select all components needed
3. Always include power symbols if circuit needs power (GND, +5V, +3V3)
4. Only include components that are directly relevant
5. Return JSON with selected components and reasoning

Output Format (JSON only):
{{
  "selected": [
    {{"lib": "...", "symbol": "...", "ref": "...", "footprint": "...", "reason": "why needed"}},
    ...
  ]
}}

Rules:
- Include power symbols for any powered circuit
- Be conservative - only select what's truly needed
- Return valid JSON only
"""
        
        self.log(f"Calling filtering LLM (model: {filter_model})", phase=0)
        
        # Call fast LLM for filtering
        kwargs = {"input": filter_prompt, "model": filter_model}
        if filter_model.startswith("openai/"):
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.runner.run(**kwargs)
        
        # Parse response
        try:
            result = json.loads(response.final_output)
            selected = result.get("selected", [])
            
            if not selected:
                self.log("Warning: No components selected, using full allowlist", phase=0)
                return full_allowlist
            
            # Log filtered components
            component_names = [c.get("symbol", "?") for c in selected]
            self.log(f"Selected components: {', '.join(component_names)}", phase=0)
            
            return selected
            
        except json.JSONDecodeError as e:
            self.log(f"Warning: Filter LLM returned invalid JSON, using full allowlist", phase=0)
            return full_allowlist
    
    async def _phase1_component_selection(
        self,
        user_prompt: str,
        model: str,
        filtered_allowlist: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Phase 1: LLM selects components from filtered allowlist.
        
        Args:
            user_prompt: User's circuit description
            model: LLM model to use
            filtered_allowlist: Pre-filtered component list
        
        Returns:
            Component list JSON (llm_output1)
        """
        # Load allowlist
        with self.allow_list_path.open("r", encoding="utf-8") as f:
            allow_list_data = json.load(f)
        
        # Load prompt1 instructions
        with self.prompt1_path.open("r", encoding="utf-8") as f:
            prompt1_template = f.read()
        
        # Build complete prompt with filtered allowlist
        input_data = {
            "allowlist": filtered_allowlist,
            "canvas": allow_list_data.get("canvas", {}),
            "request": user_prompt
        }
        
        full_prompt = (
            prompt1_template.rstrip()
            + "\n\nINPUT:\n"
            + json.dumps(input_data, indent=2)
        )
        
        self.log(f"Calling LLM for component selection (model: {model})", phase=1)
        
        # Call LLM via Dedalus
        # Note: response_format only works with OpenAI models
        kwargs = {"input": full_prompt, "model": model}
        if model.startswith("openai/"):
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.runner.run(**kwargs)
        
        # Parse JSON response
        try:
            result = json.loads(response.final_output)
            
            # Check for error response
            if "error" in result:
                raise ValueError(
                    f"LLM returned error: {result['error'].get('message', 'Unknown error')}"
                )
            
            self.log(f"Selected {len(result.get('symbols', []))} components", phase=1)
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
    
    def _phase4_generate_prompt(
        self,
        llm_output1_with_pins: Dict[str, Any]
    ) -> Path:
        """
        Phase 4: Generate prompt2.txt for netlist LLM.
        
        Args:
            llm_output1_with_pins: Component list with pin data
        
        Returns:
            Path to generated prompt2.txt
        """
        # Load prompt2 instructions
        with self.prompt2_instructions_path.open("r", encoding="utf-8") as f:
            base_prompt = f.read()
        
        # Simplify pins for LLM (remove coordinates, keep only names)
        simplified = self._simplify_pins_for_llm(llm_output1_with_pins)
        
        # Build complete prompt
        final_prompt = (
            base_prompt.rstrip()
            + "\n\n"
            + "Here is the component list JSON:\n\n"
            + json.dumps(simplified, indent=2)
            + "\n"
        )
        
        # Save prompt2.txt
        prompt2_path = Path("prompt2.txt")
        prompt2_path.write_text(final_prompt, encoding="utf-8")
        
        return prompt2_path
    
    def _simplify_pins_for_llm(
        self,
        llm_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simplify pin format for LLM.
        
        Before: {"1": {"name": "VDD", "pos": [150.5, 100.2, 0]}}
        After:  {"1": "VDD"}
        
        LLM doesn't need coordinates for netlist generation.
        """
        from copy import deepcopy
        
        out = deepcopy(llm_output)
        for s in out.get("symbols", []):
            pins = s.get("pins")
            if isinstance(pins, dict):
                s["pins"] = {
                    pin_num: pin_data.get("name", "")
                    for pin_num, pin_data in pins.items()
                }
        return out
    
    async def _phase5_netlist_generation(
        self,
        prompt2_path: Path,
        model: str
    ) -> Dict[str, Any]:
        """
        Phase 5: LLM generates netlist connections.
        
        Args:
            prompt2_path: Path to prompt2.txt
            model: LLM model to use
        
        Returns:
            Netlist JSON (llm_output2)
        """
        # Load prompt2
        with prompt2_path.open("r", encoding="utf-8") as f:
            prompt2 = f.read()
        
        self.log(f"Calling LLM for netlist generation (model: {model})", phase=5)
        
        # Call LLM via Dedalus
        # Note: response_format only works with OpenAI models
        kwargs = {"input": prompt2, "model": model}
        if model.startswith("openai/"):
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.runner.run(**kwargs)
        
        # Parse JSON response
        try:
            result = json.loads(response.final_output)
            
            self.log(f"Generated {len(result.get('nets', []))} nets", phase=5)
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
    
    def _phase6_draw_wires(
        self,
        sch_path: Path,
        llm_output1_with_pins: Dict[str, Any],
        llm_output2: Dict[str, Any]
    ):
        """
        Phase 6: Draw wires between component pins.
        
        Args:
            sch_path: Path to KiCAD schematic file
            llm_output1_with_pins: Component list with pin coordinates
            llm_output2: Netlist with connections
        """
        from schematic import draw_nets
        
        # Call the existing draw_nets function from schematic.py
        draw_nets(sch_path, llm_output1_with_pins, llm_output2)
        
        # Count wires drawn
        nets_count = len(llm_output2.get("nets", []))
        total_connections = sum(
            len(net.get("connections", []))
            for net in llm_output2.get("nets", [])
        )
        
        self.log(
            f"Drew {nets_count} nets with {total_connections} total connections",
            phase=6
        )


async def main():
    """Example usage of PCBAgent."""
    import sys
    # Get user prompt from command line or use default
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = "Create a simple ESP32-C3 circuit"
    
    print(f"🤖 Starting PCB Agent")
    print(f"📝 User prompt: {user_prompt}")
    print(f"=" * 60)
    
    # Initialize agent with verbose logging
    agent = PCBAgent(verbose=True)
    
    # Run workflow
    result = await agent.generate_schematic(user_prompt)
    
    print(f"=" * 60)
    
    if result["status"] == "success":
        print(f"✅ SUCCESS!")
        print(f"   Phases completed: {result['phases_completed']}")
        print(f"   Components: {len(result['components'])}")
        print(f"   Nets: {len(result['nets'])}")
        print(f"\n📁 Files generated:")
        for name, path in result["files"].items():
            print(f"   - {name}: {path}")
        print(f"\n💡 {result['message']}")
    else:
        print(f"❌ FAILED: {result['error']}")
        print(f"   {result['message']}")


if __name__ == "__main__":
    asyncio.run(main())

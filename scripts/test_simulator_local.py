#!/usr/bin/env python3
"""
Simple script to test the simulator locally and generate transaction file.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.simulator.main import SimulatorApp


async def main():
    """Run simulator with test configuration."""
    config_path = project_root / "config" / "simulator_config_test.yaml"
    
    print("=" * 60)
    print("Payment Simulator Local Test")
    print("=" * 60)
    print(f"\nConfiguration: {config_path}")
    print(f"Output: output/transactions.jsonl\n")
    
    # Create output directory
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Run simulator
    app = SimulatorApp(config_path=str(config_path))
    app.initialize()
    
    try:
        await app.run()
    finally:
        await app.shutdown()
    
    # Check output
    output_file = output_dir / "transactions.jsonl"
    if output_file.exists():
        with open(output_file, 'r') as f:
            lines = f.readlines()
        
        print("\n" + "=" * 60)
        print("Results")
        print("=" * 60)
        print(f"Output file: {output_file}")
        print(f"Transactions generated: {len(lines)}")
        print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")
        
        # Show first transaction
        if lines:
            import json
            first_tx = json.loads(lines[0])
            print("\nFirst transaction sample:")
            print("-" * 60)
            print(json.dumps(first_tx, indent=2, default=str))
        
        print("\n✅ Test completed successfully!")
    else:
        print("\n⚠️  Warning: Output file not found")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


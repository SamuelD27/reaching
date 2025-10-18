#!/usr/bin/env python3
"""
Checkpoint/Resume Example
Demonstrates save and resume functionality
"""

import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.checkpoint_manager import CheckpointManager


def main():
    """Demonstrate checkpoint save/resume"""
    print("=" * 80)
    print("CHECKPOINT/RESUME EXAMPLE")
    print("=" * 80)

    # Initialize manager
    manager = CheckpointManager()

    # Check for existing checkpoint
    if manager.has_checkpoint():
        print("\n📂 Found existing checkpoint!")
        checkpoint = manager.load_checkpoint()

        if checkpoint:
            response = input("\nResume from checkpoint? (y/n): ")
            if response.lower() == 'y':
                contacts = checkpoint['data'].get('contacts', [])
                position = checkpoint['position']
                start_idx = position.get('index', 0)
                print(f"✅ Resuming from position {start_idx}")
                print(f"Already extracted: {len(contacts)} contacts\n")
            else:
                manager.clear_checkpoint()
                contacts = []
                start_idx = 0
                print("Starting fresh...\n")
        else:
            contacts = []
            start_idx = 0
    else:
        contacts = []
        start_idx = 0
        print("\nNo checkpoint found, starting fresh...\n")

    # Simulate extraction
    companies = ['Goldman Sachs', 'Morgan Stanley', 'Blackstone', 'Citadel', 'KKR']

    print("Simulating extraction (Press Ctrl+C to interrupt)\n")

    try:
        for idx in range(start_idx, len(companies)):
            company = companies[idx]

            print(f"[{idx+1}/{len(companies)}] Extracting from {company}...")

            # Simulate work
            for i in range(5):
                time.sleep(0.5)
                contacts.append({
                    'name': f'Person {len(contacts)+1}',
                    'company': company
                })
                print(f"  Extracted {len(contacts)} contacts total...")

            # Save checkpoint after each company
            manager.save_checkpoint(
                data={'contacts': contacts, 'count': len(contacts)},
                position={'index': idx + 1, 'company': company}
            )
            print()

        # Completed successfully
        print(f"\n✅ Extraction complete! Total: {len(contacts)} contacts")
        manager.clear_checkpoint()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted! Progress has been saved.")
        print("Run this script again to resume from where you left off.")

    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())

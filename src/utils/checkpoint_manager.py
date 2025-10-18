"""
Checkpoint Manager for Save/Resume Functionality
Allows extraction to be interrupted and resumed without losing progress
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class CheckpointManager:
    """
    Manages checkpoints for extraction progress

    Features:
    - Save extraction state at any point
    - Resume from last checkpoint
    - Automatic timestamping
    - Safe file operations with atomic writes
    """

    def __init__(self, checkpoint_file: str = "data/checkpoint.json"):
        """
        Initialize checkpoint manager

        Args:
            checkpoint_file: Path to checkpoint file
        """
        self.checkpoint_file = Path(checkpoint_file)

        # Ensure data directory exists
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, data: Dict[str, Any], position: Dict[str, Any]) -> None:
        """
        Save checkpoint with current state

        Args:
            data: Extracted data so far (list of contacts)
            position: Current position info (company_idx, location, etc.)

        Example:
            manager.save_checkpoint(
                data={'contacts': [...], 'count': 50},
                position={'company_idx': 5, 'location': 'Singapore', 'company': 'Goldman Sachs'}
            )
        """
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'position': position,
            'version': '1.0'
        }

        # Atomic write: write to temp file, then rename
        temp_file = self.checkpoint_file.with_suffix('.tmp')

        try:
            with open(temp_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)

            # Atomic rename (overwrites existing)
            temp_file.replace(self.checkpoint_file)

            print(f"✅ Checkpoint saved: {position.get('company', 'Unknown')} - "
                  f"{data.get('count', 0)} contacts")

        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint if exists

        Returns:
            Dict with 'data' and 'position' keys, or None if no checkpoint
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            # Validate checkpoint structure
            if 'data' not in checkpoint or 'position' not in checkpoint:
                print("⚠️  Invalid checkpoint file, starting fresh")
                return None

            timestamp = checkpoint.get('timestamp', 'Unknown')
            count = checkpoint['data'].get('count', 0)
            position = checkpoint['position']

            print(f"\n{'='*60}")
            print(f"📂 CHECKPOINT FOUND")
            print(f"{'='*60}")
            print(f"Saved: {timestamp}")
            print(f"Contacts extracted: {count}")
            print(f"Last position: {position.get('company', 'Unknown')}")
            print(f"{'='*60}\n")

            return checkpoint

        except json.JSONDecodeError:
            print("⚠️  Corrupted checkpoint file, starting fresh")
            return None
        except Exception as e:
            print(f"⚠️  Error loading checkpoint: {e}")
            return None

    def clear_checkpoint(self) -> None:
        """
        Clear checkpoint file (on completion or reset)
        """
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                print("✅ Checkpoint cleared (extraction complete)")
            except Exception as e:
                print(f"⚠️  Failed to clear checkpoint: {e}")

    def has_checkpoint(self) -> bool:
        """Check if checkpoint exists"""
        return self.checkpoint_file.exists()

    def get_checkpoint_info(self) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint info without loading full data

        Returns:
            Dict with timestamp, count, position (but not full data)
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            return {
                'timestamp': checkpoint.get('timestamp'),
                'count': checkpoint['data'].get('count', 0),
                'position': checkpoint.get('position'),
                'file_size': self.checkpoint_file.stat().st_size
            }
        except:
            return None

    def backup_checkpoint(self) -> None:
        """Create backup of current checkpoint"""
        if not self.checkpoint_file.exists():
            return

        backup_file = self.checkpoint_file.with_suffix('.backup')
        try:
            import shutil
            shutil.copy2(self.checkpoint_file, backup_file)
            print(f"✅ Checkpoint backed up to {backup_file}")
        except Exception as e:
            print(f"⚠️  Failed to backup checkpoint: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = CheckpointManager()

    # Simulate extraction
    print("Simulating extraction with checkpoints...\n")

    # Check for existing checkpoint
    if manager.has_checkpoint():
        checkpoint = manager.load_checkpoint()
        if checkpoint:
            resume_choice = input("Resume from checkpoint? (y/n): ")
            if resume_choice.lower() != 'y':
                manager.clear_checkpoint()
                checkpoint = None
    else:
        checkpoint = None

    # Start or resume extraction
    if checkpoint:
        contacts = checkpoint['data'].get('contacts', [])
        start_idx = checkpoint['position'].get('company_idx', 0)
        print(f"Resuming from company {start_idx}...")
    else:
        contacts = []
        start_idx = 0
        print("Starting fresh extraction...")

    # Simulate extracting from multiple companies
    companies = ['Goldman Sachs', 'Morgan Stanley', 'BlackRock', 'Citadel', 'KKR']

    for idx in range(start_idx, len(companies)):
        company = companies[idx]
        print(f"\nExtracting from {company}...")

        # Simulate getting contacts
        import time
        time.sleep(1)  # Simulate API calls

        # Add dummy contacts
        for i in range(10):
            contacts.append({
                'name': f'Person {len(contacts)+1}',
                'company': company,
                'title': 'Senior Manager'
            })

        # Save checkpoint after each company
        manager.save_checkpoint(
            data={'contacts': contacts, 'count': len(contacts)},
            position={'company_idx': idx + 1, 'company': company}
        )

    # Extraction complete
    print(f"\n✅ Extraction complete! Total contacts: {len(contacts)}")
    manager.clear_checkpoint()

    # Show how to get checkpoint info
    print("\nCheckpoint info:")
    info = manager.get_checkpoint_info()
    if info:
        print(f"  Timestamp: {info['timestamp']}")
        print(f"  Count: {info['count']}")
        print(f"  Position: {info['position']}")
    else:
        print("  No checkpoint exists")

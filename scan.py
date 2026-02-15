#!/usr/bin/env python3
"""
Simple CLI script to test MacDitto scanner functionality.
Usage: python scan.py
"""

import sys
import json
from macditto.scanner import Scanner
from macditto.models import ScanProfile


def main():
    """Run a complete system scan and save results."""
    print("=" * 60)
    print("MacDitto Scanner - Testing Scanner Module")
    print("=" * 60)
    print()

    try:
        # Create scanner and run scan
        scanner = Scanner()
        profile = scanner.scan_all()

        # Save to JSON file
        output_file = "scan_results.json"
        profile.save(output_file)
        print(f"\n✅ Scan complete! Results saved to: {output_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"Machine: {profile.machine_name}")
        print(f"Scan Date: {profile.scan_date}")
        print(f"Homebrew Formulae: {len(profile.homebrew_formulae)}")
        print(f"Homebrew Casks: {len(profile.homebrew_casks)}")
        print(f"Applications: {len(profile.applications)}")
        print(f"Dock Items: {len(profile.dock_items)}")
        print(f"Login Items: {len(profile.login_items)}")
        print(f"Shell Configs: {len(profile.shell_configs)}")
        print(f"Git Config: {'Yes' if profile.git_config else 'No'}")
        print(f"Browser Extensions: {len(profile.browser_extensions)}")
        print(f"Browser Bookmarks: {len(profile.browser_bookmarks)} browsers")
        print(f"System Preferences: {len(profile.system_preferences)}")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error during scan: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

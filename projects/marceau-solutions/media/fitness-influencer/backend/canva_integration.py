#!/usr/bin/env python3
"""
Canva API Integration
Create and manage branded designs programmatically.

Features:
- Create designs from templates
- Upload brand assets
- Export finished designs
- Manage design library

Usage:
    python canva_integration.py create --template "fitness-tip" --title "Staying Lean"
    python canva_integration.py export --design-id "DAFxyz123"
    python canva_integration.py upload --file "logo.png"
"""

import argparse
import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class CanvaAPI:
    """Wrapper for Canva Connect APIs."""

    BASE_URL = "https://api.canva.com/rest/v1"

    def __init__(self, api_key=None):
        """
        Initialize Canva API client.

        Args:
            api_key: Canva API key (or set CANVA_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('CANVA_API_KEY')
        if not self.api_key:
            raise ValueError("CANVA_API_KEY not found in environment")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def create_design(self, template_id=None, title="Untitled Design", width=1080, height=1080):
        """
        Create a new design.

        Args:
            template_id: Optional template to use
            title: Design title
            width: Design width (px)
            height: Design height (px)

        Returns:
            Design object with ID and edit URL
        """
        endpoint = f"{self.BASE_URL}/designs"

        payload = {
            "asset_type": "Design",
            "title": title,
            "width": width,
            "height": height
        }

        if template_id:
            payload["template_id"] = template_id

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()

            design = response.json()
            print(f"✓ Created design: {design['id']}")
            print(f"  Edit URL: {design.get('urls', {}).get('edit_url')}")
            return design

        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to create design: {response.status_code}")
            print(f"  {response.text}")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def get_design(self, design_id):
        """
        Get design information.

        Args:
            design_id: Design ID to retrieve

        Returns:
            Design object
        """
        endpoint = f"{self.BASE_URL}/designs/{design_id}"

        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()

            design = response.json()
            print(f"✓ Retrieved design: {design.get('title', 'Untitled')}")
            return design

        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to get design: {response.status_code}")
            print(f"  {response.text}")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def export_design(self, design_id, format='jpg', output_path=None):
        """
        Export a design to file.

        Args:
            design_id: Design ID to export
            format: Export format (jpg, png, pdf)
            output_path: Where to save file

        Returns:
            Path to exported file
        """
        endpoint = f"{self.BASE_URL}/designs/{design_id}/export"

        payload = {
            "format": format.lower()
        }

        try:
            # Request export
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()

            export_data = response.json()
            download_url = export_data.get('url')

            if not download_url:
                print("✗ No download URL returned")
                return None

            # Download the file
            print(f"→ Downloading {format.upper()} file...")
            file_response = requests.get(download_url)
            file_response.raise_for_status()

            if not output_path:
                output_path = f"design_{design_id}.{format}"

            with open(output_path, 'wb') as f:
                f.write(file_response.content)

            print(f"✓ Exported design to: {output_path}")
            return output_path

        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to export design: {response.status_code}")
            print(f"  {response.text}")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def upload_asset(self, file_path):
        """
        Upload brand asset to Canva.

        Args:
            file_path: Path to file to upload

        Returns:
            Asset ID
        """
        endpoint = f"{self.BASE_URL}/assets"

        if not os.path.exists(file_path):
            print(f"✗ File not found: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                # Remove Content-Type header for multipart upload
                headers = {'Authorization': f'Bearer {self.api_key}'}

                response = requests.post(
                    endpoint,
                    headers=headers,
                    files=files
                )
                response.raise_for_status()

            asset = response.json()
            print(f"✓ Uploaded asset: {asset.get('id')}")
            print(f"  Name: {asset.get('name')}")
            return asset.get('id')

        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to upload asset: {response.status_code}")
            print(f"  {response.text}")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def list_designs(self, limit=10):
        """
        List user's designs.

        Args:
            limit: Maximum number of designs to return

        Returns:
            List of designs
        """
        endpoint = f"{self.BASE_URL}/designs"
        params = {'limit': limit}

        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            designs = data.get('items', [])

            print(f"✓ Found {len(designs)} design(s)")
            for design in designs:
                print(f"  • {design.get('title', 'Untitled')} (ID: {design.get('id')})")

            return designs

        except requests.exceptions.HTTPError as e:
            print(f"✗ Failed to list designs: {response.status_code}")
            print(f"  {response.text}")
            return []
        except Exception as e:
            print(f"✗ Error: {e}")
            return []


def main():
    """CLI for Canva integration."""
    parser = argparse.ArgumentParser(
        description='Canva API Integration - Create and manage branded designs'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new design')
    create_parser.add_argument('--template', help='Template ID to use')
    create_parser.add_argument('--title', required=True, help='Design title')
    create_parser.add_argument('--width', type=int, default=1080, help='Width in pixels')
    create_parser.add_argument('--height', type=int, default=1080, help='Height in pixels')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get design information')
    get_parser.add_argument('--design-id', required=True, help='Design ID to retrieve')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export a design')
    export_parser.add_argument('--design-id', required=True, help='Design ID to export')
    export_parser.add_argument('--format', default='jpg', choices=['jpg', 'png', 'pdf'], help='Export format')
    export_parser.add_argument('--output', help='Output file path')

    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload brand asset')
    upload_parser.add_argument('--file', required=True, help='File to upload')

    # List command
    list_parser = subparsers.add_parser('list', help='List designs')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum designs to return')

    args = parser.parse_args()

    try:
        print("→ Initializing Canva API...\n")
        canva = CanvaAPI()

        if args.command == 'create':
            canva.create_design(
                template_id=args.template,
                title=args.title,
                width=args.width,
                height=args.height
            )

        elif args.command == 'get':
            canva.get_design(design_id=args.design_id)

        elif args.command == 'export':
            canva.export_design(
                design_id=args.design_id,
                format=args.format,
                output_path=args.output
            )

        elif args.command == 'upload':
            canva.upload_asset(args.file)

        elif args.command == 'list':
            canva.list_designs(limit=args.limit)

        return 0

    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nTo use Canva API, you need to:")
        print("1. Go to: https://www.canva.com/developers/")
        print("2. Create a developer account")
        print("3. Create an app and get your API key")
        print("4. Add to .env file: CANVA_API_KEY=your_api_key_here")
        return 1

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

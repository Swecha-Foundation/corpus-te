import json
import requests
from typing import Dict
import os, dotenv
# Load environment variables from .env file
dotenv.load_dotenv()

# Configuration
API_BASE_URL = "https://backend2.swecha.org"  # Change this to your production URL
API_TOKEN = os.getenv("API_TOKEN")  # Replace with your actual token



def create_category(category_data: Dict, token: str) -> bool:
    """Create a single category using the API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}/api/v1/categories/"
    
    try:
        response = requests.post(url, json=category_data, headers=headers)
        
        if response.status_code == 201:
            print(f"✓ Successfully created category: {category_data['name']}")
            return True
        elif response.status_code == 400:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"✗ Failed to create category '{category_data['name']}': {error_detail}")
            return False
        else:
            print(f"✗ Failed to create category '{category_data['name']}': HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error creating category '{category_data['name']}': {e}")
        return False

def create_categories_from_json(json_file_path: str = None, categories_dict: Dict = None, token: str = None):
    """Create categories from JSON file or dictionary."""
    
    if not token:
        print("Error: No authentication token provided")
        return
    
    # Load categories data
    if json_file_path:
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            print(f"Error: File {json_file_path} not found")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file {json_file_path}")
            return
    elif categories_dict:
        data = categories_dict
    else:
        print("Error: No data source provided")
        return
    
    categories = data.get('categories', [])
    
    if not categories:
        print("No categories found in the data")
        return
    
    print(f"Creating {len(categories)} categories...")
    print("-" * 50)
    
    successful = 0
    failed = 0
    
    for category in categories:
        if create_category(category, token):
            successful += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"Summary: {successful} successful, {failed} failed")

def main():
    """Main function to run the script."""
    print("Category Creation Script")
    print("=" * 50)
    
    # Option 1: Use the embedded categories data
    # print("Using embedded categories data...")
    # create_categories_from_json(categories_dict=categories_data, token=API_TOKEN)
    
    # Option 2: Uncomment to use a JSON file instead
    print("Using categories from JSON file...")
    with open(os.path.join(os.path.dirname(__file__), 'categories.json'), 'r', encoding='utf-8') as file:
        categories_data = json.load(file)
        print(f"Loaded {len(categories_data['categories'])} categories from JSON file")
    create_categories_from_json(categories_dict=categories_data, token=API_TOKEN)

    # create_categories_from_json(json_file_path="categories.json", token=API_TOKEN)

if __name__ == "__main__":
    main()
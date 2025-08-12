#!/usr/bin/env python3
"""
Fix template filters to properly handle mixed data types
"""

def fix_template_filters():
    """Fix template filters to handle mixed valid/invalid data correctly"""
    
    # Read the current app file
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'r') as f:
        content = f.read()
    
    # New improved filter functions
    new_filters = '''# Custom Jinja2 filters for dictionary operations
@app.template_filter('dict_min')
def dict_min_filter(items, key):
    """Get minimum value from list of dictionaries by key"""
    if not items:
        return 0
    
    values = []
    for item in items:
        if key in item:
            try:
                values.append(float(item[key]))
            except (ValueError, TypeError):
                continue  # Skip invalid values
    
    return min(values) if values else 0

@app.template_filter('dict_max')
def dict_max_filter(items, key):
    """Get maximum value from list of dictionaries by key"""
    if not items:
        return 0
    
    values = []
    for item in items:
        if key in item:
            try:
                values.append(float(item[key]))
            except (ValueError, TypeError):
                continue  # Skip invalid values
    
    return max(values) if values else 0

@app.template_filter('dict_avg')
def dict_avg_filter(items, key):
    """Get average value from list of dictionaries by key"""
    if not items:
        return 0
    
    values = []
    for item in items:
        if key in item:
            try:
                values.append(float(item[key]))
            except (ValueError, TypeError):
                continue  # Skip invalid values
    
    return sum(values) / len(values) if values else 0

@app.template_filter('dict_sum')
def dict_sum_filter(items, key):
    """Get sum of values from list of dictionaries by key"""
    if not items:
        return 0
    
    values = []
    for item in items:
        if key in item:
            try:
                values.append(float(item[key]))
            except (ValueError, TypeError):
                continue  # Skip invalid values
    
    return sum(values) if values else 0'''
    
    # Find and replace the filter section
    import re
    
    # Pattern to match from the start of filters to the end of dict_sum
    pattern = r'# Custom Jinja2 filters for dictionary operations.*?@app\.template_filter\(\'dict_sum\'\)\ndef dict_sum_filter\(items, key\):.*?return 0'
    
    # Replace with new filters (handle the duplicate dict_sum issue)
    new_content = re.sub(pattern, new_filters, content, flags=re.DOTALL)
    
    # Remove any duplicate dict_sum filter that might remain
    duplicate_pattern = r'@app\.template_filter\(\'dict_sum\'\)\ndef dict_sum_filter\(items, key\):.*?return 0'
    matches = re.findall(duplicate_pattern, new_content, flags=re.DOTALL)
    
    if len(matches) > 1:
        # Remove the second occurrence
        new_content = re.sub(duplicate_pattern, '', new_content, count=1, flags=re.DOTALL)
    
    # Write back to file
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed template filters to properly handle mixed data types")

if __name__ == "__main__":
    fix_template_filters()

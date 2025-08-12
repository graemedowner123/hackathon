#!/usr/bin/env python3
"""
Fix remaining template filter issues
"""

def fix_template_filters():
    """Fix the remaining template filter issues"""
    
    # Read the current app file
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'r') as f:
        content = f.read()
    
    # Fix the dict_sum_filter
    old_sum_filter = '''@app.template_filter('dict_sum')
def dict_sum_filter(items, key):
    """Get sum of values from list of dictionaries by key"""
    if not items:
        return 0
    return sum(item[key] for item in items)'''
    
    new_sum_filter = '''@app.template_filter('dict_sum')
def dict_sum_filter(items, key):
    """Get sum of values from list of dictionaries by key"""
    if not items:
        return 0
    try:
        values = [float(item[key]) for item in items if key in item]
        return sum(values) if values else 0
    except (ValueError, TypeError, KeyError):
        return 0'''
    
    content = content.replace(old_sum_filter, new_sum_filter)
    
    # Also fix the dict_avg_filter division by zero issue
    old_avg_line = "        return 0 / len(items)"
    new_avg_line = "        return 0"
    
    content = content.replace(old_avg_line, new_avg_line)
    
    # Write back to file
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed remaining template filter issues")

if __name__ == "__main__":
    fix_template_filters()

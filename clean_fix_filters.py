#!/usr/bin/env python3
"""
Clean fix for template filters
"""

def clean_fix_filters():
    """Clean up and fix the template filters properly"""
    
    # Read the current app file
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'r') as f:
        content = f.read()
    
    # Find the corrupted section and replace it with clean filters
    lines = content.split('\n')
    
    # Find the start of the filter section
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if '# Custom Jinja2 filters for dictionary operations' in line:
            start_idx = i
        elif start_idx != -1 and '@login_manager.user_loader' in line:
            end_idx = i
            break
    
    if start_idx != -1 and end_idx != -1:
        # Replace the corrupted section with clean filters
        clean_filters = [
            '# Custom Jinja2 filters for dictionary operations',
            '@app.template_filter(\'dict_min\')',
            'def dict_min_filter(items, key):',
            '    """Get minimum value from list of dictionaries by key"""',
            '    if not items:',
            '        return 0',
            '    ',
            '    values = []',
            '    for item in items:',
            '        if key in item:',
            '            try:',
            '                values.append(float(item[key]))',
            '            except (ValueError, TypeError):',
            '                continue  # Skip invalid values',
            '    ',
            '    return min(values) if values else 0',
            '',
            '@app.template_filter(\'dict_max\')',
            'def dict_max_filter(items, key):',
            '    """Get maximum value from list of dictionaries by key"""',
            '    if not items:',
            '        return 0',
            '    ',
            '    values = []',
            '    for item in items:',
            '        if key in item:',
            '            try:',
            '                values.append(float(item[key]))',
            '            except (ValueError, TypeError):',
            '                continue  # Skip invalid values',
            '    ',
            '    return max(values) if values else 0',
            '',
            '@app.template_filter(\'dict_avg\')',
            'def dict_avg_filter(items, key):',
            '    """Get average value from list of dictionaries by key"""',
            '    if not items:',
            '        return 0',
            '    ',
            '    values = []',
            '    for item in items:',
            '        if key in item:',
            '            try:',
            '                values.append(float(item[key]))',
            '            except (ValueError, TypeError):',
            '                continue  # Skip invalid values',
            '    ',
            '    return sum(values) / len(values) if values else 0',
            '',
            '@app.template_filter(\'dict_sum\')',
            'def dict_sum_filter(items, key):',
            '    """Get sum of values from list of dictionaries by key"""',
            '    if not items:',
            '        return 0',
            '    ',
            '    values = []',
            '    for item in items:',
            '        if key in item:',
            '            try:',
            '                values.append(float(item[key]))',
            '            except (ValueError, TypeError):',
            '                continue  # Skip invalid values',
            '    ',
            '    return sum(values) if values else 0',
            ''
        ]
        
        # Replace the corrupted section
        new_lines = lines[:start_idx] + clean_filters + lines[end_idx:]
        new_content = '\n'.join(new_lines)
        
        # Write back to file
        with open('/home/graemedowner/hackathon/app_dynamodb.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Cleaned up and fixed template filters")
    else:
        print("❌ Could not find filter section to fix")

if __name__ == "__main__":
    clean_fix_filters()

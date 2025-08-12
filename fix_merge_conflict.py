#!/usr/bin/env python3
"""
Fix Git merge conflict in app_dynamodb.py
"""

def fix_merge_conflict():
    """Remove Git merge conflict markers and clean up the file"""
    
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'r') as f:
        content = f.read()
    
    # Remove Git merge conflict markers and clean up
    lines = content.split('\n')
    cleaned_lines = []
    skip_until_end = False
    
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            skip_until_end = True
            continue
        elif line.startswith('======='):
            continue
        elif line.startswith('>>>>>>> '):
            skip_until_end = False
            continue
        elif skip_until_end:
            continue
        else:
            cleaned_lines.append(line)
    
    # Join lines back together
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Remove any duplicate or orphaned code sections
    # Look for the dict_sum filter section and ensure it's clean
    import re
    
    # Find and fix any remaining issues with the dict_sum filter
    # Remove any orphaned code fragments
    cleaned_content = re.sub(r'\n\s*values = \[\]\s*\n\s*for item in items:\s*\n\s*if key in item:\s*\n.*?continue.*?\n.*?return sum.*?\n', '', cleaned_content, flags=re.DOTALL)
    
    # Write the cleaned content back
    with open('/home/graemedowner/hackathon/app_dynamodb.py', 'w') as f:
        f.write(cleaned_content)
    
    print("✅ Fixed Git merge conflict and cleaned up app_dynamodb.py")

if __name__ == "__main__":
    fix_merge_conflict()


import re
from typing import Optional


def validate_log_file(content: str) -> bool:

    if not content or len(content.strip()) == 0:
        return False
    
    # Check for logcat or not
    lines = content.split('\n')[:10]
    logcat_pattern = r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+[-\s]\d+.*?[VDIWEF][/\s]'
    
    for line in lines:
        if re.search(logcat_pattern, line):
            return True
    
    return False


def save_uploaded_file(uploaded_file, directory: str = "data/uploads") -> Optional[str]:

    import os
    
    try:
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

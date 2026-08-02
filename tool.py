import os
from ddgs import DDGS 
WORKSPACE_DIR = os.path.abspath("my_project_agent_files")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

def web_search(query: str) ->str:
    """Searches the web and returns result"""
    try:
        results = DDGS().text(query, max_results=1)
        return str(results)

    except Exception as e:
        return f"Error in searching: {str(e)}"

def calculator(expression: str) ->str:
    """Calculator"""
    valid_char = "0123456789+-*/.() "

    for c in expression:
        if c not in valid_char:
            print("Invalid charater found in expression")
            return "Error. Invalid charater found in expression"
    
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Math error: {str(e)}"

def file_action(action: str, filename: str, content: str = "") ->str:
    """Manages files in workspace. action can only be read or write"""
    target_path = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    if not target_path.startswith(os.path.join(WORKSPACE_DIR, '')):
        return "Error: You can only modify files inside the workspace"

    if action == "write":
        try:
            with open(target_path, "w") as f:
                f.write(content)
            return f"Successful: Wrote to {filename}"
        except Exception as e:
            print(f"Write error: {str(e)}")
            return f"Write error: {str(e)}"
    elif action == "read":
        if not os.path.exists(target_path):
            print(f"Error: {filename} file does not exist")
            return f"Error: {filename} file does not exist"
        try:
            with open(target_path, "r") as f:
                return f.read()
        except Exception as e:  
            print(f"Read error: {str(e)}")
            return f"Read error: {str(e)}"
    else:
        print("Error: Action must be 'read' or 'write' only")
        return "Error: Action must be 'read' or 'write' only"
import os
from google import genai
from google.genai import types
from tool import web_search, calculator, file_action 
import uuid
import sqlite3
from datetime import datetime

client = genai.Client()

TOOL_MAP = {
    "web_search": web_search,   
    "calculator": calculator,
    "file_action": file_action
}

def summarize_chat_history(client: genai.Client, current_chat_object: genai.chats.Chat, tool_list: list, run_id: str, step: int, user_prompt: str) -> genai.chats.Chat:
    if len(current_chat_object.get_history()) < 6:
        return current_chat_object
    
    first_dialogue=current_chat_object.get_history()[0]
    middle_dialogue=current_chat_object.get_history()[1:-2]
    last_dialogue=current_chat_object.get_history()[-2:]

    summary = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"You need to summarize this conversation so that it consumes less tokens when transferring. Don't lose important results/actions during summarization. The conversation to be summarized is: {str(middle_dialogue)}"
    )
    log_tokens(run_id, step, summary.usage_metadata.prompt_token_count, summary.usage_metadata.candidates_token_count, summary.usage_metadata.total_token_count)
    log_this_step(run_id, step, user_prompt, None, "Condense123", summary.text, None)
    
    new_history=[]
    new_history.append(first_dialogue)
    new_history.append(types.Content(role="model", parts=[types.Part.from_text(text=f"Summary of content: {summary.text}")]))
    new_history.extend(last_dialogue)
    
    new_chat = client.chats.create(
        model="gemini-2.5-flash",
        history=new_history,
        config=types.GenerateContentConfig(
            tools=tool_list,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.0
        )
    )
    return new_chat

# ---------------------------------------------------SQLite implementation----------------------------------------
db_file="agent_log.db"
def create_a_step_db():
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_work (
            run_id TEXT,
            step INTEGER,
            prompt TEXT,
            tool_name TEXT,
            tool_args TEXT,
            tool_output TEXT,
            final_ans TEXT,
            timestamp TEXT
        )
    """)
    connection.commit()
    connection.close()

def log_this_step(run_id: str, step: int, prompt: str, tool_name: str=None, tool_args: str=None, tool_output: str=None, final_ans: str=None):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO agent_work VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (run_id, step, prompt, tool_name, tool_args, tool_output, final_ans, datetime.now().isoformat()))
    connection.commit()
    connection.close()

def create_a_token_db():
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS token_ct (
            run_id TEXT,
            step INT,
            input_token INT,
            output_token INT,
            total_token INT
        )
        """
    )
    connection.commit()
    connection.close()

def log_tokens(curr_run_id: str, step: int, input_token: int, output_token: int, total_token: int):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO token_ct VALUES (?, ?, ?, ?, ?)", (curr_run_id, step, input_token, output_token, total_token))    
    connection.commit()
    connection.close()
    
#-------------------------------------------run agent function------------------------------------
def run_agent(user_prompt: str):
    curr_run_id = str(uuid.uuid4())
    try:
    
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                tools=[web_search, calculator, file_action],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                temperature=0.0
            )
        )
        response = chat.send_message(user_prompt)
        log_tokens(curr_run_id, 0, response.usage_metadata.prompt_token_count, response.usage_metadata.candidates_token_count, response.usage_metadata.total_token_count)

        step = 1
        already_asked = set()
        while response.function_calls:
        
            chat=summarize_chat_history(client, chat,[web_search, calculator, file_action], curr_run_id, step, user_prompt)
            tool_responses_together = []
            for call in response.function_calls:
                tool_name = call.name
                tool_args = call.args

                if (tool_name, str(tool_args)) in already_asked:
                    log_this_step(curr_run_id, step, user_prompt, tool_name, str(tool_args), "Already asked this", None)
                    tool_responses_together.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"tool response": "Already asked this"}
                        )
                    )
                    continue

                already_asked.add((tool_name, str(tool_args)))
            
                if tool_name in TOOL_MAP:
                    tool_output = TOOL_MAP[tool_name](**tool_args)
                    log_this_step(curr_run_id, step, user_prompt, tool_name, str(tool_args), tool_output, None)
                    tool_responses_together.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"tool response": tool_output}
                        )
                    )
                
                else:
                    print(f"Error: LLM gave an invalid tool name '{tool_name}'")
                    log_this_step(curr_run_id, step, user_prompt, tool_name, str(tool_args), "Invalid tool use", None)
                    tool_responses_together.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response={"tool response": "No such tools exits. Use only available tools"}
                        )
                    )
                    continue

            response = chat.send_message(tool_responses_together)
            log_tokens(curr_run_id, step, response.usage_metadata.prompt_token_count, response.usage_metadata.candidates_token_count, response.usage_metadata.total_token_count)
            step+=1

        log_this_step(curr_run_id, 100000, user_prompt, None, None, None, f"{response.text}")
        
    
    except Exception as e:
        log_this_step(curr_run_id, 10000, user_prompt, None, "An error occured", str(e), None)
        print(f"An error occured: {str(e)}")

if __name__ == "__main__":
    create_a_step_db()
    create_a_token_db()
    run_agent("In a file b.txt, write the answer to the question, 'what is the largest country by area in the world?'")
    # run_agent("What is the value of 1+2+3-9.")

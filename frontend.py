import streamlit as st
import sqlite3

db_file = "agent_log.db"

def get_all_runs():
    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()
        # Group by run_id to grab one clean entry per session trace
        cursor.execute("""
            SELECT run_id,
            MAX(prompt) as prompt,
            MIN(timestamp) as timestamp 
            FROM agent_work 
            GROUP BY run_id 
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        connection.close()
        return rows
    except sqlite3.OperationalError as e:
        print(f"{str(e)}")
        return []

def get_run_details(run_id):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT step, tool_name, tool_args, tool_output, final_ans, timestamp 
        FROM agent_work 
        WHERE run_id = ? 
        ORDER BY step ASC
        """, (run_id,))
    rows = cursor.fetchall()
    connection.close()
    return rows

def display_option_text(map :dict[str, str], x :str) ->str:
    return map[x]

def get_token_details(curr_run_id):
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT step, input_token, output_token, total_token
        FROM token_ct
        WHERE run_id = ?
        ORDER BY step ASC
        """, (curr_run_id,)
    )
    step_token_rows = cursor.fetchall()
    connection.close()
    return step_token_rows

#---------------------------------------------------------UI Part----------------------------------------------------------------
st.set_page_config(page_title="Gemini Agent Trace Logs", page_icon="🤖", layout="wide")

st.title("Gemini Agent Trace & Replay", text_alignment="center")
st.caption("Inspect tool evaluation sequences, intermediate arguments, and history condensation logs.", text_alignment="center")

# Load runs from the SQLite log matrix
all_runs = get_all_runs()

if not all_runs:
    st.info("No execution traces found yet. Run agent5.py script to populate the database!")
else:
    # Sidebar Configuration Selector
    st.sidebar.header("Choose a prompt you want to analyse")
    
    # Map out options nicely in the sidebar dropdown box
    run_options = {}
    for row in all_runs:
        run_options[row[0]]=f"{row[1][:50]}..."

    selected_run_id = st.sidebar.selectbox(
        "Use the dropdown menu below",
        options=list(run_options.keys()),
        format_func=lambda x: display_option_text(run_options, x)
    )   

    active_prompt = next(row[1] for row in all_runs if row[0] == selected_run_id)
    
    st.info(f"**User Prompt** `{active_prompt}`")
    st.subheader("Steps followed")

    steps = get_run_details(selected_run_id)

    for row in steps:
        step_num=row[0]
        tool_name=row[1]
        tool_args=row[2]
        tool_output=row[3]
        final_ans=row[4]
        timestamp=row[5]
        
        if final_ans is not None:
            st.success("### Final Answer")
            st.write(final_ans)
            st.caption(f"Timestamp: `{timestamp}`")
        elif tool_name == None and tool_args == "Condense123":
            with st.expander(f"**Step {step_num}: Call to `condense history`**", expanded=True):
                st.code(f"The history has been changed to:\n{tool_output}")
                st.caption(f"Timestamp: `{timestamp}`")
        elif tool_name == None and tool_args == "An error occured":
            st.error(f"An error occured\n`{tool_output}`")
            st.caption(f"Timestamp: `{timestamp}`")
        else:
            with st.expander(f"**Step {step_num}: Call to `{tool_name}`**", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Input to tool:**")
                    try:
                        st.json(tool_args)
                    except Exception:
                        st.code(tool_args)
                        
                with col2:
                    st.markdown("**Tool Response:**")
                    if "Already asked this" == str(tool_output):
                        st.warning(tool_output)
                    elif "Invalid tool use" == str(tool_output):
                        st.error(tool_output)
                    else:
                        st.code(tool_output)
                        
                st.caption(f"Timestamp: `{timestamp}`")

    token_use = get_token_details(selected_run_id)
    with st.expander("**Click to see token usage**", expanded=False):

        for token_row in token_use:  
            col1, col2, col3, col4 = st.columns(4)      
            with col1:
                st.metric(label="Step", value=token_row[0])
            with col2:
                st.metric(label="Input Tokens", value=token_row[1])
            with col3:
                st.metric(label="Output Tokens", value=token_row[2])
            with col4:
                st.metric(label="Total Combined", value=token_row[3])
            st.divider()

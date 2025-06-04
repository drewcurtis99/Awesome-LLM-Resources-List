from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from my_agent.utils.tools import all_tools
from langgraph.prebuilt import ToolNode
from datetime import datetime
from langchain_core.messages import SystemMessage

@lru_cache(maxsize=1)
def _get_model():
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")
    model = model.bind_tools(all_tools)
    return model

def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"

today = datetime.now().strftime("%Y-%m-%d")

system_prompt = f"""You are a thorough tech industry research assistant with access to these tools:

1. tech_trends_tool: Get trending technology keywords
2. tech_sources_tool: Find sources discussing specific keywords (use limit=10)

Today's date is {today}.

You should always do the following:

REQUIRED RESEARCH PROCESS - FOLLOW EVERY STEP:
1. FIRST: Use tech_trends_tool to identify relevant keywords
   - Choose an appropriate period (daily, weekly, monthly, quarterly)
   - Choose a category that is relevant to the user (investor may be interested in companies, ai, people, websites, subjects while a developer may be interested in frameworks, languages, tools, platforms, etc.)
   
2. SECOND: Use tech_sources_tool for EACH interesting keyword
   - ALWAYS use limit=10 to get diverse sources
   - CRITICAL: Use the SAME PERIOD parameter that you used in tech_trends_tool
   - Example: If you used period=\"weekly\" in tech_trends_tool, also use period=\"weekly\" in tech_sources_tool
   
3. FINALLY: Synthesize all findings into a comprehensive answer with source citations

DON'T SKIP STEPS - all research questions require using MULTIPLE tools in sequence.
DON'T provide final answers until you've completed the full research workflow.
ALWAYS match the period parameter between tech_trends_tool and tech_sources_tool.
"""

def call_model(state, config):
    """Call the Gemini model without forcing tool calls."""
    messages = state["messages"]
    # Add system message
    system_message = SystemMessage(content=system_prompt)
    full_messages = [system_message] + messages
    model = _get_model()
    try:
        response = model.invoke(full_messages)
        print(f"Model returned response of type: {type(response)}")
        if response:
            return {"messages": [response]}
        else:
            print("Trying again...")
            response = model.invoke(full_messages)
    except Exception as e:
        return {"messages": [{
            "role": "assistant",
            "content": f"I encountered an error while processing your request. Let me try a different approach. Error: {str(e)[:100]}"
        }]}

tool_node = ToolNode(all_tools)
from openai import OpenAI
from mcp.openai import create_tool_messages

# Create your tool schema to send to OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "make_ricker",
            "description": "Generate a Ricker wavelet",
            "parameters": {
                "type": "object",
                "properties": {
                    "frequency": {"type": "number"},
                    "dt": {"type": "number"},
                    "duration": {"type": "number"},
                },
                "required": ["frequency"],
            }
        }
    },
    # Add other tools similarly...
]

# Send user message
response = client.chat.completions.create(
    model="deepseek",
    messages=[
        {"role": "user", "content": "Generate a 30 Hz Ricker wavelet with 0.1 s duration"},
        *create_tool_messages(tools)
    ],
    tools=tools,
    tool_choice="auto",
)

# If tool is invoked, execute and feed result back to LLM
tool_call = response.choices[0].message.tool_calls[0]
tool_name = tool_call.function.name
tool_args = json.loads(tool_call.function.arguments)

# Execute tool
result = session.call_tool(tool_name, tool_args)

# Send result back to LLM
followup = client.chat.completions.create(
    model="deepseek",
    messages=[
        {"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": json.dumps(result)},
    ],
)

# run_server.py
from mcp import Tool, Session
from tools import make_ricker, compute_reflectivity

tools = [
    Tool(name="make_ricker", description="Generate a Ricker wavelet", func=make_ricker),
    Tool(name="compute_reflectivity", description="Compute 1D reflectivity series", func=compute_reflectivity),
]

session = Session(tools=tools)
session.run_stdio()

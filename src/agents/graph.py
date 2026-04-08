from common.supervisor import build_supervisor_graph

graph = None

def get_graph():
    global graph
    if graph is None:
        graph = build_supervisor_graph() # await init_graph()
    return graph

# async def init_graph():
#     checkpointer = await get_checkpointer()
#     return build_supervisor_graph(checkpointer=checkpointer)

# graph = None

# async def get_graph():
#     global graph
#     if graph is None:
#         graph = await build_supervisor_graph() # await init_graph()
    
#     return graph
from dotenv import load_dotenv
import os
from langchain_community.agent_toolkits.load_tools import load_tools
from smolagents import CodeAgent, Tool, InferenceClientModel

# Load environment variables from .env file
load_dotenv()

# Initialize the model
model = InferenceClientModel()

# Load the SerpAPI tool with the API key from environment
search_tool = Tool.from_langchain(load_tools(["serpapi"], serpapi_api_key=os.getenv("SERPAPI_API_KEY"))[0])

# Initialize the agent with the search tool and model
agent = CodeAgent(tools=[search_tool], model=model)

# Run the agent with your query
agent.run("Search for luxury entertainment ideas for a superhero-themed event, such as live performances and interactive experiences.")
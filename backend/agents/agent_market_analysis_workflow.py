from agent_market_analysis_graph import create_workflow_graph
from tools.states.agent_market_analysis_state import MarketAnalysisAgentState

if __name__ == '__main__':

    # Initial state for the workflow
    initial_state = MarketAnalysisAgentState(
        portfolio_allocation=[],  # Initialize as an empty list
        report={
            "asset_trends": [],  # Initialize as an empty list
            "macro_indicators": [],  # Initialize as an empty list
            "market_volatility_index": {},  # Initialize as an empty MarketVolatilityIndex
            "overall_diagnosis": None  # No diagnosis at the start
        }
    )
    
    # Create the workflow graph
    graph = create_workflow_graph()
    final_state = graph.invoke(input=initial_state)

    # Print the final state
    print("\nFinal State:")
    print(final_state)
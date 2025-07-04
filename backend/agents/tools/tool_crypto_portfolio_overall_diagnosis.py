from agents.tools.states.agent_crypto_analysis_state import CryptoAnalysisAgentState
from agents.tools.bedrock.anthropic_chat_completions import BedrockAnthropicChatCompletions
from agents.tools.agent_profiles import AgentProfiles
from agents.tools.risk_profiles import RiskProfiles
from typing import Optional
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CryptoPortfolioOverallDiagnosisTool:
    def __init__(self, chat_completions_model_id: Optional[str] = os.getenv("CHAT_COMPLETIONS_MODEL_ID"), agent_id: Optional[str] = "CRYPTO_ANALYSIS_AGENT"):
        """
        CryptoPortfolioOverallDiagnosisTool class to generate overall diagnosis for the crypto portfolio.
        This class uses the BedrockAnthropicChatCompletions model to generate a comprehensive diagnosis based on the crypto portfolio context.
        
        Args:
            chat_completions_model_id (str): Model ID for chat completions. Default is os.getenv("CHAT_COMPLETIONS_MODEL_ID").
            agent_id (str): Agent ID. Default is "CRYPTO_ANALYSIS_AGENT".
        """
        self.chat_completions_model_id = chat_completions_model_id
        self.agent_id = agent_id
        logger.info("CryptoPortfolioOverallDiagnosisTool initialized")

    def generate_overall_diagnosis(self, state: CryptoAnalysisAgentState) -> dict:
        """
        Generate the overall diagnosis for the crypto portfolio using the portfolio context and LLM.

        Args:
            state (CryptoAnalysisAgentState): The current state of the crypto analysis agent.

        Returns:
            dict: The overall diagnosis and updated state information.
        """
        logger.info("[Tool] Generate overall diagnosis for the crypto portfolio.")

        # Retrieve the active risk profile (fallback is handled internally in RiskProfiles)
        risk_profiles = RiskProfiles()
        active_risk_profile = risk_profiles.get_active_risk_profile()
        state.updates.append(
            f"[Action] Using risk profile: {active_risk_profile['risk_id']} - {active_risk_profile.get('short_description', 'No description')}"
        )

        # Retrieve the CRYPTO_ANALYSIS_AGENT profile
        profiler = AgentProfiles()
        agent_profile = profiler.get_agent_profile(self.agent_id)
        if not agent_profile:
            logger.error(f"Agent profile not found for agent ID: {self.agent_id}")
            state.updates.append("Unable to generate overall diagnosis due to missing agent profile.")
            return { "overall_diagnosis": "Error while retrieving agent profile!", "updates": state.updates, "next_step": state.next_step }
        else:
            # Log the agent profile
            state.updates.append(f"[Action] Using agent profile: {self.agent_id} - {agent_profile['role']}")

        # Extract crypto portfolio context from the state
        crypto_trends = state.report.crypto_trends
        crypto_momentum_indicators = state.report.crypto_momentum_indicators
        portfolio_allocation = {allocation.asset: allocation.description for allocation in state.portfolio_allocation}

        # Build the context for the LLM
        context_parts = []
        
        # Portfolio Allocation Summary
        context_parts.append("Crypto Portfolio Allocation:")
        total_crypto_allocation = 0
        total_stablecoin_allocation = 0
        for allocation in state.portfolio_allocation:
            percentage = float(allocation.allocation_percentage.replace('%', ''))
            if allocation.asset_type == "Cryptocurrency":
                total_crypto_allocation += percentage
            elif allocation.asset_type == "Stablecoin":
                total_stablecoin_allocation += percentage
            context_parts.append(f"- {allocation.asset} ({allocation.asset_type}): {allocation.allocation_percentage} - {allocation.description}")
        
        context_parts.append(f"Total Cryptocurrency exposure: {total_crypto_allocation}%")
        context_parts.append(f"Total Stablecoin exposure: {total_stablecoin_allocation}%")

        # Crypto Trends Analysis
        if crypto_trends:
            context_parts.append("\nCrypto Asset Trends Analysis:")
            for trend in crypto_trends:
                description = portfolio_allocation.get(trend.asset, "No description available")
                context_parts.append(f"- {trend.asset} ({description}): {trend.fluctuation_answer} Diagnosis: {trend.diagnosis}")

        # Crypto Momentum Indicators Analysis
        if crypto_momentum_indicators:
            context_parts.append("\nCrypto Momentum Indicators Analysis:")
            for crypto_momentum in crypto_momentum_indicators:
                context_parts.append(f"- {crypto_momentum.asset}:")
                for indicator in crypto_momentum.momentum_indicators:
                    context_parts.append(f"  * {indicator.indicator_name}: {indicator.fluctuation_answer} Diagnosis: {indicator.diagnosis}")

        portfolio_context = "\n".join(context_parts)

        # Generate the LLM prompt
        llm_prompt = (
            f"===== CRYPTO INVESTOR RISK PROFILE =====\n"
            f"Risk Profile ID      : {active_risk_profile['risk_id']}\n"
            f"Description          : {active_risk_profile.get('short_description', 'No description')}\n"
            f"========================================\n\n"
            f"Crypto Investment Agent Profile Details:\n"
            f"Role                 : {agent_profile['role']}\n"
            f"Kind of Data         : {agent_profile['kind_of_data']}\n"
            f"Instructions         : {agent_profile['instructions']}\n"
            f"Rules                : {agent_profile['rules']}\n\n"
            f"Crypto Portfolio Analysis Context:\n{portfolio_context}\n\n"
            f"Based on the above crypto portfolio analysis, provide a comprehensive overall diagnosis "
            f"that addresses portfolio diversification, risk exposure, trend momentum, and actionable "
            f"recommendations for crypto asset allocation adjustments. Consider both cryptocurrency "
            f"volatility and stablecoin stability in your assessment."
        )

        logger.info("LLM Prompt for Crypto Overall Diagnosis:")
        logger.info(llm_prompt)

        # Generate LLM response
        try:
            # Instantiate the chat completion model
            chat_completions = BedrockAnthropicChatCompletions(model_id=self.chat_completions_model_id)
            # Generate a comprehensive crypto portfolio diagnosis
            overall_diagnosis = chat_completions.predict(llm_prompt)
            # Log the LLM response
            if not overall_diagnosis:
                overall_diagnosis = "No crypto portfolio diagnosis generated."
            logger.info("LLM Response for Crypto Overall Diagnosis:")
            logger.info(overall_diagnosis)
        except Exception as e:
            logger.error(f"Error generating crypto overall diagnosis: {e}")
            overall_diagnosis = "Unable to generate crypto portfolio diagnosis at this time."

        # Update the state with the overall diagnosis
        state.report.overall_diagnosis = overall_diagnosis
        state.updates.append("[Tool] Generated overall diagnosis for the crypto portfolio.")
        state.next_step = "__end__"
        
        return { "overall_diagnosis": overall_diagnosis, "updates": state.updates, "next_step": state.next_step }

# Initialize the CryptoPortfolioOverallDiagnosisTool
crypto_portfolio_overall_diagnosis_tool = CryptoPortfolioOverallDiagnosisTool()

# Define tools
def generate_overall_diagnosis_tool(state: CryptoAnalysisAgentState) -> dict:
    """
    Generate the overall diagnosis for the crypto portfolio and update the state.

    Args:
        state (CryptoAnalysisAgentState): The current state of the crypto analysis agent.

    Returns:
        dict: The overall diagnosis and updated state information.
    """
    return crypto_portfolio_overall_diagnosis_tool.generate_overall_diagnosis(state=state)

if __name__ == "__main__":
    from states.agent_crypto_analysis_state import CryptoAnalysisAgentState, PortfolioAllocation, CryptoAssetTrend, MomentumIndicator, CryptoMomentumIndicator

    # Example usage with realistic crypto portfolio context
    state = CryptoAnalysisAgentState(
        portfolio_allocation=[
            PortfolioAllocation(asset="BTC", asset_type="Cryptocurrency", description="Bitcoin", allocation_percentage="45%"),
            PortfolioAllocation(asset="ETH", asset_type="Cryptocurrency", description="Ethereum", allocation_percentage="20%"),
            PortfolioAllocation(asset="FDUSD", asset_type="Stablecoin", description="First Digital USD", allocation_percentage="10%"),
            PortfolioAllocation(asset="USDC", asset_type="Stablecoin", description="USD Coin", allocation_percentage="5%"),
        ],
        report={
            "crypto_trends": [
                CryptoAssetTrend(asset="BTC", fluctuation_answer="BTC close price is $108,849.60, MA10 is $108,810.78, and MA20 is $108,797.01.", diagnosis="Bullish trend confirmed. 2025-07-02 close price above both Moving Averages (MA10 and MA20)."),
                CryptoAssetTrend(asset="ETH", fluctuation_answer="ETH close price is $2,650.45, MA10 is $2,620.33, and MA20 is $2,590.12.", diagnosis="Strong bullish momentum. 2025-07-02 close price 2.1% above MA10. Consider profit-taking."),
            ],
            "crypto_momentum_indicators": [
                CryptoMomentumIndicator(asset="BTC", momentum_indicators=[
                    MomentumIndicator(indicator_name="RSI", fluctuation_answer="BTC RSI (14-day) is 47.43 on 2025-07-03.", diagnosis="RSI at 47.43 shows bearish momentum. Downward pressure may persist."),
                    MomentumIndicator(indicator_name="Volume", fluctuation_answer="BTC volume is 3.49 vs 20-day avg of 2.81 on 2025-07-03.", diagnosis="Normal volume levels (1.2x average). Standard trading activity.")
                ]),
                CryptoMomentumIndicator(asset="ETH", momentum_indicators=[
                    MomentumIndicator(indicator_name="RSI", fluctuation_answer="ETH RSI (14-day) is 62.85 on 2025-07-03.", diagnosis="RSI at 62.85 shows bullish momentum. Upward price pressure likely to continue."),
                    MomentumIndicator(indicator_name="Volume", fluctuation_answer="ETH volume is 217.84 vs 20-day avg of 81.09 on 2025-07-03.", diagnosis="Exceptionally high volume (2.7x average). Strong conviction in price movement.")
                ])
            ],
            "overall_diagnosis": None,
        },
        updates=["[Tool] Calculate crypto trends.", "[Tool] Calculate crypto momentum indicators."]
    )

    # Use the tool to generate the overall diagnosis
    overall_diagnosis = generate_overall_diagnosis_tool(state)

    # Print the updated state
    print("\nUpdated Crypto State:")
    print(state.model_dump_json(indent=4))

    # Print the overall diagnosis
    print("\nCrypto Overall Diagnosis:")
    print(overall_diagnosis)
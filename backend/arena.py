"""
Debate Arena Module - Orchestrates multi-agent debates
"""
import ollama
from typing import Generator
from agents import Agent, get_template_agent


class DebateArena:
    """Orchestrates a debate between multiple AI agents."""
    
    def __init__(self, topic: str, rounds: int = 3):
        """
        Initialize a debate arena.
        
        Args:
            topic: The topic to debate
            rounds: Number of debate rounds (each agent speaks once per round)
        """
        self.topic = topic
        self.rounds = rounds
        self.agents: list[Agent] = []
        self.history: list[dict] = []
        self.is_running = False
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the debate."""
        self.agents.append(agent)
    
    def add_agents(self, agents: list[Agent]) -> None:
        """Add multiple agents to the debate."""
        self.agents.extend(agents)
    
    def run_debate(self) -> Generator[dict, None, None]:
        """
        Run the debate and yield each argument as it's generated.
        
        Yields:
            Dictionary containing round number, agent info, and their argument
        """
        if len(self.agents) < 2:
            yield {
                "type": "error",
                "message": "Need at least 2 agents for a debate"
            }
            return
        
        self.is_running = True
        self.history = []
        
        # Announce debate start
        yield {
            "type": "start",
            "topic": self.topic,
            "agents": [a.to_dict() for a in self.agents],
            "rounds": self.rounds
        }
        
        # Run each round
        for round_num in range(1, self.rounds + 1):
            yield {
                "type": "round_start",
                "round": round_num
            }
            
            for agent in self.agents:
                # Generate the agent's response
                message = agent.generate_response(
                    topic=self.topic,
                    debate_history=self.history,
                    round_num=round_num
                )
                
                # Create the entry
                entry = {
                    "type": "argument",
                    "round": round_num,
                    "agent": agent.name,
                    "role": agent.role,
                    "message": message
                }
                
                # Store in history
                self.history.append(entry)
                
                # Yield for real-time streaming
                yield entry
        
        # Generate final synthesis
        synthesis = self._generate_synthesis()
        yield {
            "type": "synthesis",
            "round": "final",
            "agent": "Moderator",
            "role": "Synthesis",
            "message": synthesis
        }
        
        # Announce debate end
        yield {
            "type": "end",
            "total_arguments": len(self.history)
        }
        
        self.is_running = False
    
    def _generate_synthesis(self) -> str:
        """Generate a synthesis of the debate."""
        
        # Format all arguments
        arguments_text = []
        for entry in self.history:
            arguments_text.append(
                f"**{entry['agent']}** ({entry['role']}, Round {entry['round']}): "
                f"{entry['message']}"
            )
        
        all_arguments = "\n\n".join(arguments_text)
        
        prompt = f"""You are a neutral moderator synthesizing a debate.

## Debate Topic
"{self.topic}"

## All Arguments
{all_arguments}

## Your Task
Provide a balanced synthesis of this debate. Include:

1. **Points of Agreement**: What did the debaters agree on?
2. **Points of Contention**: What remains disputed?
3. **Key Insights**: What were the strongest arguments made?
4. **Conclusion**: Based on the debate, what's the most reasonable position?
5. **Confidence**: How much consensus was reached? (Low/Medium/High)

Be concise but thorough. Around 150 words."""

        try:
            response = ollama.chat(
                model='llama3.2:3b',
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.5}
            )
            return response['message']['content'].strip()
        except Exception as e:
            return f"[Error generating synthesis: {str(e)}]"
    
    def get_history(self) -> list[dict]:
        """Get the full debate history."""
        return self.history.copy()
    
    def reset(self) -> None:
        """Reset the arena for a new debate."""
        self.history = []
        self.is_running = False


def create_default_debate(topic: str, rounds: int = 2) -> DebateArena:
    """
    Create a debate with default agents (Optimist, Skeptic, Pragmatist).
    
    Args:
        topic: The debate topic
        rounds: Number of rounds
        
    Returns:
        Configured DebateArena ready to run
    """
    arena = DebateArena(topic=topic, rounds=rounds)
    
    arena.add_agents([
        get_template_agent("optimist"),
        get_template_agent("skeptic"),
        get_template_agent("pragmatist"),
    ])
    
    return arena


def create_custom_debate(
    topic: str,
    agent_templates: list[str],
    rounds: int = 2
) -> DebateArena:
    """
    Create a debate with specified agent templates.
    
    Args:
        topic: The debate topic
        agent_templates: List of template names ("optimist", "skeptic", etc.)
        rounds: Number of rounds
        
    Returns:
        Configured DebateArena ready to run
    """
    arena = DebateArena(topic=topic, rounds=rounds)
    
    for template_name in agent_templates:
        arena.add_agent(get_template_agent(template_name))
    
    return arena


# Quick test
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎭 AI DEBATE ARENA - Test Run")
    print("=" * 60)
    
    # Create a debate
    arena = create_default_debate(
        topic="Should developers use AI coding assistants, or does it make them worse programmers?",
        rounds=2
    )
    
    print(f"\n📋 Topic: {arena.topic}")
    print(f"👥 Agents: {', '.join(a.name for a in arena.agents)}")
    print(f"🔄 Rounds: {arena.rounds}")
    print("\n" + "-" * 60 + "\n")
    
    # Run the debate
    for entry in arena.run_debate():
        if entry["type"] == "argument":
            print(f"[Round {entry['round']}] {entry['agent']} ({entry['role']}):")
            print(f"{entry['message']}\n")
            print("-" * 40 + "\n")
        elif entry["type"] == "synthesis":
            print("=" * 60)
            print("📊 SYNTHESIS")
            print("=" * 60)
            print(entry['message'])
            print()


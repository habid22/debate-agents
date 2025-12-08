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
        
        Structure:
        1. Opening Statements (Round 1)
        2. Rebuttals (Rounds 2 to N)
        3. Cross-Examination
        4. Closing Statements
        5. Voting
        6. Synthesis
        
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
        
        # ========== PHASE 1: OPENING STATEMENTS & REBUTTALS ==========
        for round_num in range(1, self.rounds + 1):
            phase_name = "Opening Statements" if round_num == 1 else f"Rebuttal Round {round_num - 1}"
            yield {
                "type": "round_start",
                "round": round_num,
                "phase": phase_name
            }
            
            for agent in self.agents:
                message = agent.generate_response(
                    topic=self.topic,
                    debate_history=self.history,
                    round_num=round_num
                )
                
                entry = {
                    "type": "argument",
                    "round": round_num,
                    "phase": phase_name,
                    "agent": agent.name,
                    "role": agent.role,
                    "message": message
                }
                
                self.history.append(entry)
                yield entry
        
        # ========== PHASE 2: CROSS-EXAMINATION ==========
        yield {
            "type": "cross_exam_start",
            "message": "Cross-Examination: Each debater will ask a pointed question to challenge an opponent."
        }
        
        cross_exam_entries = self._run_cross_examination()
        for entry in cross_exam_entries:
            self.history.append(entry)
            yield entry
        
        # ========== PHASE 3: CLOSING STATEMENTS ==========
        yield {
            "type": "closing_start",
            "message": "Closing Statements: Each debater makes their final argument."
        }
        
        for agent in self.agents:
            closing = agent.generate_closing_statement(
                topic=self.topic,
                debate_history=self.history
            )
            
            entry = {
                "type": "closing",
                "agent": agent.name,
                "role": agent.role,
                "message": closing
            }
            
            self.history.append(entry)
            yield entry
        
        # ========== PHASE 4: VOTING ==========
        yield {
            "type": "voting_start",
            "message": "Voting: Each debater votes for the most compelling argument."
        }
        
        votes = self._run_voting_round()
        for vote_entry in votes:
            yield vote_entry
        
        # Tally and announce results
        vote_tally = self._tally_votes(votes)
        yield {
            "type": "voting_results",
            "tally": vote_tally,
            "message": self._format_voting_results(vote_tally)
        }
        
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
    
    def _run_cross_examination(self) -> list:
        """Run cross-examination where each agent questions another."""
        entries = []
        agent_names = [agent.name for agent in self.agents]
        
        # Each agent picks someone to question (rotate through opponents)
        for i, questioner in enumerate(self.agents):
            # Pick the next agent in rotation (not themselves)
            target_idx = (i + 1) % len(self.agents)
            target = self.agents[target_idx]
            
            # Generate the question
            question = questioner.generate_cross_examination(
                topic=self.topic,
                debate_history=self.history,
                target_agent=target.name
            )
            
            question_entry = {
                "type": "cross_exam_question",
                "questioner": questioner.name,
                "target": target.name,
                "message": question
            }
            entries.append(question_entry)
            
            # Generate the response
            response = target.generate_cross_exam_response(
                topic=self.topic,
                debate_history=self.history,
                questioner=questioner.name,
                question=question
            )
            
            response_entry = {
                "type": "cross_exam_response",
                "responder": target.name,
                "questioner": questioner.name,
                "message": response
            }
            entries.append(response_entry)
        
        return entries
    
    def _run_voting_round(self) -> list:
        """Run a voting round where each agent votes for the most compelling argument."""
        votes = []
        agent_names = [agent.name for agent in self.agents]
        
        for agent in self.agents:
            vote_result = agent.generate_vote(
                topic=self.topic,
                debate_history=self.history,
                other_agents=agent_names
            )
            
            vote_entry = {
                "type": "vote",
                "voter": vote_result['voter'],
                "vote_for": vote_result['vote'],
                "reason": vote_result['reason']
            }
            votes.append(vote_entry)
        
        return votes
    
    def _tally_votes(self, votes: list) -> dict:
        """Tally the votes and return counts."""
        tally = {}
        for vote in votes:
            vote_for = vote.get('vote_for')
            if vote_for:
                tally[vote_for] = tally.get(vote_for, 0) + 1
        return tally
    
    def _format_voting_results(self, tally: dict) -> str:
        """Format voting results as a readable message."""
        if not tally:
            return "No votes were cast."
        
        # Sort by vote count
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)
        
        # Find winner(s)
        max_votes = sorted_results[0][1]
        winners = [name for name, count in sorted_results if count == max_votes]
        
        # Build message
        lines = ["**Voting Results:**"]
        for name, count in sorted_results:
            vote_word = "vote" if count == 1 else "votes"
            lines.append(f"- {name}: {count} {vote_word}")
        
        if len(winners) == 1:
            lines.append(f"\n**Winner:** {winners[0]} received the most votes!")
        else:
            lines.append(f"\n**Tie:** {' and '.join(winners)} tied for the most votes!")
        
        return "\n".join(lines)
    
    def _generate_synthesis(self) -> str:
        """Generate a synthesis of the debate."""
        
        # Format all arguments
        arguments_text = []
        for entry in self.history:
            entry_type = entry.get('type', 'argument')
            
            if entry_type == 'cross_exam_question':
                arguments_text.append(
                    f"**{entry['questioner']}** (Question to {entry['target']}): {entry['message']}"
                )
            elif entry_type == 'cross_exam_response':
                arguments_text.append(
                    f"**{entry['responder']}** (Response): {entry['message']}"
                )
            elif entry_type == 'closing':
                arguments_text.append(
                    f"**{entry['agent']}** (Closing Statement): {entry['message']}"
                )
            elif 'agent' in entry:
                round_info = f", Round {entry.get('round', '?')}" if 'round' in entry else ""
                arguments_text.append(
                    f"**{entry['agent']}** ({entry.get('role', 'Debater')}{round_info}): "
                    f"{entry['message']}"
                )
        
        all_arguments = "\n\n".join(arguments_text)
        
        prompt = f"""You are a neutral moderator synthesizing a debate.

## Debate Topic
"{self.topic}"

## All Arguments
{all_arguments}

## Your Task
Provide a balanced synthesis of this debate. You MUST format your response with these exact section headers (use bold markdown):

**Points of Agreement**: What did the debaters agree on?

**Points of Contention**: What remains disputed?

**Key Insights**: What were the strongest arguments made?

**Conclusion**: Based on the debate, what's the most reasonable position?

**Confidence**: How much consensus was reached? (Low/Medium/High)

IMPORTANT FORMATTING RULES:
- Use EXACTLY these section names with **bold** formatting
- Do NOT use numbered lists (1., 2., 3.) before section headers
- Each section should have a few sentences or bullet points
- Be concise but thorough. Around 150 words total.
- NO emojis or emoticons
- Write in a neutral, analytical tone"""

        try:
            response = ollama.chat(
                model='mistral:7b',
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


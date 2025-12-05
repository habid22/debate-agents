"""
Agent Module - Individual AI agents with unique personalities
"""
import re
import ollama


class Agent:
    """An AI agent with a unique personality that participates in debates."""
    
    def __init__(self, name: str, role: str, personality: str, stance: str = "neutral"):
        """
        Initialize an agent.
        
        Args:
            name: Agent's display name
            role: Agent's role/title (e.g., "Startup Founder", "Senior Engineer")
            personality: Description of how the agent thinks and argues
            stance: Initial stance on topics ("pro", "con", "neutral")
        """
        self.name = name
        self.role = role
        self.personality = personality
        self.stance = stance
        self.model = "mistral:7b"  # Default model, can be changed
    
    def generate_response(self, topic: str, debate_history: list, round_num: int) -> str:
        """
        Generate this agent's argument based on the debate context.
        
        Args:
            topic: The debate topic
            debate_history: List of previous arguments in the debate
            round_num: Current round number
            
        Returns:
            The agent's argument as a string
        """
        # Format the debate history for context
        history_text = self._format_history(debate_history)
        
        # Build the prompt
        prompt = self._build_prompt(topic, history_text, round_num)
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.8,  # Some creativity
                    'top_p': 0.9,
                }
            )
            return response['message']['content'].strip()
        except Exception as e:
            return f"[Error generating response: {str(e)}]"
    
    def _format_history(self, debate_history: list) -> str:
        """Format debate history into readable text."""
        if not debate_history:
            return "(No previous arguments - you are speaking first)"
        
        formatted = []
        for entry in debate_history:
            formatted.append(f"**{entry['agent']}** ({entry['role']}): {entry['message']}")
        
        return "\n\n".join(formatted)
    
    def _build_prompt(self, topic: str, history_text: str, round_num: int) -> str:
        """Build the prompt for the LLM."""
        
        if round_num == 1:
            return f"""You are {self.name}, a {self.role}.

## Your Personality & Speaking Style
{self.personality}

## Debate Topic
"{topic}"

## Context
You are in a private, casual debate with other philosophers. Speak naturally and directly.

## Your Task
Give your opening argument. Speak in {self.name}'s authentic voice - their way of reasoning, their philosophical approach.

CRITICAL RULES:
- Speak in {self.name}'s authentic voice and style
- Take a clear stance that reflects your philosophy
- Use a specific example
- Keep it under 100 words
- Be DIRECT - get to your point quickly

AVOID THESE REPETITIVE PHRASES:
- "My esteemed colleague(s)"
- "Esteemed colleagues"
- "Gentlemen"
- "Let us embark on a philosophical journey"
- "In this contemplation"
- "I propose we reconsider"
- Any flowery, overly formal openings

Just speak naturally and make your argument. Start with your actual point, not formal pleasantries.

## Your Opening Argument:"""
        else:
            return f"""You are {self.name}, a {self.role}.

## Your Personality & Speaking Style
{self.personality}

## Debate Topic
"{topic}"

## Previous Arguments
{history_text}

## Context
You are in a casual debate with other philosophers. Speak naturally and directly to them.

## Your Task
Respond to one of the philosophers above. Challenge their argument or build on it.

CRITICAL RULES:
- Address the philosopher by name (e.g., "Kant, your argument fails because..." or "Mill overlooks...")
- Pick ONE person to respond to (NOT yourself - you are {self.name})
- Reference something specific they said
- Speak in {self.name}'s authentic voice
- Keep it under 100 words
- Be DIRECT - challenge or engage immediately

AVOID THESE REPETITIVE PHRASES:
- "My esteemed colleague"
- "I must challenge your claim"
- "While I acknowledge"
- "Let us continue our dialogue"
- Any flowery, overly formal language

Just speak naturally. Start with your actual disagreement or point, not formal pleasantries.

## Your Rebuttal:"""
    
    def generate_vote(self, topic: str, debate_history: list, other_agents: list) -> dict:
        """
        Generate this agent's vote for the most compelling argument.
        
        Args:
            topic: The debate topic
            debate_history: List of all arguments in the debate
            other_agents: List of other agent names (cannot vote for self)
            
        Returns:
            Dict with 'vote' (agent name) and 'reason' (brief explanation)
        """
        # Format debate for context
        history_text = self._format_history(debate_history)
        other_names = [name for name in other_agents if name != self.name]
        
        prompt = f"""You are {self.name}. The debate is over. Vote for ONE philosopher whose argument was most compelling.

AVAILABLE CHOICES: {', '.join(other_names)}
(You cannot vote for yourself)

THE DEBATE:
{history_text}

YOUR TASK: Pick who made the best argument and explain why in 2-3 sentences. Reference something SPECIFIC they said.

YOU MUST RESPOND IN THIS EXACT FORMAT:
VOTE: [pick one name from the list above]
REASON: [2-3 sentences about WHY - mention a specific argument they made]

DO NOT write anything else. Just VOTE and REASON."""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.5}
            )
            content = response['message']['content'].strip()
            
            # Parse the response - try multiple approaches
            vote = None
            reason = ""
            
            # Try to find VOTE
            vote_match = re.search(r'VOTE:\s*(\w+)', content, re.IGNORECASE)
            if vote_match:
                vote_text = vote_match.group(1).strip()
                for name in other_names:
                    if name.lower() == vote_text.lower():
                        vote = name
                        break
            
            # Try to find REASON
            reason_match = re.search(r'REASON:\s*(.+?)(?=\n\n|$)', content, re.IGNORECASE | re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
                # Clean up the reason - remove extra whitespace
                reason = ' '.join(reason.split())
            
            # Approach 2: If VOTE not found, look for any name mentioned prominently
            if not vote:
                # Check if content starts with a name
                for name in other_names:
                    if content.lower().startswith(name.lower()) or f"vote for {name.lower()}" in content.lower():
                        vote = name
                        break
            
            # Approach 3: Find any name in the content
            if not vote:
                for name in other_names:
                    if name.lower() in content.lower():
                        vote = name
                        break
            
            # If we have a vote but no reason, extract text after the name as reason
            if vote and not reason:
                # Try to get any text after REASON: or after the vote
                remaining = content
                if 'REASON:' in content.upper():
                    remaining = content.upper().split('REASON:', 1)[1] if 'REASON:' in content.upper() else content
                    remaining = content[content.upper().find('REASON:') + 7:].strip()
                elif vote in content:
                    remaining = content.split(vote, 1)[1] if vote in content else content
                reason = remaining.strip()[:300] if remaining else ""  # Cap at 300 chars
            
            # Final fallback
            if not vote and other_names:
                vote = other_names[0]
                reason = f"Their philosophical approach offered valuable insights on this topic."
            
            # Clean reason of any formatting artifacts
            reason = reason.replace('**', '').replace('*', '').strip()
            if not reason or len(reason) < 10:
                reason = f"Their argument presented a compelling case that challenged my perspective."
            
            return {
                'voter': self.name,
                'vote': vote,
                'reason': reason
            }
            
        except Exception as e:
            # Return a default vote on error
            return {
                'voter': self.name,
                'vote': other_names[0] if other_names else None,
                'reason': f"Error generating vote: {str(e)}"
            }
    
    def to_dict(self) -> dict:
        """Convert agent to dictionary for serialization."""
        return {
            "name": self.name,
            "role": self.role,
            "personality": self.personality,
            "stance": self.stance
        }


# Pre-built agent templates for common debate scenarios
AGENT_TEMPLATES = {
    "optimist": Agent(
        name="Alex",
        role="The Optimist",
        personality="You see opportunities everywhere. You focus on potential benefits, "
                   "growth possibilities, and positive outcomes. You believe in taking "
                   "calculated risks and moving fast. You're enthusiastic but not naive.",
        stance="pro"
    ),
    "skeptic": Agent(
        name="Morgan",
        role="The Skeptic", 
        personality="You question everything. You focus on risks, hidden costs, and "
                   "potential failures. You've seen many ideas fail and want to prevent "
                   "mistakes. You're not negative, just cautious and thorough.",
        stance="con"
    ),
    "pragmatist": Agent(
        name="Jordan",
        role="The Pragmatist",
        personality="You balance idealism with reality. You focus on what actually works "
                   "in practice, considering context and tradeoffs. You often find middle "
                   "ground and practical compromises. You value data over opinions.",
        stance="neutral"
    ),
    "innovator": Agent(
        name="Sam",
        role="The Innovator",
        personality="You challenge conventional wisdom. You ask 'why not?' and explore "
                   "unconventional solutions. You're excited by new approaches but also "
                   "understand the value of proven methods when appropriate.",
        stance="neutral"
    ),
    "veteran": Agent(
        name="Casey",
        role="The Veteran",
        personality="You have years of experience and have seen trends come and go. "
                   "You value lessons learned from past failures and successes. You're "
                   "wary of hype but open to genuine improvements.",
        stance="neutral"
    ),
    "devils_advocate": Agent(
        name="Riley",
        role="Devil's Advocate",
        personality="Your job is to challenge whatever position seems dominant. If everyone "
                   "agrees, you find counterarguments. You strengthen debates by ensuring "
                   "all sides are properly tested. You're not contrarian for fun - you "
                   "genuinely want to stress-test ideas.",
        stance="con"
    ),
    # Ethical Philosophers
    "kant": Agent(
        name="Kant",
        role="Philosopher",
        personality="You are Immanuel Kant. You believe in the categorical imperative - act only according to "
                   "rules you could will to be universal laws. Never treat people merely as means to an end. "
                   "Duty and moral law matter more than consequences. You're systematic, rigorous, and believe "
                   "in rational autonomy. Reason is the supreme authority. The rightness of an action depends "
                   "on the principle behind it, not its outcomes. "
                   "SPEAKING STYLE: You speak in a systematic, methodical way. You use precise language and "
                   "build arguments step-by-step. You're formal but clear, like a German academic. You reference "
                   "universal principles and moral law. You don't use casual language - you speak with intellectual rigor.",
        stance="neutral"
    ),
    "mill": Agent(
        name="Mill",
        role="Philosopher",
        personality="You are John Stuart Mill. You are a utilitarian - the right action is that which produces "
                   "the greatest happiness for the greatest number. You believe in maximizing overall well-being "
                   "and minimizing suffering. Quality of pleasure matters, not just quantity. You value individual "
                   "liberty but within the framework of harm prevention. Consequences determine morality. "
                   "SPEAKING STYLE: You speak clearly and persuasively, like a 19th-century English intellectual. "
                   "You use practical examples and consider real-world consequences. You're thoughtful and measured, "
                   "but accessible. You appeal to reason and human welfare.",
        stance="neutral"
    ),
    "aristotle": Agent(
        name="Aristotle",
        role="Philosopher",
        personality="You are Aristotle. You believe in virtue ethics - moral character and virtue matter more "
                   "than rules or consequences. The Golden Mean: virtue lies between extremes. You emphasize "
                   "practical wisdom (phronesis), logic, and empirical observation. Happiness (eudaimonia) comes "
                   "from living virtuously and fulfilling one's purpose (telos). Character and habits shape morality. "
                   "SPEAKING STYLE: You speak like an ancient Greek philosopher - methodical, logical, and grounded. "
                   "You use examples from nature and human experience. You reference the Golden Mean, virtue, and "
                   "practical wisdom. You speak with the authority of someone who has observed human nature deeply. "
                   "You're not flowery - you're direct and wise, like a teacher explaining fundamental truths.",
        stance="neutral"
    ),
    "rawls": Agent(
        name="Rawls",
        role="Philosopher",
        personality="You are John Rawls. You believe in justice as fairness. Behind the 'veil of ignorance' - "
                   "not knowing your position in society - you would choose principles ensuring equal basic "
                   "liberties and fair equality of opportunity. The difference principle: inequalities are only "
                   "just if they benefit the least advantaged. Justice requires fairness, not just utility. "
                   "SPEAKING STYLE: You speak like a 20th-century American political philosopher - careful, "
                   "analytical, and concerned with fairness. You use thought experiments (like the veil of ignorance) "
                   "and systematic reasoning. You're precise and thoughtful, like a professor explaining justice theory.",
        stance="neutral"
    ),
    "socrates": Agent(
        name="Socrates",
        role="Philosopher",
        personality="You are Socrates, the father of Western philosophy. You use the Socratic method - "
                   "asking probing questions to expose contradictions and lead others to truth. You claim "
                   "to know nothing, yet your questions reveal deep wisdom. You believe virtue is knowledge "
                   "and that the unexamined life is not worth living. Challenge assumptions through questions. "
                   "Explore ethical concepts by examining what they truly mean. "
                   "SPEAKING STYLE: You speak like the ancient Greek Socrates - you ask questions, probe assumptions, "
                   "and expose contradictions. You might say 'What do you mean by...?' or 'But consider this...' "
                   "You're humble ('I know nothing') but your questions reveal deep insight. You speak conversationally, "
                   "like you're in a dialogue, not giving a lecture.",
        stance="neutral"
    ),
    "nietzsche": Agent(
        name="Nietzsche",
        role="Philosopher",
        personality="You are Friedrich Nietzsche. You reject slave morality and conventional ethics. You celebrate "
                   "the will to power and believe in creating your own values rather than following the herd. "
                   "You're provocative, aphoristic, and challenge all established moral systems. 'God is dead' - "
                   "we must create meaning ourselves. Embrace life fully, become the Übermensch. Question everything, "
                   "especially moral certainties. Be bold and unapologetic. "
                   "SPEAKING STYLE: You speak like Nietzsche - provocative, bold, and aphoristic. You use striking "
                   "phrases and challenge conventional thinking. You're dramatic and unapologetic. You might say "
                   "'But what if...' or make bold declarations. You speak with intensity and conviction, like someone "
                   "who sees through illusions. You're not polite or measured - you're direct and challenging.",
        stance="con"
    )
}


def get_template_agent(template_name: str) -> Agent:
    """Get a pre-built agent from templates."""
    template = AGENT_TEMPLATES.get(template_name.lower())
    if template:
        # Return a new instance with the same properties
        return Agent(
            name=template.name,
            role=template.role,
            personality=template.personality,
            stance=template.stance
        )
    raise ValueError(f"Unknown template: {template_name}. Available: {list(AGENT_TEMPLATES.keys())}")


def create_custom_agent(name: str, role: str, personality: str, stance: str = "neutral") -> Agent:
    """Create a custom agent with specified properties."""
    return Agent(name=name, role=role, personality=personality, stance=stance)


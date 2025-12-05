"""
Agent Module - Individual AI agents with unique personalities
"""
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
        self.model = "llama3.2:3b"  # Default model, can be changed
    
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
            return f"""You are **{self.name}**, a {self.role}.

## Your Personality
{self.personality}

## Debate Topic
"{topic}"

## Opening Round
This is the opening round. Present your initial position clearly and boldly.

## Previous Arguments
{history_text}

## Your Task
Give your opening argument. You MUST:
1. Stay in character as {self.name}
2. Take a clear, strong stance on this topic
3. Use a specific example to support your position
4. Keep it under 100 words

DO NOT start your response with your own name or use **bold** markdown formatting.
Just give your argument directly.

## Your Opening Argument:"""
        else:
            return f"""You are **{self.name}**, a {self.role}.

## Your Personality
{self.personality}

## Debate Topic
"{topic}"

## Round {round_num} - REBUTTAL ROUND

## Previous Arguments
{history_text}

## CRITICAL INSTRUCTIONS
This is a REBUTTAL round. You MUST:
1. **NAME a specific person** you're responding to (e.g., "I disagree with Morgan's claim that...")
2. **QUOTE or reference their specific argument** that you're challenging
3. **EXPLAIN why they're wrong** or why your view is better
4. If you agree with someone, say so and BUILD on their point
5. Stay in character as {self.name}
6. Keep it under 100 words

DO NOT just repeat your position. ENGAGE with what others said.
DO NOT start your response with your own name or use **bold** markdown formatting.
DO NOT end with "Please respond" or ask others to reply.
Just give your argument directly.

## Your Rebuttal:"""
    
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
                   "on the principle behind it, not its outcomes.",
        stance="neutral"
    ),
    "mill": Agent(
        name="Mill",
        role="Philosopher",
        personality="You are John Stuart Mill. You are a utilitarian - the right action is that which produces "
                   "the greatest happiness for the greatest number. You believe in maximizing overall well-being "
                   "and minimizing suffering. Quality of pleasure matters, not just quantity. You value individual "
                   "liberty but within the framework of harm prevention. Consequences determine morality.",
        stance="neutral"
    ),
    "aristotle": Agent(
        name="Aristotle",
        role="Philosopher",
        personality="You are Aristotle. You believe in virtue ethics - moral character and virtue matter more "
                   "than rules or consequences. The Golden Mean: virtue lies between extremes. You emphasize "
                   "practical wisdom (phronesis), logic, and empirical observation. Happiness (eudaimonia) comes "
                   "from living virtuously and fulfilling one's purpose (telos). Character and habits shape morality.",
        stance="neutral"
    ),
    "rawls": Agent(
        name="Rawls",
        role="Philosopher",
        personality="You are John Rawls. You believe in justice as fairness. Behind the 'veil of ignorance' - "
                   "not knowing your position in society - you would choose principles ensuring equal basic "
                   "liberties and fair equality of opportunity. The difference principle: inequalities are only "
                   "just if they benefit the least advantaged. Justice requires fairness, not just utility.",
        stance="neutral"
    ),
    "socrates": Agent(
        name="Socrates",
        role="Philosopher",
        personality="You are Socrates, the father of Western philosophy. You use the Socratic method - "
                   "asking probing questions to expose contradictions and lead others to truth. You claim "
                   "to know nothing, yet your questions reveal deep wisdom. You believe virtue is knowledge "
                   "and that the unexamined life is not worth living. Challenge assumptions through questions. "
                   "Explore ethical concepts by examining what they truly mean.",
        stance="neutral"
    ),
    "nietzsche": Agent(
        name="Nietzsche",
        role="Philosopher",
        personality="You are Friedrich Nietzsche. You reject slave morality and conventional ethics. You celebrate "
                   "the will to power and believe in creating your own values rather than following the herd. "
                   "You're provocative, aphoristic, and challenge all established moral systems. 'God is dead' - "
                   "we must create meaning ourselves. Embrace life fully, become the Übermensch. Question everything, "
                   "especially moral certainties. Be bold and unapologetic.",
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


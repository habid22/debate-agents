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
        
        # Extract participants from debate history
        participants = self._extract_participants(debate_history)
        # Remove self from participants list
        other_participants = [p for p in participants if p != self.name]
        
        # Build the prompt
        prompt = self._build_prompt(topic, history_text, round_num, other_participants)
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.8,  # Some creativity
                    'top_p': 0.9,
                }
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            return result
        except Exception as e:
            return f"[Error generating response: {str(e)}]"
    
    def _format_history(self, debate_history: list) -> str:
        """Format debate history into readable text."""
        if not debate_history:
            return "(No previous arguments - you are speaking first)"
        
        formatted = []
        for entry in debate_history:
            entry_type = entry.get('type', 'argument')
            
            if entry_type == 'cross_exam_question':
                formatted.append(f"**{entry['questioner']}** (Question to {entry['target']}): {entry['message']}")
            elif entry_type == 'cross_exam_response':
                formatted.append(f"**{entry['responder']}** (Response to {entry['questioner']}): {entry['message']}")
            elif entry_type == 'closing':
                formatted.append(f"**{entry['agent']}** (Closing Statement): {entry['message']}")
            elif 'agent' in entry and 'role' in entry:
                formatted.append(f"**{entry['agent']}** ({entry['role']}): {entry['message']}")
            # Skip entries without proper fields (like phase announcements)
        
        return "\n\n".join(formatted)
    
    def _extract_participants(self, debate_history: list) -> list:
        """Extract unique participant names from debate history."""
        participants = set()
        for entry in debate_history:
            if 'agent' in entry:
                participants.add(entry['agent'])
            if 'questioner' in entry:
                participants.add(entry['questioner'])
            if 'responder' in entry:
                participants.add(entry['responder'])
            if 'target' in entry:
                participants.add(entry['target'])
        return list(participants)
    
    def _build_prompt(self, topic: str, history_text: str, round_num: int, participants: list = None) -> str:
        """Build the prompt for the LLM."""
        
        if round_num == 1:
            return f"""You are {self.name}, a {self.role}.

## Your Personality & Speaking Style
{self.personality}

## Debate Topic
"{topic}"

## Context
You are in a debate. Speak naturally and directly.

## Your Task
Give your opening argument from YOUR unique perspective as {self.name}.

CRITICAL RULES:
- Your argument must reflect YOUR unique worldview as {self.role}
- Use YOUR characteristic way of thinking - what makes YOU different from others?
- Pick a SPECIFIC angle that fits YOUR personality (not generic points anyone could make)
- Use a concrete example that YOU would use
- Keep it under 100 words
- Be DIRECT - get to your point quickly
- NO generic statements - make it distinctly YOUR take

AVOID:
- Generic arguments anyone could make
- Flowery, overly formal openings
- "My esteemed colleague(s)", "Gentlemen", "Let us embark..."
- Vague philosophical musings

FORMATTING:
- Do NOT wrap your response in quotation marks

## Your Opening Argument (make it uniquely {self.name}'s perspective):"""
        else:
            # Build participants string for the prompt
            participants_str = ", ".join(participants) if participants else "the other debaters"
            
            return f"""You are {self.name}, a {self.role}.

## Your Personality & Speaking Style
{self.personality}

## Debate Topic
"{topic}"

## Participants You Can Address
{participants_str}
(ONLY address people from this list. No one else exists in this debate.)

## What Has Already Been Said
{history_text}

## Your Task
Respond to ONE person above with a FRESH point that NO ONE has made yet.

CRITICAL RULES - READ CAREFULLY:
1. DO NOT repeat any point already made above - bring something NEW
2. DO NOT make the same criticism someone else already made
3. Pick a DIFFERENT angle that reflects YOUR unique perspective as {self.role}
4. Address ONE person by name: {participants_str}
5. Challenge something SPECIFIC they said
6. Keep it under 100 words

WHAT MAKES YOU UNIQUE:
- You are {self.name}, {self.role}
- Your personality: Think about what YOU specifically would notice that others wouldn't
- What's YOUR unique take that no one else in this debate would have?

AVOID:
- Repeating points others already made (READ THE PREVIOUS ARGUMENTS)
- Starting with "{participants[0] if participants else 'Name'}, your optimism..." if someone already said that
- Generic criticisms - be SPECIFIC and ORIGINAL
- Flowery language, "my esteemed colleague", etc.

FORMATTING:
- Do NOT wrap your response in quotation marks

## Your Response (must be DIFFERENT from what others said):"""
    
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
    
    def generate_cross_examination(self, topic: str, debate_history: list, target_agent: str) -> str:
        """
        Generate a pointed question to challenge a specific opponent.
        
        Args:
            topic: The debate topic
            debate_history: List of all arguments in the debate
            target_agent: The agent to question
            
        Returns:
            A challenging question for the target agent
        """
        history_text = self._format_history(debate_history)
        
        prompt = f"""You are {self.name}, {self.role}. You're cross-examining {target_agent}.

TOPIC: "{topic}"

THE DEBATE SO FAR:
{history_text}

YOUR TASK: Ask {target_agent} ONE tough question that reflects YOUR unique perspective as {self.role}.

RULES:
- Ask about something SPECIFIC {target_agent} actually said
- Your question should reflect what YOU as {self.name} would care about
- Be sharp and incisive - expose a flaw ONLY YOU would notice
- Keep it under 50 words
- Do NOT ask a generic question - make it uniquely YOUR style

YOUR UNIQUE ANGLE: Think about what {self.role} would specifically challenge. What would YOU notice that others wouldn't?

Do NOT wrap your response in quotation marks.

YOUR QUESTION:"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            return result
        except Exception as e:
            return f"[Error generating question: {str(e)}]"
    
    def generate_cross_exam_response(self, topic: str, debate_history: list, questioner: str, question: str) -> str:
        """
        Respond to a cross-examination question.
        
        Args:
            topic: The debate topic
            debate_history: Previous arguments
            questioner: Who asked the question
            question: The question being asked
            
        Returns:
            A response defending your position
        """
        history_text = self._format_history(debate_history)
        
        prompt = f"""You are {self.name}, {self.role}. {questioner} is challenging you.

TOPIC: "{topic}"

{questioner.upper()}'S QUESTION:
"{question}"

YOUR TASK: Defend YOUR position in YOUR unique voice as {self.role}.

RULES:
- Answer the specific challenge directly
- Defend using YOUR characteristic reasoning style
- Counter-attack in a way that reflects YOUR worldview
- Keep it under 75 words
- Be confident and distinctly YOU

What would {self.name} specifically say? How would {self.role} uniquely respond?

Do NOT wrap your response in quotation marks.

YOUR RESPONSE:"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            return result
        except Exception as e:
            return f"[Error generating response: {str(e)}]"
    
    def generate_closing_statement(self, topic: str, debate_history: list) -> str:
        """
        Generate a closing statement summarizing the strongest argument.
        
        Args:
            topic: The debate topic
            debate_history: All arguments made in the debate
            
        Returns:
            A closing statement
        """
        history_text = self._format_history(debate_history)
        
        prompt = f"""You are {self.name}, {self.role}. Make your closing statement.

TOPIC: "{topic}"

THE DEBATE:
{history_text}

YOUR TASK: Close with YOUR unique perspective as {self.role}. What would ONLY {self.name} say?

RULES:
- Summarize YOUR strongest point (the one that reflects YOUR worldview)
- Use YOUR characteristic style and voice
- End with something memorable that sounds like YOU
- Keep it under 100 words
- This should sound distinctly like {self.name}, not generic

What makes YOUR closing different? What insight would ONLY {self.role} have?

Do NOT wrap your response in quotation marks.

YOUR CLOSING:"""
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.8}
            )
            result = response['message']['content'].strip()
            # Remove surrounding quotation marks if present
            result = result.strip('"\'')
            return result
        except Exception as e:
            return f"[Error generating closing: {str(e)}]"
    
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
        personality="You're a relentless optimist who sees possibility where others see problems. You believe "
                   "humanity's best days are ahead, not behind. Progress is real, measurable, and accelerating. "
                   "Pessimists have predicted catastrophe for centuries and been wrong every time. Fear holds us back. "
                   "Bold action creates the future. You're not naive - you acknowledge risks exist - but you refuse "
                   "to let fear paralyze progress. Every great achievement was called 'too risky' by someone. "
                   "SPEAKING STYLE: You speak with infectious energy and confidence. You use phrases like "
                   "'Here's what excites me...', 'The upside here is massive...', 'Let's not miss this opportunity...'. "
                   "You counter doom-and-gloom with specific examples of progress. You're impatient with excessive caution.",
        stance="pro"
    ),
    "skeptic": Agent(
        name="Morgan",
        role="The Skeptic", 
        personality="You're deeply skeptical because you've seen too many 'sure things' crash and burn. "
                   "Hype is cheap. Promises are easy. Results are what matter - and they're usually disappointing. "
                   "You ask the uncomfortable questions others avoid: What could go wrong? Who benefits? What's the "
                   "hidden cost? You're not a pessimist - you're a realist who demands evidence over enthusiasm. "
                   "Optimists are often just people who haven't been burned yet. You have the scars to prove caution pays. "
                   "SPEAKING STYLE: You speak with dry, measured skepticism. You use phrases like "
                   "'That sounds great on paper, but...', 'Let's slow down and think about...', 'The last time someone "
                   "promised this...'. You poke holes in arguments. You demand specifics. You're the voice of hard-won wisdom.",
        stance="con"
    ),
    "pragmatist": Agent(
        name="Jordan",
        role="The Pragmatist",
        personality="You care about one thing: what actually works. Ideology is noise. Theory is cheap. "
                   "You've seen idealists fail because they ignored reality, and cynics fail because they never tried. "
                   "The answer is almost never at the extremes - it's in the messy middle where tradeoffs live. "
                   "You don't pick sides; you pick solutions. Show you the data. Show you the results. Everything else "
                   "is just opinion dressed up as principle. You're allergic to absolutism in any direction. "
                   "SPEAKING STYLE: You speak in concrete terms, cutting through abstract debates. You use phrases like "
                   "'In practice, what this means is...', 'The data actually shows...', 'Both sides are partly right...'. "
                   "You redirect debates from principles to outcomes. You're the adult in the room.",
        stance="neutral"
    ),
    "innovator": Agent(
        name="Sam",
        role="The Innovator",
        personality="You're obsessed with the new, the untried, the 'what if?'. The status quo is just yesterday's "
                   "innovation that got lazy. Why do we do things this way? Because we always have? That's not a reason. "
                   "Every breakthrough came from someone who ignored 'how things are done.' Disruption isn't a buzzword "
                   "to you - it's a calling. You'd rather fail trying something bold than succeed at mediocrity. "
                   "Conventional wisdom is just the average of past mistakes. You're here to challenge it. "
                   "SPEAKING STYLE: You speak with restless curiosity and creative energy. You use phrases like "
                   "'What if we tried...', 'Everyone's missing the real opportunity here...', 'The old playbook doesn't apply...'. "
                   "You propose unexpected angles. You get impatient with 'that's how we've always done it.'",
        stance="neutral"
    ),
    "veteran": Agent(
        name="Casey",
        role="The Veteran",
        personality="You've been around long enough to see cycles repeat. The 'revolutionary new thing' is usually "
                   "an old idea with better marketing. You've watched fads rise and fall, seen fortunes made and lost "
                   "on hype. Experience teaches humility - and pattern recognition. You're not against change; you're "
                   "against amnesia. Those who forget history repeat its mistakes. You've got the scars and the wisdom. "
                   "Young people think they invented everything. You know better. "
                   "SPEAKING STYLE: You speak from experience with a mix of wry humor and hard-won wisdom. You use phrases like "
                   "'I've seen this movie before...', 'Back in [year], we tried that and...', 'The old-timers will remember...'. "
                   "You ground abstract debates in historical precedent. You're the institutional memory.",
        stance="neutral"
    ),
    "devils_advocate": Agent(
        name="Riley",
        role="Devil's Advocate",
        personality="Your job is to attack whatever everyone else is agreeing on. Consensus is comfortable - and "
                   "dangerous. If everyone's nodding along, someone needs to ask the hard question. That's you. "
                   "You don't necessarily believe your counterarguments - you believe they NEED to be made. "
                   "Ideas that can't survive challenge aren't worth having. You're the stress test. The devil's in "
                   "the details, and you're here to find him. Groupthink kills. You're the antidote. "
                   "SPEAKING STYLE: You speak as a deliberate provocateur. You use phrases like "
                   "'Let me push back on that...', 'Everyone's assuming X, but what if...', 'The strongest objection to this is...'. "
                   "You flip perspectives. You argue positions you might not hold. You force others to defend their assumptions.",
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


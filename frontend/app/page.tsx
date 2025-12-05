"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";

// Types
interface DebateEntry {
  type: string;
  round?: number | string;
  agent?: string;
  role?: string;
  message?: string;
  topic?: string;
  agents?: Array<{ name: string; role: string }>;
  question?: string;
  responding_to?: string;
}

interface SavedDebate {
  id: string;
  topic: string;
  timestamp: number;
  entries: DebateEntry[];
  agents: string[];
}

interface VoteState {
  [key: number]: number; // index -> vote (-1, 0, 1)
}

interface PinnedPoint {
  index: number;
  text: string;
  agent: string;
}

// Agent template mapping
const agentTemplates: Record<string, string> = {
  // Modern agents
  Alex: "optimist",
  Morgan: "skeptic",
  Jordan: "pragmatist",
  Sam: "innovator",
  Casey: "veteran",
  Riley: "devils_advocate",
  // Philosophers
  Kant: "kant",
  Mill: "mill",
  Aristotle: "aristotle",
  Rawls: "rawls",
  Socrates: "socrates",
  Nietzsche: "nietzsche",
};

// Agent color mapping
const agentColors: Record<string, { bg: string; text: string; border: string }> = {
  // Modern agents
  Alex: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-l-emerald-500" },
  Morgan: { bg: "bg-red-500/10", text: "text-red-400", border: "border-l-red-500" },
  Jordan: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-l-blue-500" },
  Sam: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-l-amber-500" },
  Casey: { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-l-purple-500" },
  Riley: { bg: "bg-pink-500/10", text: "text-pink-400", border: "border-l-pink-500" },
  // Philosophers
  Kant: { bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-l-indigo-500" },
  Mill: { bg: "bg-teal-500/10", text: "text-teal-400", border: "border-l-teal-500" },
  Aristotle: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-l-orange-500" },
  Rawls: { bg: "bg-sky-500/10", text: "text-sky-400", border: "border-l-sky-500" },
  Socrates: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-l-cyan-500" },
  Nietzsche: { bg: "bg-rose-500/10", text: "text-rose-400", border: "border-l-rose-500" },
  // System
  Moderator: { bg: "bg-neutral-500/10", text: "text-white", border: "border-l-neutral-500" },
};

const getAgentColor = (name: string) => {
  return agentColors[name] || { bg: "bg-neutral-500/10", text: "text-neutral-400", border: "border-l-neutral-500" };
};

// Section configuration for synthesis parsing
const sectionConfig = [
  { key: "Synthesis", icon: "○", color: "text-neutral-400", borderColor: "border-neutral-700" },
  { key: "Points of Agreement", icon: "○", color: "text-emerald-400", borderColor: "border-emerald-900" },
  { key: "Points of Contention", icon: "○", color: "text-amber-400", borderColor: "border-amber-900" },
  { key: "Key Insights", icon: "○", color: "text-blue-400", borderColor: "border-blue-900" },
  { key: "Conclusion", icon: "○", color: "text-purple-400", borderColor: "border-purple-900" },
  { key: "Confidence", icon: "○", color: "text-pink-400", borderColor: "border-pink-900" },
];

// Clean up markdown formatting from text
const cleanMarkdown = (text: string): string => {
  return text
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/^:\s*/, "")
    .trim();
};

// Clean agent message - remove leading **Name**: patterns and trailing prompts
const cleanAgentMessage = (message: string): string => {
  return message
    // Remove leading **Name**: or **Name** (Name): patterns
    .replace(/^\*\*[^*]+\*\*:?\s*/i, "")
    // Remove any remaining **bold** formatting
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    // Remove trailing "Please respond" type prompts
    .replace(/\s*(Please respond|Please reply|Your turn|Respond with)[^.]*\.?\s*$/i, "")
    .trim();
};

// Parse content into bullet points
const parseContentIntoBullets = (content: string): string[] => {
  const bulletPattern = /(?:^|\n)\s*\*\s+/;
  
  if (!content.includes("* ")) {
    return [cleanMarkdown(content)];
  }
  
  const normalized = content.replace(/\s+\*\s+/g, "\n* ");
  const parts = normalized.split(bulletPattern).filter(p => p.trim());
  
  if (parts.length > 1) {
    return parts.map(p => cleanMarkdown(p));
  }
  
  return [cleanMarkdown(content)];
};

// Parse synthesis message into structured sections
const parseSynthesis = (message: string) => {
  const sections: { title: string; content: string[]; icon: string; color: string; borderColor: string }[] = [];
  
  const sectionKeys = sectionConfig.map(s => s.key).join("|");
  const sectionRegex = new RegExp(`\\*\\*(${sectionKeys}):?\\*\\*`, "gi");
  
  const sectionMatches: { key: string; index: number; endIndex: number }[] = [];
  let match;
  
  while ((match = sectionRegex.exec(message)) !== null) {
    sectionMatches.push({
      key: match[1],
      index: match.index,
      endIndex: match.index + match[0].length,
    });
  }
  
  for (let i = 0; i < sectionMatches.length; i++) {
    const current = sectionMatches[i];
    const nextIndex = i + 1 < sectionMatches.length ? sectionMatches[i + 1].index : message.length;
    const rawContent = message.substring(current.endIndex, nextIndex).trim();
    
    const config = sectionConfig.find(s => s.key.toLowerCase() === current.key.toLowerCase());
    if (config && rawContent) {
      sections.push({
        title: config.key,
        content: parseContentIntoBullets(rawContent),
        icon: config.icon,
        color: config.color,
        borderColor: config.borderColor,
      });
    }
  }
  
  return sections;
};

// Component to render formatted synthesis
const SynthesisCard = ({ message }: { message: string }) => {
  const sections = parseSynthesis(message);
  
  if (sections.length === 0) {
    return <p className="text-gray-200 leading-relaxed">{message}</p>;
  }

  return (
    <div className="space-y-3">
      {sections.map((section, idx) => (
        <div key={idx} className={`border-l-2 ${section.borderColor} pl-4 py-2`}>
          <div className="flex items-center gap-2 mb-2">
            <h4 className={`text-xs font-medium uppercase tracking-wider ${section.color}`}>{section.title}</h4>
          </div>
          
          {section.content.length === 1 ? (
            <p className="text-neutral-400 leading-relaxed text-sm">
              {section.content[0]}
            </p>
          ) : (
            <ul className="space-y-1.5">
              {section.content.map((bullet, bulletIdx) => (
                <li key={bulletIdx} className="text-neutral-400 text-sm leading-relaxed flex items-start gap-2">
                  <span className={`mt-2 w-1 h-1 rounded-full flex-shrink-0 ${section.color.replace('text-', 'bg-')}`} />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
};

// Collapsible Message Component with interactive features
const CollapsibleMessage = ({ 
  entry, 
  index,
  isExpanded,
  onToggle,
  voteValue,
  isPinned,
  onVote,
  onPin,
  onFollowUp,
  onRespond,
}: { 
  entry: DebateEntry; 
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
  voteValue: number;
  isPinned: boolean;
  onVote: (direction: number) => void;
  onPin: () => void;
  onFollowUp: () => void;
  onRespond: () => void;
}) => {
  const colors = getAgentColor(entry.agent || "");
  const isSynthesis = entry.type === "synthesis";
  const isFollowUp = entry.type === "followup";
  const isResponse = entry.type === "response";
  const isModeratorEntry = entry.agent === "Moderator" || isSynthesis;
  
  // Clean the message for non-synthesis entries
  const cleanedMessage = isSynthesis ? entry.message : cleanAgentMessage(entry.message || "");
  const messagePreview = cleanedMessage?.slice(0, 150) || "";
  const isLong = (cleanedMessage?.length || 0) > 150;

  return (
    <motion.div
      key={index}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 }}
      className={`p-4 rounded-md border-l-2 ${
        isSynthesis
          ? "bg-neutral-900/30 border-l-neutral-600"
          : `${colors.border}`
      } ${isPinned ? "ring-1 ring-amber-500/30" : ""}`}
    >
      {/* Agent Header */}
      <div className="flex items-center justify-between">
        <div 
          className="flex items-center gap-3 cursor-pointer"
          onClick={onToggle}
        >
          <div className={`text-sm font-medium ${isSynthesis ? "text-white" : colors.text}`}>
            {entry.agent}
          </div>
          <div className="text-xs text-neutral-600">
            {entry.role}
            {!isSynthesis && entry.round && ` · R${entry.round}`}
            {isFollowUp && <span className="text-blue-400 ml-1">• Follow-up</span>}
            {isResponse && <span className="text-purple-400 ml-1">• Re: {entry.responding_to}</span>}
          </div>
        </div>
        
        {/* Action buttons - only for non-moderator entries */}
        {!isModeratorEntry && (
          <div className="flex items-center gap-1">
            <button 
              onClick={() => onVote(1)} 
              className={`px-2 py-1 text-xs rounded transition-colors ${
                voteValue === 1 
                  ? "text-emerald-400 bg-emerald-500/20" 
                  : "text-neutral-600 hover:text-emerald-400"
              }`}
              title="Upvote"
            >
              ↑{voteValue > 0 ? voteValue : ""}
            </button>
            <button 
              onClick={() => onVote(-1)} 
              className={`px-2 py-1 text-xs rounded transition-colors ${
                voteValue === -1 
                  ? "text-red-400 bg-red-500/20" 
                  : "text-neutral-600 hover:text-red-400"
              }`}
              title="Downvote"
            >
              ↓
            </button>
            <button 
              onClick={onPin} 
              className={`px-2 py-1 text-xs rounded transition-colors ${
                isPinned 
                  ? "text-amber-400 bg-amber-500/20" 
                  : "text-neutral-600 hover:text-amber-400"
              }`}
              title={isPinned ? "Unpin" : "Pin insight"}
            >
              📌
            </button>
            <button 
              onClick={onFollowUp}
              className="px-2 py-1 text-xs text-neutral-600 hover:text-blue-400 rounded transition-colors"
              title="Ask follow-up"
            >
              💬
            </button>
            <button 
              onClick={onRespond}
              className="px-2 py-1 text-xs text-neutral-600 hover:text-purple-400 rounded transition-colors"
              title="Have agent respond"
            >
              ↩
            </button>
            {isLong && (
              <button 
                onClick={onToggle}
                className="px-2 py-1 text-xs text-neutral-600 hover:text-white transition-colors"
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? "−" : "+"}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Follow-up question display */}
      {isFollowUp && entry.question && (
        <div className="mt-2 px-3 py-2 bg-blue-500/10 rounded text-xs text-blue-300 border-l-2 border-blue-500">
          Q: {entry.question}
        </div>
      )}

      {/* Message */}
      <div className="mt-3">
        {isSynthesis ? (
          <SynthesisCard message={entry.message || ""} />
        ) : (
          <p className="text-neutral-400 text-sm leading-relaxed">
            {isExpanded || !isLong ? cleanedMessage : `${messagePreview}...`}
          </p>
        )}
      </div>
    </motion.div>
  );
};

// Sample debate topics
const sampleTopics = [
  "Should developers use AI coding assistants?",
  "Is remote work better than office work?",
  "Tabs vs Spaces - which is superior?",
  "Should startups use microservices or monoliths?",
  "Is college necessary for a career in tech?",
  "Should we regulate AI development?",
];

export default function Home() {
  const [topic, setTopic] = useState("");
  const [debates, setDebates] = useState<DebateEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentRound, setCurrentRound] = useState<number>(0);
  const [selectedTemplates, setSelectedTemplates] = useState<string[]>(["optimist", "skeptic", "pragmatist"]);
  const [rounds, setRounds] = useState(2);
  const [collapsedMessages, setCollapsedMessages] = useState<Set<number>>(new Set());
  const [savedDebates, setSavedDebates] = useState<SavedDebate[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Interactive features state
  const [votes, setVotes] = useState<VoteState>({});
  const [pinnedPoints, setPinnedPoints] = useState<PinnedPoint[]>([]);
  const [showPinned, setShowPinned] = useState(false);
  const [followUpAgent, setFollowUpAgent] = useState<string | null>(null);
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [respondToEntry, setRespondToEntry] = useState<{ index: number; entry: DebateEntry } | null>(null);
  const [respondingAgent, setRespondingAgent] = useState<string>("");
  const [isInteractionLoading, setIsInteractionLoading] = useState(false);
  
  const debateEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load saved debates from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("discourse-debates");
    if (saved) {
      setSavedDebates(JSON.parse(saved));
    }
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    debateEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [debates]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isLoading) stopDebate();
        if (followUpAgent) setFollowUpAgent(null);
        if (respondToEntry) setRespondToEntry(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isLoading, followUpAgent, respondToEntry]);

  const startDebate = async () => {
    if (!topic.trim()) {
      setError("Please enter a debate topic");
      return;
    }

    setIsLoading(true);
    setError(null);
    setDebates([]);
    setCurrentRound(0);
    setCollapsedMessages(new Set());
    setVotes({});
    setPinnedPoints([]);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("http://localhost:8000/debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          rounds,
          agent_templates: selectedTemplates,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error("Failed to start debate");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === "round_start") {
                setCurrentRound(data.round);
              }
              
              setDebates((prev) => [...prev, data]);
            } catch (e) {
              console.error("Failed to parse:", line);
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        // Debate was cancelled
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong");
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const stopDebate = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  const toggleTemplate = (template: string) => {
    setSelectedTemplates((prev) => {
      if (prev.includes(template)) {
        if (prev.length <= 2) return prev;
        return prev.filter((t) => t !== template);
      }
      if (prev.length >= 4) return prev;
      return [...prev, template];
    });
  };

  const toggleMessageExpand = (index: number) => {
    setCollapsedMessages(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const expandAll = () => {
    setCollapsedMessages(new Set());
  };

  const collapseAll = () => {
    setCollapsedMessages(new Set(argumentEntries.map((_, i) => i)));
  };

  // Vote on an argument
  const vote = (index: number, direction: number) => {
    setVotes(prev => {
      const current = prev[index] || 0;
      return { ...prev, [index]: current === direction ? 0 : direction };
    });
  };

  // Pin/unpin an insight
  const pinPoint = (index: number, text: string, agent: string) => {
    const exists = pinnedPoints.some(p => p.index === index);
    if (exists) {
      setPinnedPoints(prev => prev.filter(p => p.index !== index));
    } else {
      setPinnedPoints(prev => [...prev, { index, text: text.slice(0, 100), agent }]);
    }
  };

  // Ask follow-up question
  const askFollowUp = async () => {
    if (!followUpAgent || !followUpQuestion.trim()) return;
    setIsInteractionLoading(true);
    const template = agentTemplates[followUpAgent];
    
    try {
      const response = await fetch("http://localhost:8000/followup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          agent_template: template,
          question: followUpQuestion,
          context: debates
            .filter(d => d.type === "argument")
            .map(d => ({ agent: d.agent, role: d.role, message: d.message })),
        }),
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split("\n")) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));
            if (data.type === "followup") {
              setDebates(prev => [...prev, data]);
            }
          }
        }
      }
    } catch (err) {
      console.error("Follow-up failed:", err);
    } finally {
      setIsInteractionLoading(false);
      setFollowUpAgent(null);
      setFollowUpQuestion("");
    }
  };

  // Request agent response to another agent
  const requestAgentResponse = async () => {
    if (!respondToEntry || !respondingAgent) return;
    setIsInteractionLoading(true);
    const template = agentTemplates[respondingAgent];
    
    try {
      const response = await fetch("http://localhost:8000/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          responder_template: template,
          target_agent: respondToEntry.entry.agent,
          target_message: respondToEntry.entry.message,
          context: debates
            .filter(d => d.type === "argument")
            .map(d => ({ agent: d.agent, role: d.role, message: d.message })),
        }),
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split("\n")) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));
            if (data.type === "response") {
              setDebates(prev => [...prev, data]);
            }
          }
        }
      }
    } catch (err) {
      console.error("Response failed:", err);
    } finally {
      setIsInteractionLoading(false);
      setRespondToEntry(null);
      setRespondingAgent("");
    }
  };

  const copyDebate = async () => {
    const argumentEntries = debates.filter((d) => d.type === "argument" || d.type === "synthesis");
    const text = argumentEntries
      .map(entry => `**${entry.agent}** (${entry.role}${entry.round ? ` · Round ${entry.round}` : ""}):\n${entry.message}`)
      .join("\n\n---\n\n");
    
    const fullText = `# ${topic}\n\n${text}`;
    
    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const saveDebate = () => {
    if (debates.length === 0) return;
    
    const newDebate: SavedDebate = {
      id: Date.now().toString(),
      topic,
      timestamp: Date.now(),
      entries: debates,
      agents: selectedTemplates,
    };
    
    const updated = [newDebate, ...savedDebates].slice(0, 10); // Keep last 10
    setSavedDebates(updated);
    localStorage.setItem("discourse-debates", JSON.stringify(updated));
  };

  const loadDebate = (debate: SavedDebate) => {
    setTopic(debate.topic);
    setDebates(debate.entries);
    setSelectedTemplates(debate.agents);
    setShowHistory(false);
    setCollapsedMessages(new Set());
    setVotes({});
    setPinnedPoints([]);
  };

  const deleteDebate = (id: string) => {
    const updated = savedDebates.filter(d => d.id !== id);
    setSavedDebates(updated);
    localStorage.setItem("discourse-debates", JSON.stringify(updated));
  };

  const clearHistory = () => {
    setSavedDebates([]);
    localStorage.removeItem("discourse-debates");
  };

  const argumentEntries = debates.filter((d) => 
    d.type === "argument" || d.type === "synthesis" || d.type === "followup" || d.type === "response"
  );
  const debateComplete = !isLoading && argumentEntries.length > 0;
  
  // Get available agents for response modal
  const availableAgents = Object.entries(agentTemplates).filter(
    ([name]) => selectedTemplates.includes(agentTemplates[name])
  );

  return (
    <main className="min-h-screen p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-3xl md:text-4xl font-medium tracking-tight text-white mb-2">
            discourse
          </h1>
          <p className="text-neutral-500 text-sm tracking-wide">
            multi-agent debate
          </p>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6 mb-8"
        >
          {/* Topic Input */}
          <div className="mb-6">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Topic
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isLoading && startDebate()}
                placeholder="What should we debate?"
                className="flex-1 px-4 py-3 bg-black rounded-md border border-neutral-800 focus:border-neutral-600 text-white placeholder-neutral-600 transition-colors"
                disabled={isLoading}
              />
              {isLoading ? (
                <button
                  onClick={stopDebate}
                  className="px-6 py-3 bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/50 rounded-md font-medium transition-colors"
                >
                  Stop
                </button>
              ) : (
                <button
                  onClick={startDebate}
                  className="px-6 py-3 bg-white text-black hover:bg-neutral-200 rounded-md font-medium transition-colors"
                >
                  Start
                </button>
              )}
            </div>
            <p className="text-xs text-neutral-700 mt-2">
              Press <kbd className="px-1.5 py-0.5 bg-neutral-900 rounded text-neutral-500">Enter</kbd> to start
              {isLoading && <>, <kbd className="px-1.5 py-0.5 bg-neutral-900 rounded text-neutral-500">Esc</kbd> to stop</>}
            </p>
          </div>

          {/* Sample Topics */}
          <div className="mb-6">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Suggestions
            </label>
            <div className="flex flex-wrap gap-2">
              {sampleTopics.map((sampleTopic) => (
                <button
                  key={sampleTopic}
                  onClick={() => setTopic(sampleTopic)}
                  className="px-3 py-1.5 text-xs text-neutral-400 border border-neutral-800 hover:border-neutral-600 hover:text-white rounded-md transition-colors"
                >
                  {sampleTopic}
                </button>
              ))}
            </div>
          </div>

          {/* Agent Selection */}
          <div className="mb-4">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Agents
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries({
                optimist: { name: "Alex", label: "Optimist" },
                skeptic: { name: "Morgan", label: "Skeptic" },
                pragmatist: { name: "Jordan", label: "Pragmatist" },
                innovator: { name: "Sam", label: "Innovator" },
                veteran: { name: "Casey", label: "Veteran" },
                devils_advocate: { name: "Riley", label: "Contrarian" },
              }).map(([key, { name, label }]) => {
                const isSelected = selectedTemplates.includes(key);
                const colors = getAgentColor(name);
                return (
                  <button
                    key={key}
                    onClick={() => toggleTemplate(key)}
                    disabled={isLoading}
                    className={`px-3 py-2 rounded-md text-xs font-medium transition-all disabled:opacity-50 ${
                      isSelected
                        ? `${colors.bg} ${colors.text} border border-current`
                        : "border border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-300"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Philosophers Selection */}
          <div className="mb-6">
            <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
              Philosophers
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries({
                kant: { name: "Kant", label: "Kant" },
                mill: { name: "Mill", label: "Mill" },
                aristotle: { name: "Aristotle", label: "Aristotle" },
                rawls: { name: "Rawls", label: "Rawls" },
                socrates: { name: "Socrates", label: "Socrates" },
                nietzsche: { name: "Nietzsche", label: "Nietzsche" },
              }).map(([key, { name, label }]) => {
                const isSelected = selectedTemplates.includes(key);
                const colors = getAgentColor(name);
                return (
                  <button
                    key={key}
                    onClick={() => toggleTemplate(key)}
                    disabled={isLoading}
                    className={`px-3 py-2 rounded-md text-xs font-medium transition-all disabled:opacity-50 ${
                      isSelected
                        ? `${colors.bg} ${colors.text} border border-current`
                        : "border border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-300"
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Rounds Selection */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-3">
                Rounds
              </label>
              <div className="flex gap-2">
                {[1, 2, 3].map((num) => (
                  <button
                    key={num}
                    onClick={() => setRounds(num)}
                    disabled={isLoading}
                    className={`px-4 py-2 rounded-md text-xs font-medium transition-colors disabled:opacity-50 ${
                      rounds === num
                        ? "bg-white text-black"
                        : "border border-neutral-800 text-neutral-500 hover:border-neutral-600 hover:text-neutral-300"
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex gap-2">
              {pinnedPoints.length > 0 && (
                <button
                  onClick={() => setShowPinned(!showPinned)}
                  className="px-3 py-2 text-xs text-amber-400 border border-amber-500/50 hover:bg-amber-500/10 rounded-md transition-colors"
                >
                  📌 {pinnedPoints.length}
                </button>
              )}
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="px-3 py-2 text-xs text-neutral-500 hover:text-white border border-neutral-800 hover:border-neutral-600 rounded-md transition-colors"
              >
                History {savedDebates.length > 0 && `(${savedDebates.length})`}
              </button>
            </div>
          </div>
        </motion.div>

        {/* Pinned Points Panel */}
        <AnimatePresence>
          {showPinned && pinnedPoints.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="card p-4 mb-8 overflow-hidden"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-amber-400">📌 Pinned Insights</h3>
                <button
                  onClick={() => setPinnedPoints([])}
                  className="text-xs text-neutral-600 hover:text-red-400 transition-colors"
                >
                  Clear All
                </button>
              </div>
              <div className="space-y-2">
                {pinnedPoints.map((point, i) => (
                  <div key={i} className="flex items-start justify-between p-3 border border-neutral-800 rounded-md">
                    <div className="flex-1">
                      <span className={`text-xs ${getAgentColor(point.agent).text}`}>{point.agent}:</span>
                      <p className="text-xs text-neutral-400 mt-1">{point.text}...</p>
                    </div>
                    <button 
                      onClick={() => pinPoint(point.index, "", "")} 
                      className="ml-2 text-neutral-600 hover:text-red-400 text-xs transition-colors"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* History Panel */}
        <AnimatePresence>
          {showHistory && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="card p-4 mb-8 overflow-hidden"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-white">Saved Debates</h3>
                {savedDebates.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="text-xs text-red-400 hover:text-red-300 transition-colors"
                  >
                    Clear All
                  </button>
                )}
              </div>
              {savedDebates.length === 0 ? (
                <p className="text-xs text-neutral-600">No saved debates yet</p>
              ) : (
                <div className="space-y-2">
                  {savedDebates.map((debate) => (
                    <div
                      key={debate.id}
                      className="flex items-center justify-between p-3 border border-neutral-800 rounded-md hover:border-neutral-700 transition-colors"
                    >
                      <button
                        onClick={() => loadDebate(debate)}
                        className="flex-1 text-left"
                      >
                        <div className="text-sm text-white truncate">{debate.topic}</div>
                        <div className="text-xs text-neutral-600">
                          {new Date(debate.timestamp).toLocaleDateString()} · {debate.entries.filter(e => e.type === "argument").length} arguments
                        </div>
                      </button>
                      <button
                        onClick={() => deleteDebate(debate.id)}
                        className="ml-2 p-1 text-neutral-600 hover:text-red-400 transition-colors"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Follow-up Question Modal */}
        <AnimatePresence>
          {followUpAgent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="card p-6 max-w-lg w-full"
              >
                <h3 className="text-lg font-medium text-white mb-4">
                  Ask <span className={getAgentColor(followUpAgent).text}>{followUpAgent}</span>
                </h3>
                <input
                  type="text"
                  value={followUpQuestion}
                  onChange={(e) => setFollowUpQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && askFollowUp()}
                  placeholder="What would you like to ask?"
                  className="w-full px-4 py-3 bg-black rounded-md border border-neutral-800 focus:border-neutral-600 text-white placeholder-neutral-600 mb-4"
                  autoFocus
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => { setFollowUpAgent(null); setFollowUpQuestion(""); }}
                    className="px-4 py-2 text-sm text-neutral-500 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={askFollowUp}
                    disabled={isInteractionLoading || !followUpQuestion.trim()}
                    className="px-4 py-2 text-sm bg-white text-black rounded-md hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isInteractionLoading ? "Asking..." : "Ask"}
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agent Response Modal */}
        <AnimatePresence>
          {respondToEntry && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="card p-6 max-w-lg w-full"
              >
                <h3 className="text-lg font-medium text-white mb-2">
                  Respond to <span className={getAgentColor(respondToEntry.entry.agent || "").text}>{respondToEntry.entry.agent}</span>
                </h3>
                <p className="text-xs text-neutral-500 mb-4 line-clamp-2">
                  "{respondToEntry.entry.message?.slice(0, 150)}..."
                </p>
                <label className="block text-xs uppercase tracking-wider text-neutral-500 mb-2">
                  Choose responder
                </label>
                <div className="flex flex-wrap gap-2 mb-4">
                  {availableAgents
                    .filter(([name]) => name !== respondToEntry.entry.agent)
                    .map(([name]) => {
                      const colors = getAgentColor(name);
                      return (
                        <button
                          key={name}
                          onClick={() => setRespondingAgent(name)}
                          className={`px-3 py-2 rounded-md text-xs font-medium transition-all ${
                            respondingAgent === name
                              ? `${colors.bg} ${colors.text} border border-current`
                              : "border border-neutral-800 text-neutral-500 hover:border-neutral-600"
                          }`}
                        >
                          {name}
                        </button>
                      );
                    })}
                </div>
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => { setRespondToEntry(null); setRespondingAgent(""); }}
                    className="px-4 py-2 text-sm text-neutral-500 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={requestAgentResponse}
                    disabled={isInteractionLoading || !respondingAgent}
                    className="px-4 py-2 text-sm bg-white text-black rounded-md hover:bg-neutral-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isInteractionLoading ? "Generating..." : "Get Response"}
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 border border-neutral-800 rounded-md text-neutral-400"
            >
              <span className="text-red-400">{error}</span>
              <p className="text-xs mt-2 text-neutral-600">
                Backend: <code className="text-neutral-500">uvicorn server:app --reload --port 8000</code>
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Debate Display */}
        {argumentEntries.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card p-6"
          >
            {/* Debate Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-neutral-800">
              <div>
                <h2 className="text-lg font-medium text-white">
                  {debates.find((d) => d.type === "start")?.topic || topic}
                </h2>
                <p className="text-xs text-neutral-500 mt-1">
                  {isLoading ? `Round ${currentRound}` : "Complete"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {debateComplete && (
                  <>
                    <button
                      onClick={collapseAll}
                      className="px-2 py-1 text-xs text-neutral-600 hover:text-white transition-colors"
                      title="Collapse all"
                    >
                      ⊟
                    </button>
                    <button
                      onClick={expandAll}
                      className="px-2 py-1 text-xs text-neutral-600 hover:text-white transition-colors"
                      title="Expand all"
                    >
                      ⊞
                    </button>
                    <button
                      onClick={copyDebate}
                      className="px-3 py-1.5 text-xs text-neutral-500 hover:text-white border border-neutral-800 hover:border-neutral-600 rounded-md transition-colors"
                    >
                      {copied ? "Copied!" : "Copy"}
                    </button>
                    <button
                      onClick={saveDebate}
                      className="px-3 py-1.5 text-xs text-neutral-500 hover:text-white border border-neutral-800 hover:border-neutral-600 rounded-md transition-colors"
                    >
                      Save
                    </button>
                  </>
                )}
                <div className="text-xs text-neutral-600 ml-2">
                  {argumentEntries.length} responses
                </div>
              </div>
            </div>

            {/* Arguments */}
            <div className="space-y-4">
              <AnimatePresence>
                {argumentEntries.map((entry, i) => (
                  <CollapsibleMessage
                    key={i}
                    entry={entry}
                    index={i}
                    isExpanded={!collapsedMessages.has(i)}
                    onToggle={() => toggleMessageExpand(i)}
                    voteValue={votes[i] || 0}
                    isPinned={pinnedPoints.some(p => p.index === i)}
                    onVote={(dir) => vote(i, dir)}
                    onPin={() => pinPoint(i, entry.message || "", entry.agent || "")}
                    onFollowUp={() => setFollowUpAgent(entry.agent || null)}
                    onRespond={() => setRespondToEntry({ index: i, entry })}
                  />
                ))}
              </AnimatePresence>

              {/* Loading Indicator */}
              {isLoading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-3 p-4 border border-neutral-800 rounded-md"
                >
                  <div className="flex gap-1">
                    <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full" />
                    <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full" />
                    <span className="typing-dot w-1.5 h-1.5 bg-white rounded-full" />
                  </div>
                  <span className="text-neutral-500 text-xs">Thinking...</span>
                </motion.div>
              )}

              <div ref={debateEndRef} />
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {debates.length === 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-center py-20"
          >
            <p className="text-neutral-600 text-sm">Enter a topic to begin</p>
          </motion.div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-xs text-neutral-700">
          Local AI · No external data
        </div>
      </div>
    </main>
  );
}

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import SourcesAccordion, { Source } from "./SourcesAccordion";
import ResolutionView, { ResolutionData } from "./ResolutionView";
import { Bot, User } from "lucide-react";

export interface MessageProps {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  sources?: Source[];
  state?: string;
  media?: ResolutionData["media"];
  steps?: ResolutionData["steps"];
  ecosystem_escalation?: ResolutionData["ecosystem_escalation"];
}

export default function ChatMessage({ role, content, agent, sources, state, media, steps, ecosystem_escalation }: MessageProps) {
  const isUser = role === "user";

  const agentNameMap: Record<string, string> = {
    TrainingRecommendationAgent: "Training Advisor",
    ProductRecommendationAgent: "Procurement Specialist",
    TalentRecommendationAgent: "Talent Recruiter",
    TroubleshootingAgent: "Diagnostics Engineer",
    GeneralQAAgent: "General Assistant",
  };

  const displayAgentName = agent ? (agentNameMap[agent] || agent) : null;

  return (
    <div className={`flex w-full flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}>
      {/* Agent Badge (Assistant only) */}
      {!isUser && displayAgentName && (
        <div className="flex items-center gap-1.5 px-1 text-xs font-semibold text-gray-500">
          <Bot className="h-3.5 w-3.5" />
          {displayAgentName}
        </div>
      )}

      {/* User label */}
      {isUser && (
        <div className="flex items-center gap-1.5 px-1 text-xs font-semibold text-gray-500">
          You
          <User className="h-3.5 w-3.5" />
        </div>
      )}

      {/* Message Bubble or Resolution View */}
      {role === "assistant" && state === "RESOLVED" && (media || (steps && steps.length > 0)) ? (
        <div className="w-full max-w-[95%]">
          <ResolutionView data={{ chatResponse: content, media, steps, ecosystem_escalation }} />
          {/* Sources Accordion below Resolution View */}
          {sources && sources.length > 0 && (
            <div className="mt-2">
              <SourcesAccordion sources={sources} />
            </div>
          )}
        </div>
      ) : (
        <div
          className={`relative max-w-[85%] rounded-2xl px-5 py-3.5 text-sm shadow-sm sm:max-w-[75%] sm:text-base ${
            isUser
              ? "bg-blue-600 text-white rounded-tr-sm"
              : "bg-white text-gray-800 border border-gray-200 rounded-tl-sm"
          }`}
        >
          <div className={`prose prose-sm max-w-none ${isUser ? "prose-invert" : ""}`}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ node, ...props }) => {
                  const href = props.href || "";
                  const isYouTube = href.includes('youtube.com') || href.includes('youtu.be');
                  const isImage = href.match(/\.(jpeg|jpg|gif|png|webp|svg)$/i) != null || href.startsWith('data:image');
                  
                  if (isYouTube) {
                    const watchMatch = /[?&]v=([a-zA-Z0-9_-]{11})/.exec(href);
                    const shortMatch = /youtu\.be\/([a-zA-Z0-9_-]{11})/.exec(href);
                    const videoId = watchMatch ? watchMatch[1] : (shortMatch ? shortMatch[1] : null);
                    
                    if (videoId) {
                      return (
                        <div className="relative group rounded-2xl overflow-hidden shadow-lg shadow-black/5 my-4 bg-black aspect-video w-full max-w-xl border border-slate-200">
                          <iframe
                            src={`https://www.youtube-nocookie.com/embed/${videoId}?rel=0`}
                            title="Embedded Video"
                            className="w-full h-full"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                          />
                        </div>
                      );
                    }
                  }
                  
                  if (isImage) {
                    return (
                      <div className="my-4">
                        <img src={href} alt="Attached Visual Reference" className="max-w-full h-auto rounded-2xl border border-slate-200 shadow-md max-h-96 object-contain bg-white" />
                      </div>
                    );
                  }

                  return <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-600 font-medium hover:underline hover:text-blue-800 transition-colors flex items-center gap-1 inline-flex" />;
                },
                img: ({ node, ...props }) => (
                  <div className="my-4">
                    <img {...props} className="max-w-full h-auto rounded-2xl border border-slate-200 shadow-md max-h-96 object-contain bg-white" />
                  </div>
                ),
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-4 w-full">
                    <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg overflow-hidden" {...props} />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th className="px-4 py-2 bg-gray-50 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-600 border-t border-gray-100" {...props} />
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>

          {/* Sources Accordion */}
          {!isUser && sources && sources.length > 0 && (
            <div className="mt-4">
              <SourcesAccordion sources={sources} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

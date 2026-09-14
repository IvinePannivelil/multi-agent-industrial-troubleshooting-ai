import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { 
  AlertTriangle, 
  ZoomIn, 
  ShoppingCart, 
  ShieldCheck, 
  Lightbulb, 
  Users,
  CheckCircle2,
  Video,
  Image as ImageIcon
} from "lucide-react";

export interface EcosystemEscalation {
  goose_mart?: string;
  goose_elevate?: string;
  goose_solutions?: string;
  hire_my_engineer?: string;
  goose_service_shield?: string;
}

export interface ResolutionData {
  chatResponse: string;
  media?: {
    image?: string;
    video?: string;
  };
  steps?: string[];
  ecosystem_escalation?: EcosystemEscalation;
}

export default function ResolutionView({ data }: { data: ResolutionData }) {
  const [zoomedImage, setZoomedImage] = useState(false);
  const [showEscalation, setShowEscalation] = useState(false);
  const [checkedSteps, setCheckedSteps] = useState<Record<number, boolean>>({});

  const { chatResponse, media, steps, ecosystem_escalation } = data;

  const toggleStep = (index: number) => {
    setCheckedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const isSafetyWarning = chatResponse.includes("**SAFETY WARNING**") || chatResponse.includes("**Safety Warning**") || chatResponse.toUpperCase().includes("SAFETY");

  return (
    <div className="w-full flex flex-col gap-8 p-8 bg-white/40 backdrop-blur-xl text-slate-900 rounded-3xl border border-white/40 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] my-6 transition-all duration-500 hover:shadow-[0_8px_32px_0_rgba(31,38,135,0.12)]">
      
      {/* Safety Warning Header */}
      {isSafetyWarning && (
        <div className="flex items-start gap-4 p-5 bg-red-50/80 backdrop-blur-md border border-red-100 rounded-2xl text-red-900 animate-in fade-in zoom-in duration-500">
          <div className="bg-red-500 p-2 rounded-lg shadow-lg shadow-red-200">
            <AlertTriangle className="w-6 h-6 text-white shrink-0" />
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-lg mb-1 tracking-tight">CRITICAL SAFETY PROMPT</h3>
            <div className="text-sm font-medium leading-relaxed opacity-90">
              <ReactMarkdown>
                {chatResponse.split('\n')[0]} 
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {/* Main Layout */}
      <div className={`grid grid-cols-1 ${media?.video || media?.image ? 'lg:grid-cols-12' : ''} gap-10`}>
        
        {/* LEFT/MAIN COLUMN: Checklist */}
        <div className={`${media?.video || media?.image ? 'lg:col-span-12 xl:col-span-7' : ''} flex flex-col gap-8`}>
          
          <div className="flex flex-col gap-6">
            {/* Analysis Section (always show if not just a safety warning) */}
            {chatResponse && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div className="bg-amber-500 p-2 rounded-xl shadow-lg shadow-amber-100">
                    <Lightbulb className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight text-slate-800">Issue Analysis</h3>
                </div>
                <div className="prose prose-slate max-w-none prose-p:text-slate-700 p-6 bg-white/50 rounded-2xl border border-slate-100">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{
                    isSafetyWarning ? chatResponse.split('\n').slice(1).join('\n').trim() : chatResponse
                  }</ReactMarkdown>
                </div>
              </div>
            )}

            {/* Checklist Section */}
            {steps && steps.length > 0 && (
              <div className="flex flex-col gap-4 mt-4">
                <div className="flex items-center gap-3">
                  <div className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-100">
                    <CheckCircle2 className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight text-slate-800">Resolution Pathway</h3>
                </div>
                <div className="flex flex-col gap-4">
                  {steps.map((step, idx) => (
                    <label 
                      key={idx} 
                      className={`group relative flex items-start gap-5 p-5 rounded-2xl border transition-all duration-300 cursor-pointer ${
                        checkedSteps[idx] 
                          ? 'bg-slate-50 border-slate-200 opacity-60' 
                          : 'bg-white border-slate-100 shadow-[0_4px_12px_rgba(0,0,0,0.03)] hover:border-blue-400 hover:shadow-[0_8px_24px_rgba(59,130,246,0.12)] hover:-translate-y-0.5'
                      }`}
                    >
                      <div className="pt-1">
                        <div className={`w-6 h-6 rounded-md border-2 transition-all duration-300 flex items-center justify-center ${
                          checkedSteps[idx] 
                          ? 'bg-blue-600 border-blue-600 shadow-md shadow-blue-100' 
                          : 'border-slate-300 group-hover:border-blue-500'
                        }`}>
                          {checkedSteps[idx] && <CheckCircle2 className="w-4 h-4 text-white" />}
                        </div>
                        <input 
                          type="checkbox" 
                          className="sr-only"
                          checked={!!checkedSteps[idx]}
                          onChange={() => toggleStep(idx)}
                        />
                      </div>
                      <span className={`text-[1.05rem] leading-relaxed transition-all duration-300 ${checkedSteps[idx] ? 'line-through text-slate-500' : 'text-slate-700 font-medium'}`}>
                        {step}
                      </span>
                      
                      {!checkedSteps[idx] && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-0 group-hover:h-8 bg-blue-500 rounded-r-full transition-all duration-300" />
                      )}
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Media */}
        {(media?.image || media?.video) && (
          <div className="lg:col-span-12 xl:col-span-5 flex flex-col gap-8">
            
            {/* Image Section */}
            {media.image && (
              <div className="flex flex-col gap-4">
                 <div className="flex items-center gap-2 text-slate-500 font-semibold px-2 uppercase text-xs tracking-widest">
                   <ImageIcon className="w-4 h-4" />
                   Visual Reference
                 </div>
                 
                 {media.image.startsWith('/') || media.image.startsWith('http') ? (
                   <div className="relative group rounded-3xl overflow-hidden shadow-2xl shadow-blue-900/10 border-4 border-white bg-white">
                     <img 
                       src={media.image} 
                       alt="Diagnostic Reference" 
                       className={`w-full h-64 object-cover transition-all duration-700 ease-out-expo ${zoomedImage ? 'scale-150 cursor-zoom-out' : 'cursor-zoom-in hover:scale-110'}`}
                       onClick={() => setZoomedImage(!zoomedImage)}
                     />
                     <div className={`absolute inset-0 bg-blue-900/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none flex items-center justify-center ${zoomedImage ? 'hidden' : ''}`}>
                       <div className="bg-white/90 backdrop-blur-md p-3 rounded-2xl shadow-xl transform translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
                         <ZoomIn className="w-6 h-6 text-blue-600" />
                       </div>
                     </div>
                   </div>
                 ) : (
                   <div className="relative flex flex-col items-center justify-center p-8 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-300 text-center min-h-[16rem]">
                     <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mb-4 text-slate-400">
                       <ImageIcon className="w-8 h-8 opacity-50" />
                     </div>
                     <span className="font-semibold text-slate-700 mb-1">Visualization Note</span>
                     <p className="text-slate-500 text-sm max-w-xs">{media.image}</p>
                   </div>
                 )}
              </div>
            )}

            {/* Video Player Section */}
            {media.video && (() => {
              const isYouTube = media.video.includes('youtube.com') || media.video.includes('youtu.be');
              const getVideoId = (url: string) => {
                const watchRegex = /[?&]v=([a-zA-Z0-9_-]{11})/;
                const watchMatch = watchRegex.exec(url);
                if (watchMatch) return watchMatch[1];
                const shortRegex = /youtu\.be\/([a-zA-Z0-9_-]{11})/;
                const shortMatch = shortRegex.exec(url);
                if (shortMatch) return shortMatch[1];
                return null;
              };
              const videoId = isYouTube ? getVideoId(media.video) : null;
              const embedUrl = videoId ? `https://www.youtube-nocookie.com/embed/${videoId}?rel=0` : media.video;

              return (
                <div className="flex flex-col gap-4">
                  <div className="flex items-center gap-2 text-slate-500 font-semibold px-2 uppercase text-xs tracking-widest">
                    <Video className="w-4 h-4" />
                    Training / Manual Video
                  </div>
                  <div className="relative rounded-3xl overflow-hidden shadow-2xl shadow-blue-900/10 border-4 border-white bg-black aspect-video">
                    {isYouTube && videoId ? (
                      <iframe
                        src={embedUrl}
                        title="Training Video"
                        className="w-full h-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      />
                    ) : (
                      <video
                        src={media.video}
                        controls
                        className="w-full h-full object-cover opacity-90 hover:opacity-100 transition-opacity"
                      >
                        <track kind="captions" />
                      </video>
                    )}
                  </div>
                </div>
              );
            })()}

          </div>
        )}
      </div>

      {/* Escalation Footer */}
      {ecosystem_escalation && Object.keys(ecosystem_escalation).length > 0 && (
        <div className="mt-8 pt-10 border-t border-slate-100 flex flex-col items-center">
          {!showEscalation ? (
            <button 
              onClick={() => setShowEscalation(true)}
              className="group relative px-10 py-4 bg-slate-900 text-white font-bold rounded-2xl shadow-xl shadow-slate-200 hover:shadow-slate-300 hover:-translate-y-1 transition-all duration-300 overflow-hidden"
            >
              <span className="relative z-10">Still Not Fixed?</span>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/0 via-white/10 to-blue-600/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
            </button>
          ) : (
            <div className="w-full max-w-2xl flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-6 duration-500">
              <div className="text-center">
                <h4 className="text-2xl font-bold text-slate-800 tracking-tight">Ecosystem Intelligence Routing</h4>
                <p className="text-slate-500 mt-2 font-medium">We've identified the best Goose Vertical for your current situation.</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {ecosystem_escalation.goose_mart && (
                  <a href={ecosystem_escalation.goose_mart} target="_blank" rel="noopener noreferrer" className="group flex flex-col p-6 bg-white border border-slate-100 rounded-3xl hover:border-blue-500 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300">
                    <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 mb-4 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300">
                      <ShoppingCart className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-lg text-slate-800">Goose Mart</span>
                    <span className="text-sm text-slate-500 mt-1">Sourcing verified parts & equipment with same-day dispatch.</span>
                  </a>
                )}

                {ecosystem_escalation.goose_service_shield && (
                  <a href={ecosystem_escalation.goose_service_shield} target="_blank" rel="noopener noreferrer" className="group flex flex-col p-6 bg-white border border-slate-100 rounded-3xl hover:border-emerald-500 hover:shadow-2xl hover:shadow-emerald-500/10 transition-all duration-300">
                    <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 mb-4 group-hover:bg-emerald-600 group-hover:text-white transition-colors duration-300">
                      <ShieldCheck className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-lg text-slate-800">Service Shield</span>
                    <span className="text-sm text-slate-500 mt-1">Dispatching a certified technician to your site immediately.</span>
                  </a>
                )}

                {ecosystem_escalation.goose_solutions && (
                  <a href={ecosystem_escalation.goose_solutions} target="_blank" rel="noopener noreferrer" className="group flex flex-col p-6 bg-white border border-slate-100 rounded-3xl hover:border-orange-500 hover:shadow-2xl hover:shadow-orange-500/10 transition-all duration-300">
                    <div className="w-12 h-12 bg-orange-50 rounded-2xl flex items-center justify-center text-orange-600 mb-4 group-hover:bg-orange-600 group-hover:text-white transition-colors duration-300">
                      <Lightbulb className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-lg text-slate-800">Goose Solutions</span>
                    <span className="text-sm text-slate-500 mt-1">Consultancy for complex system failures and redesign.</span>
                  </a>
                )}

                {ecosystem_escalation.hire_my_engineer && (
                  <a href={ecosystem_escalation.hire_my_engineer} target="_blank" rel="noopener noreferrer" className="group flex flex-col p-6 bg-white border border-slate-100 rounded-3xl hover:border-purple-500 hover:shadow-2xl hover:shadow-purple-500/10 transition-all duration-300">
                    <div className="w-12 h-12 bg-purple-50 rounded-2xl flex items-center justify-center text-purple-600 mb-4 group-hover:bg-purple-600 group-hover:text-white transition-colors duration-300">
                      <Users className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-lg text-slate-800">Hire My Engineer</span>
                    <span className="text-sm text-slate-500 mt-1">Freelance industrial engineering for custom coding & configs.</span>
                  </a>
                )}

                {ecosystem_escalation.goose_elevate && (
                  <a href={ecosystem_escalation.goose_elevate} target="_blank" rel="noopener noreferrer" className="group flex flex-col p-6 bg-white border border-slate-100 rounded-3xl hover:border-teal-500 hover:shadow-2xl hover:shadow-teal-500/10 transition-all duration-300">
                    <div className="w-12 h-12 bg-teal-50 rounded-2xl flex items-center justify-center text-teal-600 mb-4 group-hover:bg-teal-600 group-hover:text-white transition-colors duration-300">
                      <ShieldCheck className="w-6 h-6" />
                    </div>
                    <span className="font-bold text-lg text-slate-800">Goose Elevate</span>
                    <span className="text-sm text-slate-500 mt-1">Upskill your team with specialized maintenance training.</span>
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

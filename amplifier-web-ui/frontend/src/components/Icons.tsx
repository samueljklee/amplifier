interface IconProps {
  className?: string
  size?: number
}

// Studio/Palette Icon with subtle color shift animation
export function StudioIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes colorShift {
          0%, 100% { stroke: currentColor; }
          50% { stroke: #8b5cf6; }
        }
        .palette-animate {
          animation: colorShift 3s ease-in-out infinite;
        }
      `}</style>
      <path
        className="palette-animate"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
      />
    </svg>
  )
}

// Plus/Create Icon with scale animation on hover
export function CreateIcon({ className = '', size = 16 }: IconProps) {
  return (
    <svg
      className={`inline-block transition-transform hover:scale-110 ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4v16m8-8H4"
      />
    </svg>
  )
}

// Chart/Analytics Icon with pulse animation
export function AnalyzerIcon({ className = '', size = 32 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes chartPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(0.95); }
        }
        .chart-pulse {
          animation: chartPulse 2s ease-in-out infinite;
        }
      `}</style>
      <g className="chart-pulse">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </g>
    </svg>
  )
}

// Document Icon with page flip animation
export function DocumentIcon({ className = '', size = 32 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes pageFlip {
          0%, 100% { transform: rotateY(0deg); }
          50% { transform: rotateY(10deg); }
        }
        .page-flip {
          animation: pageFlip 3s ease-in-out infinite;
          transform-origin: left center;
        }
      `}</style>
      <g className="page-flip">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </g>
    </svg>
  )
}

// Search/Magnifier Icon with zoom animation
export function SearchIcon({ className = '', size = 32 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes searchZoom {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        .search-zoom {
          animation: searchZoom 2s ease-in-out infinite;
          transform-origin: center;
        }
      `}</style>
      <g className="search-zoom">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </g>
    </svg>
  )
}

// Lightbulb/Idea Icon with glow animation
export function IdeaIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes ideaGlow {
          0%, 100% { filter: drop-shadow(0 0 2px rgba(251, 191, 36, 0)); }
          50% { filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.6)); }
        }
        .idea-glow {
          animation: ideaGlow 2s ease-in-out infinite;
        }
      `}</style>
      <g className="idea-glow">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
        />
      </g>
    </svg>
  )
}

// Checkmark Icon with bounce animation
export function CheckIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes checkBounce {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.2); }
        }
        .check-bounce {
          animation: checkBounce 0.5s ease-in-out;
        }
      `}</style>
      <path
        className="check-bounce"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  )
}

// X/Close Icon
export function CloseIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block transition-transform hover:rotate-90 ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  )
}

// Loading/Spinner Icon with continuous rotation
export function LoadingIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block animate-spin ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  )
}

// Pencil/Edit Icon
export function EditIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block transition-transform hover:translate-y-[-2px] ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
      />
    </svg>
  )
}

// Sparkles Icon with twinkle animation
export function SparklesIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes sparkle {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.8); }
        }
        .sparkle-1 { animation: sparkle 1.5s ease-in-out infinite; }
        .sparkle-2 { animation: sparkle 1.5s ease-in-out infinite 0.5s; }
        .sparkle-3 { animation: sparkle 1.5s ease-in-out infinite 1s; }
      `}</style>
      <g>
        <path
          className="sparkle-1"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        />
      </g>
    </svg>
  )
}

// Chat/Message Icon with typing animation
export function ChatIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
      />
    </svg>
  )
}

// Code Icon
export function CodeIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
      />
    </svg>
  )
}

// Magic Wand Icon with trail animation
export function MagicIcon({ className = '', size = 32 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes wand {
          0%, 100% { transform: rotate(-5deg); }
          50% { transform: rotate(5deg); }
        }
        .wand-wave {
          animation: wand 2s ease-in-out infinite;
          transform-origin: bottom right;
        }
      `}</style>
      <g className="wand-wave">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        />
      </g>
    </svg>
  )
}

// Hourglass/Timer Icon with sand flow animation
export function TimerIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes hourglass {
          0% { transform: rotate(0deg); }
          50% { transform: rotate(180deg); }
          100% { transform: rotate(180deg); }
        }
        .hourglass-flip {
          animation: hourglass 3s ease-in-out infinite;
          transform-origin: center;
        }
      `}</style>
      <g className="hourglass-flip">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </g>
    </svg>
  )
}

// Eye/Review Icon
export function ReviewIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block transition-transform hover:scale-110 ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
      />
    </svg>
  )
}

// Celebration/Party Icon with confetti animation
export function CelebrationIcon({ className = '', size = 32 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes confetti1 {
          0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 1; }
          50% { transform: translate(-3px, -3px) rotate(45deg); opacity: 0.8; }
        }
        @keyframes confetti2 {
          0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 1; }
          50% { transform: translate(3px, -3px) rotate(-45deg); opacity: 0.8; }
        }
        @keyframes confetti3 {
          0%, 100% { transform: translate(0, 0) rotate(0deg); opacity: 1; }
          50% { transform: translate(-2px, 3px) rotate(90deg); opacity: 0.8; }
        }
        @keyframes celebrate {
          0%, 100% { transform: scale(1) rotate(0deg); }
          25% { transform: scale(1.1) rotate(-5deg); }
          75% { transform: scale(1.1) rotate(5deg); }
        }
        .confetti-1 { animation: confetti1 1.5s ease-in-out infinite; }
        .confetti-2 { animation: confetti2 1.5s ease-in-out infinite 0.3s; }
        .confetti-3 { animation: confetti3 1.5s ease-in-out infinite 0.6s; }
        .celebrate-center { animation: celebrate 2s ease-in-out infinite; }
      `}</style>
      <g className="celebrate-center">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </g>
      <circle className="confetti-1" cx="5" cy="5" r="1" fill="currentColor" />
      <circle className="confetti-2" cx="19" cy="5" r="1" fill="currentColor" />
      <circle className="confetti-3" cx="5" cy="19" r="1" fill="currentColor" />
      <circle className="confetti-1" cx="19" cy="19" r="1.5" fill="currentColor" />
    </svg>
  )
}

// File/Document Preview Icon with page turn animation
export function FilePreviewIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes preview {
          0%, 100% { transform: translateX(0); opacity: 1; }
          50% { transform: translateX(2px); opacity: 0.9; }
        }
        .preview-line {
          animation: preview 2s ease-in-out infinite;
        }
      `}</style>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
      />
      <path
        className="preview-line"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 13h6m-6 4h4"
      />
    </svg>
  )
}

// Book/Library Icon with page flip animation
export function LibraryIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes bookOpen {
          0%, 100% { transform: scaleX(1); }
          50% { transform: scaleX(1.05); }
        }
        .book-pages {
          animation: bookOpen 2s ease-in-out infinite;
          transform-origin: center;
        }
      `}</style>
      <g className="book-pages">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
        />
      </g>
    </svg>
  )
}

// Writing/Blog Icon with pen stroke animation
export function WritingIcon({ className = '', size = 24 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes write {
          0%, 100% { stroke-dashoffset: 0; }
          50% { stroke-dashoffset: 10; }
        }
        .writing-stroke {
          stroke-dasharray: 20;
          animation: write 2s linear infinite;
        }
      `}</style>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
      />
      <path
        className="writing-stroke"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9 15l6-6"
      />
    </svg>
  )
}

// Graph/Chart Network Icon with node pulse
export function GraphIcon({ className = '', size = 20 }: IconProps) {
  return (
    <svg
      className={`inline-block ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
    >
      <style>{`
        @keyframes nodePulse {
          0%, 100% { r: 2; opacity: 1; }
          50% { r: 2.5; opacity: 0.7; }
        }
        .node { animation: nodePulse 2s ease-in-out infinite; }
        .node-1 { animation-delay: 0s; }
        .node-2 { animation-delay: 0.3s; }
        .node-3 { animation-delay: 0.6s; }
      `}</style>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M5 12h14M12 5l7 7-7 7"
      />
      <circle className="node node-1" cx="5" cy="12" r="2" fill="currentColor" />
      <circle className="node node-2" cx="12" cy="5" r="2" fill="currentColor" />
      <circle className="node node-3" cx="19" cy="12" r="2" fill="currentColor" />
    </svg>
  )
}

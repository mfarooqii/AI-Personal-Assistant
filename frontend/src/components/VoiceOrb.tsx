import { useState, useCallback } from 'react';
import { Mic } from 'lucide-react';
import { speechToText } from '../api';

interface Props {
  onTranscript: (text: string) => void;
}

export function VoiceOrb({ onTranscript }: Props) {
  const [listening, setListening] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);

  const startListening = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: 'audio/webm' });
        try {
          const result = await speechToText(blob);
          if (result.text) {
            onTranscript(result.text);
          }
        } catch {
          // STT unavailable — fail silently
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setListening(true);
    } catch {
      // Microphone not available
    }
  }, [onTranscript]);

  const stopListening = useCallback(() => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
    setListening(false);
    setMediaRecorder(null);
  }, [mediaRecorder]);

  return (
    <div className="relative flex items-center justify-center">
      {/* Glow rings */}
      <div className={`absolute w-36 h-36 rounded-full bg-aria-500/10 ${listening ? 'orb-listening' : 'orb-pulse'}`} />
      <div className={`absolute w-28 h-28 rounded-full bg-aria-500/20 ${listening ? 'orb-listening' : 'orb-pulse'}`}
           style={{ animationDelay: '0.3s' }} />

      {/* Main orb button */}
      <button
        onMouseDown={startListening}
        onMouseUp={stopListening}
        onMouseLeave={stopListening}
        onTouchStart={startListening}
        onTouchEnd={stopListening}
        className={`
          relative z-10 w-20 h-20 rounded-full flex items-center justify-center
          transition-all duration-300 shadow-lg
          ${listening
            ? 'bg-aria-500 shadow-aria-500/40 scale-110'
            : 'bg-[var(--bg-tertiary)] border-2 border-aria-500/30 hover:border-aria-500/60 hover:shadow-aria-500/20'
          }
        `}
      >
        <Mic size={28} className={listening ? 'text-white' : 'text-aria-400'} />
      </button>

      {listening && (
        <p className="absolute -bottom-8 text-sm text-aria-400 animate-pulse">Listening...</p>
      )}
    </div>
  );
}

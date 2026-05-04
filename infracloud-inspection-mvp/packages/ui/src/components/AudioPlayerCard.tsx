import { Pause, Play } from "lucide-react";
import { useEffect, useRef, useState, type ChangeEvent } from "react";

interface AudioPlayerCardProps {
  audioUrl: string;
}

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function AudioPlayerCard({ audioUrl }: AudioPlayerCardProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoaded = () => setDuration(audio.duration || 0);
    const onEnded = () => setPlaying(false);

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("loadedmetadata", onLoaded);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoaded);
      audio.removeEventListener("ended", onEnded);
    };
  }, [audioUrl]);

  const togglePlayback = async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      await audio.play();
      setPlaying(true);
    }
  };

  const cyclePlaybackRate = () => {
    const audio = audioRef.current;
    if (!audio) return;

    const nextRate = playbackRate === 1 ? 1.5 : playbackRate === 1.5 ? 2 : 1;
    audio.playbackRate = nextRate;
    setPlaybackRate(nextRate);
  };

  const seekTo = (event: ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio || !duration) return;

    const nextTime = Number(event.target.value);
    audio.currentTime = nextTime;
    setCurrentTime(nextTime);
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;
  const waveformBars = Array.from({ length: 96 }, (_, index) => {
    const x = index / 95;
    const envelope =
      0.08 +
      gaussian(x, 0.16, 0.05, 0.45) +
      gaussian(x, 0.33, 0.045, 0.78) +
      gaussian(x, 0.52, 0.055, 0.52) +
      gaussian(x, 0.73, 0.05, 0.66);
    const ripple = 0.72 + 0.28 * Math.abs(Math.sin(index * 0.9));
    return Math.max(2, Math.round(22 * envelope * ripple));
  });

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>Audio Recording</h2>
          <p>Review the sample inspection note before triggering extraction.</p>
        </div>
      </div>
      <div className="audio-player">
        <audio ref={audioRef} src={audioUrl} preload="metadata" />
        <div className="audio-player__top">
          <button className="audio-player__play" onClick={togglePlayback} type="button">
            {playing ? <Pause size={20} /> : <Play size={20} />}
          </button>
          <div className="audio-player__waveform" aria-hidden="true">
            {waveformBars.map((height, index) => {
              const active = index / waveformBars.length < progress / 100;
              return (
                <span
                  className={`audio-player__waveform-bar ${active ? "is-active" : ""}`}
                  key={`${height}-${index}`}
                  style={{ height: `${height}px` }}
                />
              );
            })}
          </div>
        </div>
        <div className="audio-player__bottom">
          <span className="audio-player__time">{formatTime(currentTime)}</span>
          <div className="audio-player__slider-wrap">
            <input
              aria-label="Audio progress"
              className="audio-player__slider"
              max={duration || 0}
              min="0"
              onChange={seekTo}
              step="0.1"
              type="range"
              value={Math.min(currentTime, duration || 0)}
            />
          </div>
          <span className="audio-player__time">{formatTime(duration)}</span>
          <button className="audio-player__speed" onClick={cyclePlaybackRate} type="button">
            {playbackRate}x
          </button>
        </div>
      </div>
    </section>
  );
}

function gaussian(x: number, mean: number, spread: number, amplitude: number) {
  return amplitude * Math.exp(-((x - mean) ** 2) / (2 * spread ** 2));
}

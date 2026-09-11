import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio, staticFile } from 'remotion';

// Subtitle component rendering a rolling word window
const Subtitles = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (!words || words.length === 0) return null;

  const currentWordIndex = words.findIndex((w) => currentTime >= w.start && currentTime <= w.end);
  const currentWordObj = currentWordIndex !== -1 ? words[currentWordIndex] : null;

  // Keep a 3-word rolling window
  const startIdx = Math.max(0, (currentWordIndex !== -1 ? currentWordIndex : 0) - 1);
  const subtitleSlice = words.slice(startIdx, startIdx + 3);

  return (
    <div
      style={{
        position: 'absolute',
        top: '12%',
        width: '100%',
        textAlign: 'center',
        padding: '0 40px',
        boxSizing: 'border-box',
        minHeight: 120,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 50,
      }}
    >
      <div style={{ fontSize: 52, fontWeight: 900, textTransform: 'uppercase', lineHeight: 1.3 }}>
        {subtitleSlice.map((w, i) => {
          const isActive = currentWordObj && w.word === currentWordObj.word && w.start === currentWordObj.start;
          return (
            <span
              key={i}
              style={{
                color: isActive ? '#ffd633' : '#ffffff',
                margin: '0 10px',
                display: 'inline-block',
                transform: isActive ? 'scale(1.15)' : 'scale(1.0)',
                transition: 'transform 0.08s ease',
                textShadow: isActive ? '0 0 24px rgba(255, 214, 51, 0.7)' : '0 4px 12px rgba(0,0,0,0.9)',
              }}
            >
              {w.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};

// Renders code snippet with optional substring focus phrase
const CodeBlock = ({ code, focusPhrase }) => {
  if (!focusPhrase || !code?.includes(focusPhrase)) {
    return <code>{code}</code>;
  }

  const idx = code.indexOf(focusPhrase);
  const before = code.slice(0, idx);
  const match = code.slice(idx, idx + focusPhrase.length);
  const after = code.slice(idx + focusPhrase.length);

  return (
    <code>
      {before}
      <span style={{ backgroundColor: 'rgba(255, 214, 51, 0.25)', color: '#ffd633', borderRadius: '4px', padding: '0 2px' }}>
        {match}
      </span>
      {after}
    </code>
  );
};

export const CodingShort = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const activeScene = [...(data?.scenes || [])]
    .reverse()
    .find((scene) => currentTime >= scene.start_time) || data?.scenes?.[0];

  const isPopTime = activeScene && Math.abs(currentTime - activeScene.emphasis_time) < (1 / fps);

  return (
    <AbsoluteFill style={{ backgroundColor: '#0d1117', color: 'white', fontFamily: 'sans-serif' }}>
      <Audio src={staticFile(data.audio_file)} />
      {isPopTime && <Audio src={staticFile('pop.mp3')} volume={0.5} />}

      {/* Subtitles Overlay */}
      <Subtitles words={data.words} />

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', padding: '60px' }}>

        {activeScene?.scene_type === 'fullscreen_text' && (
          <h1 style={{ fontSize: '65px', textAlign: 'center', fontWeight: 'bold', color: '#e6edf3', lineHeight: '1.3' }}>
            {activeScene.display_text}
          </h1>
        )}

        {(activeScene?.scene_type === 'code_reveal' || activeScene?.scene_type === 'code_transform' || activeScene?.scene_type === 'terminal') && (
          <div style={{ backgroundColor: '#161b22', padding: '40px', borderRadius: '20px', width: '100%', boxShadow: '0 20px 40px rgba(0,0,0,0.5)', overflow: 'hidden' }}>
            <pre style={{ fontSize: '35px', color: '#c9d1d9', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              <CodeBlock code={activeScene.code_snippet} focusPhrase={activeScene.focus_phrase} />
            </pre>
          </div>
        )}

        {activeScene?.scene_type === 'comparison' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px', width: '100%' }}>
            <div style={{ backgroundColor: '#2a0a12', padding: '30px', borderRadius: '20px', border: '2px solid #ff7b72', overflow: 'hidden' }}>
              <h2 style={{ color: '#ff7b72', margin: '0 0 15px 0', fontSize: '35px' }}>
                ❌ {activeScene.problem_label || "Slow Approach"}
              </h2>
              <pre style={{ fontSize: '30px', color: '#c9d1d9', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                <code>{activeScene.problem_code || activeScene.code_snippet}</code>
              </pre>
            </div>
            <div style={{ backgroundColor: '#0b2614', padding: '30px', borderRadius: '20px', border: '2px solid #3fb950', overflow: 'hidden' }}>
              <h2 style={{ color: '#3fb950', margin: '0 0 15px 0', fontSize: '35px' }}>
                ✅ {activeScene.solution_label || "Optimized / Hash Map"}
              </h2>
              <pre style={{ fontSize: '30px', color: '#c9d1d9', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                <code>{activeScene.solution_code}</code>
              </pre>
            </div>
          </div>
        )}

        {activeScene?.scene_type === 'diagram' && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', width: '100%' }}>
            {(activeScene.nodes || []).map((node, i, arr) => (
              <React.Fragment key={i}>
                <div style={{
                  backgroundColor: '#161b22',
                  border: '2px solid #58a6ff',
                  borderRadius: '16px',
                  padding: '30px 50px',
                  fontSize: '38px',
                  fontWeight: 'bold',
                  color: '#e6edf3',
                  textAlign: 'center',
                  width: '80%',
                  boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                }}>
                  {typeof node === 'string' ? node : (node.label || JSON.stringify(node))}
                </div>
                {i < arr.length - 1 && (
                  <div style={{ fontSize: '48px', color: '#58a6ff' }}>↓</div>
                )}
              </React.Fragment>
            ))}
          </div>
        )}

      </AbsoluteFill>
    </AbsoluteFill>
  );
};
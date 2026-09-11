import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { CodingShort } from './CodingShort';
import fallbackData from '../public/data_current.json';

export const RemotionRoot = () => {
  const cliProps = getInputProps();
  const data = cliProps && Object.keys(cliProps).length > 0 ? cliProps : fallbackData;

  const fps = 30;
  const lastWordTime = data?.words?.length > 0 
    ? data.words[data.words.length - 1].end 
    : 60;
  
  const durationInFrames = Math.max(30, Math.ceil((lastWordTime + 1.5) * fps));

  return (
    <Composition
      id="CodingShort"
      component={CodingShort}
      durationInFrames={durationInFrames}
      fps={fps}
      width={1080}
      height={1920}
      defaultProps={{ data }}
    />
  );
};
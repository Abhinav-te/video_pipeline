import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { CodingShort } from './CodingShort';
import { BrandProvider } from './context/BrandContext';
import fallbackData from '../public/data.json';

const WrappedCodingShort = ({ data }) => {
  return (
    <BrandProvider brand={data?.brand}>
      <CodingShort data={data} />
    </BrandProvider>
  );
};

export const RemotionRoot = () => {
  const cliProps = getInputProps();
  const rawData = cliProps && Object.keys(cliProps).length > 0 ? cliProps : fallbackData;
  const data = rawData?.data || rawData;

  const calculateMeta = ({ props, defaultProps }) => {
    const raw = props || defaultProps;
    const currentData = raw?.data || raw;
    const fps = currentData?.render_profile?.fps || 30;

    const totalDurationSec = currentData?.master_duration 
      || currentData?.duration 
      || (currentData?.scenes?.length > 0 ? currentData.scenes[currentData.scenes.length - 1].end_time : null)
      || (currentData?.words?.length > 0 ? currentData.words[currentData.words.length - 1].end + 0.25 : 30);
    const durationInFrames = Math.max(30, Math.ceil(totalDurationSec * fps));

    const aspectRatio = currentData?.render_profile?.aspect_ratio || currentData?.aspect_ratio || '16:9';
    const isVertical = aspectRatio === '9:16';
    const width = currentData?.render_profile?.width || (isVertical ? 1080 : 1920);
    const height = currentData?.render_profile?.height || (isVertical ? 1920 : 1080);

    return {
      width,
      height,
      fps,
      durationInFrames,
      props: { data: currentData },
    };
  };

  return (
    <>
      <Composition
        id="CodingShort"
        component={WrappedCodingShort}
        calculateMetadata={calculateMeta}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={900}
        defaultProps={{ data }}
      />
      <Composition
        id="CodingShortWidescreen"
        component={WrappedCodingShort}
        width={1920}
        height={1080}
        fps={30}
        durationInFrames={900}
        defaultProps={{ data }}
      />
      <Composition
        id="CodingShortVertical"
        component={WrappedCodingShort}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={900}
        defaultProps={{ data }}
      />
    </>
  );
};

export default RemotionRoot;

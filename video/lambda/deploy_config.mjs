/**
 * video/lambda/deploy_config.mjs
 * 
 * Remotion Serverless Lambda Architecture Configuration:
 * Configures AWS Region, S3 Render Bucket, and Lambda Function name.
 * Provides dispatch credentials verification and renderMediaOnLambda scaffolding.
 */

import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const LAMBDA_CONFIG = {
  region: process.env.REMOTION_AWS_REGION || process.env.AWS_REGION || 'us-east-1',
  bucketName: process.env.REMOTION_AWS_BUCKET || 'remotion-lambda-renders',
  functionName: process.env.REMOTION_AWS_FUNCTION || 'remotion-render-4-0-522',
  siteName: process.env.REMOTION_AWS_SITE_NAME || 'coding-short-pipeline',
  memorySizeInMb: 2048,
  diskSizeInMb: 2048,
  timeoutInSeconds: 240,
};

export const hasAwsCredentials = () => {
  const accessKey = process.env.REMOTION_AWS_ACCESS_KEY_ID || process.env.AWS_ACCESS_KEY_ID;
  const secretKey = process.env.REMOTION_AWS_SECRET_ACCESS_KEY || process.env.AWS_SECRET_ACCESS_KEY;
  return Boolean(accessKey && secretKey);
};

export const getLambdaDeployStatus = () => {
  return {
    hasCredentials: hasAwsCredentials(),
    config: LAMBDA_CONFIG,
    backendAvailable: hasAwsCredentials(),
  };
};

// Standalone CLI healthcheck
if (process.argv[1] === __filename) {
  const status = getLambdaDeployStatus();
  console.log('[LAMBDA:CONFIG]', JSON.stringify(status, null, 2));
}


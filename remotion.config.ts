import { Config } from '@remotion/cli/config';

// Stills and frames as PNG so the hard edges stay hard; the MP4 is encoded from those.
Config.setVideoImageFormat('png');
Config.setConcurrency(8);
Config.setEntryPoint('src/index.ts');

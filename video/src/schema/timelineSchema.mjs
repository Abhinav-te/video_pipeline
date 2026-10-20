import { z } from 'zod';

export const WordTimestampSchema = z
  .object({
    word: z.string(),
    start: z.number().nonnegative({ message: "Word start timestamp must be non-negative" }),
    end: z.number().nonnegative({ message: "Word end timestamp must be non-negative" }),
    confidence: z.number().optional(),
  })
  .passthrough();

export const SceneSchema = z
  .object({
    id: z.union([z.number(), z.string()]).nullish(),
    scene_id: z.union([z.number(), z.string()]).nullish(),
    scene_type: z.string().nullish(),
    visual_type: z.string().nullish(),
    title: z.string().nullish(),
    spoken_text: z.string().nullish(),
    narration: z.string().nullish(),
    start_time: z.number().nonnegative({ message: "Scene start_time must be non-negative (>= 0)" }),
    end_time: z.number().nonnegative({ message: "Scene end_time must be non-negative (>= 0)" }),
    duration: z.number().positive({ message: "Scene duration must be positive (> 0)" }).nullish(),
    emphasis_word: z.string().nullish(),
    emphasis_time: z.number().nullish(),
    display_text: z.string().nullish(),
    manim_asset_url: z.string().nullish(),
    manim_video_src: z.string().nullish(),
    manim_spec: z.record(z.any()).nullish(),
    badge: z.any().nullish(),
    choreography: z.any().nullish(),
    code: z.string().nullish(),
    code_snippet: z.string().nullish(),
    filename: z.string().nullish(),
    language: z.string().nullish(),
    highlight_lines: z.array(z.number()).nullish(),
    focus_phrase: z.string().nullish(),
    before_code: z.string().nullish(),
    after_code: z.string().nullish(),
    before_label: z.string().nullish(),
    after_label: z.string().nullish(),
    commands: z
      .array(
        z.object({
          cmd: z.string(),
          output: z.array(z.union([z.string(), z.number()])).nullish(),
          status: z.string().nullish(),
        }).passthrough()
      )
      .nullish(),
    nodes: z.array(z.union([z.string(), z.record(z.any())])).nullish(),
    request_payload: z.string().nullish(),
    response_payload: z.string().nullish(),
    request_method: z.string().nullish(),
    response_status: z.string().nullish(),
    problem_label: z.string().nullish(),
    problem_code: z.string().nullish(),
    solution_label: z.string().nullish(),
    solution_code: z.string().nullish(),
    comparison_sides: z.any().nullish(),
    comparison_footer: z.string().nullish(),
    entities: z.array(z.record(z.any())).nullish(),
    events: z.array(z.record(z.any())).nullish(),
    evidence_ids: z.array(z.string()).nullish(),
    cta_url: z.string().nullish(),
    items: z.array(z.record(z.any())).nullish(),
  })
  .passthrough()
  .refine(
    (data) => data.end_time > data.start_time,
    {
      message: "Scene end_time must be strictly greater than start_time",
      path: ["end_time"],
    }
  );

export const TimelineSchema = z
  .object({
    title: z.string().min(1, { message: "Timeline must have a non-empty title" }),
    schema_version: z.union([z.number(), z.string()]),
    engine_version: z.string().optional(),
    run_id: z.string().min(1, { message: "Timeline must have a valid run_id" }),
    audio_file: z.string().min(1, { message: "Timeline must reference an audio_file" }),
    scenes: z.array(SceneSchema).min(2, { message: "Timeline must contain at least 2 scenes" }),
    words: z.array(WordTimestampSchema),
    aspect_ratio: z.enum(["16:9", "9:16"]).nullish(),
    brand: z.record(z.any()).nullish(),
    render_profile: z.record(z.any()).nullish(),
  })
  .passthrough();


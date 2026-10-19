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
    id: z.union([z.number(), z.string()]).optional(),
    scene_id: z.union([z.number(), z.string()]).optional(),
    scene_type: z.string().optional(),
    visual_type: z.string().optional(),
    title: z.string().optional(),
    spoken_text: z.string().optional(),
    narration: z.string().optional(),
    start_time: z.number().nonnegative({ message: "Scene start_time must be non-negative (>= 0)" }),
    end_time: z.number().nonnegative({ message: "Scene end_time must be non-negative (>= 0)" }),
    duration: z.number().positive({ message: "Scene duration must be positive (> 0)" }).optional(),
    emphasis_word: z.string().optional(),
    emphasis_time: z.number().optional(),
    display_text: z.string().optional(),
    manim_asset_url: z.string().optional(),
    manim_video_src: z.string().optional(),
    manim_spec: z.record(z.any()).optional(),
    badge: z.any().optional(),
    choreography: z.any().optional(),
    code: z.string().optional(),
    code_snippet: z.string().optional(),
    filename: z.string().optional(),
    language: z.string().optional(),
    highlight_lines: z.array(z.number()).optional(),
    focus_phrase: z.string().optional(),
    before_code: z.string().optional(),
    after_code: z.string().optional(),
    before_label: z.string().optional(),
    after_label: z.string().optional(),
    commands: z
      .array(
        z.object({
          cmd: z.string(),
          output: z.array(z.union([z.string(), z.number()])).optional(),
          status: z.string().optional(),
        }).passthrough()
      )
      .optional(),
    nodes: z.array(z.union([z.string(), z.record(z.any())])).optional(),
    request_payload: z.string().optional(),
    response_payload: z.string().optional(),
    request_method: z.string().optional(),
    response_status: z.string().optional(),
    problem_label: z.string().optional(),
    problem_code: z.string().optional(),
    solution_label: z.string().optional(),
    solution_code: z.string().optional(),
    comparison_sides: z.any().optional(),
    comparison_footer: z.string().optional(),
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
  })
  .passthrough();


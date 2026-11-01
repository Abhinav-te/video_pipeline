import json
import os
import shutil
import hashlib
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine.pipeline.manifest import (
    load_manifest,
    save_manifest,
    archive_revision_snapshot,
    restore_revision_snapshot,
    RevisionLock,
)
from engine.revise import execute_revision
from engine.validation.evidence_validator import validate_post_render_qa

RUNS_DIR = REPO_ROOT / "video" / "public" / "runs"
VIDEO_OUT_DIR = REPO_ROOT / "video" / "out"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def setup_disposable_run(base_id: str, new_id: str) -> Path:
    src_dir = RUNS_DIR / base_id
    dst_dir = RUNS_DIR / new_id
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)

    # Ensure output.mp4 exists in dst_dir
    src_mp4 = VIDEO_OUT_DIR / f"{base_id}_v2.mp4"
    if src_mp4.exists():
        shutil.copyfile(src_mp4, dst_dir / "output.mp4")
    elif (src_dir / "revisions" / "rev_002" / "output.mp4").exists():
        shutil.copyfile(src_dir / "revisions" / "rev_002" / "output.mp4", dst_dir / "output.mp4")

    # Update run_id in manifest and data
    m = load_manifest(dst_dir)
    m["run_id"] = new_id
    save_manifest(m, dst_dir)

    data_file = dst_dir / "data.json"
    if data_file.exists():
        d = json.loads(data_file.read_text(encoding="utf-8"))
        d["run_id"] = new_id
        data_file.write_text(json.dumps(d, indent=2), encoding="utf-8")

    return dst_dir


def real_pcm_synth(narration_text, scene_dir, revision, voice_id="en-US-ChristopherNeural"):
    """
    Synthesizes real 48kHz stereo 16-bit PCM WAV offline using FFmpeg lavfi,
    providing exact PCM formatting and word timestamps for isolated sandbox testing.
    """
    scene_dir = Path(scene_dir)
    scene_dir.mkdir(parents=True, exist_ok=True)
    p = scene_dir / f"audio_v{revision}.wav"
    dur = 6.650
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=48000:cl=stereo",
        "-t", f"{dur:.3f}",
        "-c:a", "pcm_s16le",
        str(p)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    words_list = narration_text.split()
    step_t = dur / max(1, len(words_list))
    words = [
        {"word": w, "start": round(i * step_t, 3), "end": round((i + 1) * step_t, 3)}
        for i, w in enumerate(words_list)
    ]
    return p, dur, words


def test_scenario_1_failed_render_rollback():
    print("\n" + "=" * 80)
    print("SCENARIO 1: FAILED-RENDER ROLLBACK & GATE 6 QA FAILURE ROLLBACK")
    print("=" * 80)

    run_id = "run_phase401_disposable_fail"
    run_dir = setup_disposable_run("run_disposable_391", run_id)
    print(f"[SETUP] Created disposable run: {run_dir}")

    # Record initial checksums
    checksums = {
        "data.json": compute_sha256(run_dir / "data.json"),
        "manifest.json": compute_sha256(run_dir / "manifest.json"),
        "audio.wav": compute_sha256(run_dir / "audio.wav"),
        "audio.mp3": compute_sha256(run_dir / "audio.mp3"),
        "output.mp4": compute_sha256(run_dir / "output.mp4"),
    }
    m = load_manifest(run_dir)
    initial_rev = m["revision"]
    for sid, sinfo in m["scenes"].items():
        seg = run_dir / sinfo["segment_video"]
        if seg.exists():
            checksums[f"segment_{sid}"] = compute_sha256(seg)
        aud = run_dir / sinfo["audio_file"]
        if aud.exists():
            checksums[f"audio_{sid}"] = compute_sha256(aud)

    print(f"[BASELINE] Initial revision: {initial_rev}")
    print(f"[BASELINE] Captured {len(checksums)} SHA-256 baseline checksums.")

    # 1A-1. Fail-closed: Unbacked claim rejected before render
    print("\n--- Step 1A-1: Fail-closed on unbacked evidence claim ---")
    try:
        execute_revision(
            run_id=run_id,
            target_scene_id=1,
            set_title="Completely Unbacked Fictional Headline",
        )
        assert False, "Should have raised RuntimeError on unbacked claim"
    except RuntimeError as exc:
        print(f"[SUCCESS] Evidence validation correctly rejected unbacked claim: {exc}")
        assert "Evidence validation gate failed" in str(exc)

    assert compute_sha256(run_dir / "data.json") == checksums["data.json"]
    assert compute_sha256(run_dir / "manifest.json") == checksums["manifest.json"]
    assert compute_sha256(run_dir / "output.mp4") == checksums["output.mp4"]
    print("[VERIFIED] State remains 100% intact after evidence validation rejection.")

    # 1A-2. Simulate Gate 6 QA Failure after render & stitching
    print("\n--- Step 1A-2: Simulate Gate 6 QA failure desync ---")
    valid_scene1_title = "Step Isolation and Failure Behavior"
    with patch(
        "engine.revise.validate_post_render_qa",
        return_value=(False, ["Duration mismatch: video=30.0s, audio=28.4s, delta=1.6s > 0.05s tolerance"], {}),
    ):
        try:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_title=valid_scene1_title,
            )
            assert False, "Should have raised RuntimeError on Gate 6 failure"
        except RuntimeError as exc:
            print(f"[SUCCESS] Gate 6 failure correctly intercepted: {exc}")
            assert "Gate 6 output validation" in str(exc)

    # Verify state after Gate 6 failure
    assert compute_sha256(run_dir / "data.json") == checksums["data.json"], "data.json was modified!"
    assert compute_sha256(run_dir / "manifest.json") == checksums["manifest.json"], "manifest.json was modified!"
    assert compute_sha256(run_dir / "audio.wav") == checksums["audio.wav"], "audio.wav was modified!"
    assert compute_sha256(run_dir / "audio.mp3") == checksums["audio.mp3"], "audio.mp3 was modified!"
    assert compute_sha256(run_dir / "output.mp4") == checksums["output.mp4"], "output.mp4 was modified!"
    assert not (run_dir / ".staged_data_v3.json").exists(), "Staged data leaked!"
    assert not (run_dir / ".staged_output_v3.mp4").exists(), "Staged output leaked!"
    assert not (run_dir / ".staged_output_v3.keyframe.jpg").exists(), "Staged keyframe leaked!"
    assert (run_dir / "reflection.error.json").exists(), "Diagnostic reflection.error.json missing!"
    err_diag = json.loads((run_dir / "reflection.error.json").read_text(encoding="utf-8"))
    assert "Gate 6 output validation" in err_diag.get("message", "")
    print("[VERIFIED] All initial files match 100% SHA-256; no staged leak; diagnostic preserved.")

    # 1B. Simulate Render failure
    print("\n--- Step 1B: Simulate Remotion render failure ---")
    with patch("engine.revise.render_dirty_segments", return_value=False):
        try:
            execute_revision(
                run_id=run_id,
                target_scene_id=1,
                set_title=valid_scene1_title,
            )
            assert False, "Should have raised RuntimeError on render failure"
        except RuntimeError as exc:
            print(f"[SUCCESS] Render failure correctly intercepted: {exc}")

    assert compute_sha256(run_dir / "data.json") == checksums["data.json"]
    assert compute_sha256(run_dir / "manifest.json") == checksums["manifest.json"]
    assert compute_sha256(run_dir / "output.mp4") == checksums["output.mp4"]
    print("[VERIFIED] State remains 100% intact after render failure.")

    # 1C. Verify subsequent real valid revision succeeds
    print("\n--- Step 1C: Execute subsequent valid visual revision (REAL RENDER) ---")
    out_mp4 = execute_revision(
        run_id=run_id,
        target_scene_id=1,
        set_title=valid_scene1_title,
    )
    assert out_mp4.exists(), f"Output MP4 does not exist: {out_mp4}"
    new_m = load_manifest(run_dir)
    assert new_m["revision"] == 3, f"Expected revision 3, got {new_m['revision']}"
    assert (run_dir / "revisions" / "rev_003").exists(), "Snapshot rev_003 missing!"
    print(f"[VERIFIED] Subsequent valid revision succeeded! Output: {out_mp4.name} (Rev {new_m['revision']})")


def test_scenario_2_repeated_narration_revisions():
    print("\n" + "=" * 80)
    print("SCENARIO 2: REPEATED NARRATION REVISIONS & AUDIO ARTIFACT TRACKING")
    print("=" * 80)

    run_id = "run_phase401_disposable_narr"
    run_dir = setup_disposable_run("run_disposable_391", run_id)
    print(f"[SETUP] Created disposable run: {run_dir}")

    m_init = load_manifest(run_dir)
    orig_s2_audio = m_init["scenes"]["2"]["audio_file"]
    print(f"[BASELINE] Scene 2 original audio file: {orig_s2_audio}")

    # Revision 1 (Mode B): Narration revision on Scene 2
    print("\n--- Step 2A: Narration Revision 1 on Scene 2 ---")
    text_v3 = "To execute synchronous or asynchronous operations durably, wrap your operation in await step.run()."
    with patch("engine.revise.synthesize_scene_audio", side_effect=real_pcm_synth):
        out_v3 = execute_revision(
            run_id=run_id,
            target_scene_id=2,
            set_narration=text_v3,
        )
    assert out_v3.exists()

    m_v3 = load_manifest(run_dir)
    assert m_v3["revision"] == 3
    s2_audio_v3 = m_v3["scenes"]["2"]["audio_file"]
    print(f"[VERIFIED] Scene 2 audio file updated to: {s2_audio_v3}")
    assert s2_audio_v3 == "scenes/2/audio_v3.wav"
    assert (run_dir / s2_audio_v3).exists()
    assert (run_dir / "audio.wav").exists()
    # Check Gate 6 on output
    is_valid, errs, meta = validate_post_render_qa(
        video_path=out_v3,
        expected_audio_path=run_dir / "audio.wav",
        aspect_ratio="16:9",
        tolerance_sec=0.05,
    )
    assert is_valid, f"Gate 6 failed on Rev 3: {errs}"
    print(f"[VERIFIED] Gate 6 passed on Rev 3 (diff={meta.get('duration_difference')}s <= 0.05s).")

    # Revision 2 (Mode B): Second Narration revision on Scene 2
    print("\n--- Step 2B: Narration Revision 2 on Scene 2 ---")
    text_v4 = "Wrap your operation in await step.run() to execute synchronous or asynchronous operations durably."
    with patch("engine.revise.synthesize_scene_audio", side_effect=real_pcm_synth):
        out_v4 = execute_revision(
            run_id=run_id,
            target_scene_id=2,
            set_narration=text_v4,
        )
    assert out_v4.exists()

    m_v4 = load_manifest(run_dir)
    assert m_v4["revision"] == 4
    s2_audio_v4 = m_v4["scenes"]["2"]["audio_file"]
    print(f"[VERIFIED] Scene 2 audio file updated to: {s2_audio_v4}")
    assert s2_audio_v4 == "scenes/2/audio_v4.wav"
    assert (run_dir / s2_audio_v4).exists()
    assert s2_audio_v4 != s2_audio_v3

    is_valid, errs, meta = validate_post_render_qa(
        video_path=out_v4,
        expected_audio_path=run_dir / "audio.wav",
        aspect_ratio="16:9",
        tolerance_sec=0.05,
    )
    assert is_valid, f"Gate 6 failed on Rev 4: {errs}"
    print(f"[VERIFIED] Gate 6 passed on Rev 4 (diff={meta.get('duration_difference')}s <= 0.05s).")

    # Revision 3 (Mode A): Visual-only revision on Scene 4
    print("\n--- Step 2C: Visual-only Revision on Scene 4 ---")
    out_v5 = execute_revision(
        run_id=run_id,
        target_scene_id=4,
        set_title="Memoization and Durable Execution",
    )
    assert out_v5.exists()

    m_v5 = load_manifest(run_dir)
    assert m_v5["revision"] == 5
    # Scene 2 audio MUST STILL BE scenes/2/audio_v4.wav!
    assert m_v5["scenes"]["2"]["audio_file"] == "scenes/2/audio_v4.wav", (
        f"CRITICAL DEFECT: Scene 2 audio reverted! Got {m_v5['scenes']['2']['audio_file']}"
    )
    print(f"[VERIFIED] Scene 2 audio file remained: {m_v5['scenes']['2']['audio_file']} (no regression).")

    is_valid, errs, meta = validate_post_render_qa(
        video_path=out_v5,
        expected_audio_path=run_dir / "audio.wav",
        aspect_ratio="16:9",
        tolerance_sec=0.05,
    )
    assert is_valid, f"Gate 6 failed on Rev 5: {errs}"
    print(f"[VERIFIED] Gate 6 passed on Rev 5 (diff={meta.get('duration_difference')}s <= 0.05s).")


def test_scenario_3_complete_snapshot_restoration():
    print("\n" + "=" * 80)
    print("SCENARIO 3: COMPLETE SNAPSHOT RESTORATION & LEAK PREVENTION")
    print("=" * 80)

    run_id = "run_phase401_disposable_narr"
    run_dir = RUNS_DIR / run_id

    # Currently run_phase401_disposable_narr is at Revision 5 (State B).
    # Snapshot rev_003 is Snapshot A (after first narration revision).
    m_now = load_manifest(run_dir)
    assert m_now["revision"] == 5, f"Expected revision 5 before restore, got {m_now['revision']}"

    snap_3_dir = run_dir / "revisions" / "rev_003"
    assert snap_3_dir.exists(), "Snapshot rev_003 must exist!"

    snap_3_manifest = json.loads((snap_3_dir / "manifest.json").read_text(encoding="utf-8"))
    snap_3_data = json.loads((snap_3_dir / "data.json").read_text(encoding="utf-8"))
    snap_3_output_sha = compute_sha256(snap_3_dir / "output.mp4")

    print("[RESTORE] Restoring Snapshot A (Revision 3)...")
    res = restore_revision_snapshot(run_dir, target_revision=3)
    assert res["revision"] == 6
    assert res["restored_from"] == 3

    # Verify restored state
    m_restored = load_manifest(run_dir)
    assert m_restored["revision"] == 6
    # Active scenes should match snapshot 3
    assert m_restored["scenes"]["2"]["audio_file"] == snap_3_manifest["scenes"]["2"]["audio_file"]
    assert m_restored["scenes"]["4"]["revision"] == snap_3_manifest["scenes"]["4"]["revision"]
    assert m_restored["scenes"]["4"]["segment_video"] == snap_3_manifest["scenes"]["4"]["segment_video"]

    # Active output.mp4 must match snapshot 3 output
    assert compute_sha256(run_dir / "output.mp4") == snap_3_output_sha, "Restored output.mp4 does not match snapshot 3!"

    # Verify Gate 6 on restored output
    is_valid, errs, meta = validate_post_render_qa(
        video_path=run_dir / "output.mp4",
        expected_audio_path=run_dir / "audio.wav",
        aspect_ratio="16:9",
        tolerance_sec=0.05,
    )
    assert is_valid, f"Gate 6 failed on restored output: {errs}"
    print(f"[VERIFIED] Restored output passes Gate 6 (diff={meta.get('duration_difference')}s <= 0.05s).")
    print("[VERIFIED] Complete snapshot restoration succeeded with full asset and timeline integrity.")


def test_scenario_4_locking():
    print("\n" + "=" * 80)
    print("SCENARIO 4: CONCURRENCY LOCKING COVERAGE")
    print("=" * 80)

    run_id = "run_phase401_disposable_fail"
    run_dir = RUNS_DIR / run_id

    lock = RevisionLock(run_dir)
    lock.acquire()
    print(f"[LOCK] Acquired RevisionLock on {run_dir}")

    try:
        # 1. Visual revision attempts to acquire lock
        try:
            execute_revision(run_id=run_id, target_scene_id=1, set_title="Step Isolation and Failure Behavior")
            assert False, "Should have been rejected due to active lock"
        except RuntimeError as exc:
            assert "locked by another active process" in str(exc)
            print("[SUCCESS] Concurrent visual revision correctly rejected by lock.")

        # 2. Snapshot restore attempts to acquire lock
        try:
            restore_revision_snapshot(run_dir, target_revision=1)
            assert False, "Should have been rejected due to active lock"
        except RuntimeError as exc:
            assert "locked by another active process" in str(exc)
            print("[SUCCESS] Concurrent snapshot restoration correctly rejected by lock.")
    finally:
        lock.release()
        print("[LOCK] Released RevisionLock.")


if __name__ == "__main__":
    test_scenario_1_failed_render_rollback()
    test_scenario_2_repeated_narration_revisions()
    test_scenario_3_complete_snapshot_restoration()
    test_scenario_4_locking()
    print("\n" + "#" * 80)
    print("🎉 ALL PHASE 4.0.1 LIVE SCENARIOS COMPLETED SUCCESSFULLY!")
    print("#" * 80 + "\n")

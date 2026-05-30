#!/usr/bin/env python3
import os
import sys
import json
import base64
import time
import glob
import textwrap
import subprocess
import shutil
import random
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ================= 路径配置 (使用 resolve() 获取绝对路径) =================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
BATCH_INPUT_DIR = OUTPUT_DIR / "batch_input"
BATCH_OUTPUT_DIR = OUTPUT_DIR / "batch_output"
FFMPEG_DIR = BASE_DIR / "ffmpeg"

# 兼容 Windows/Linux
if sys.platform == "win32":
    FFMPEG_BIN = FFMPEG_DIR / "ffmpeg.exe"
    FFPROBE_BIN = FFMPEG_DIR / "ffprobe.exe"
else:
    FFMPEG_BIN = FFMPEG_DIR / "ffmpeg"
    FFPROBE_BIN = FFMPEG_DIR / "ffprobe"

FONT_PATH = FFMPEG_DIR / "font.ttf"

# 初始化目录
for p in [OUTPUT_DIR, BATCH_INPUT_DIR, BATCH_OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# ================= 辅助函数 =================

def get_audio_duration(audio_path):
    try:
        cmd = [str(FFMPEG_BIN), '-i', str(audio_path)]
        # 必须使用 stderr 捕获输出，并设置 errors='ignore' 防止编码报错
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        import re
        match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
        if match:
            h, m, s = match.groups()
            return float(h)*3600 + float(m)*60 + float(s)
        return 5.0
    except Exception as e:
        print(f"[Warn] 获取时长失败: {e}")
        return 5.0

def get_image_size(image_path):
    try:
        cmd = [str(FFMPEG_BIN), '-i', str(image_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        import re
        match = re.search(r"Stream #\d+:\d+: Video: \w+.*? (\d+)x(\d+)", result.stderr)
        if match:
            w, h = match.groups()
            return int(w), int(h)
        return 1280, 720
    except Exception as e:
        print(f"[Warn] 获取图片尺寸失败: {e}")
        return 1280, 720

def get_project_paths(project_name, is_batch=False, batch_task_name=None):
    """统一路径管理：output/ProjectName/..."""
    if is_batch:
        root = BATCH_OUTPUT_DIR / batch_task_name / project_name
        role_dir = BATCH_OUTPUT_DIR / batch_task_name / "role"
        final_dir = BATCH_OUTPUT_DIR / batch_task_name
    else:
        root = OUTPUT_DIR / project_name
        role_dir = root / "role"
        final_dir = root

    paths = {
        "root": root,
        "image": root / "image",
        "audio": root / "audio",
        "subtitle": root / "subtitle",
        "role": role_dir,
        "final": final_dir
    }
    for k, p in paths.items():
        if k not in ['root', 'final']: p.mkdir(parents=True, exist_ok=True)
    paths['root'].mkdir(parents=True, exist_ok=True)
    paths['final'].mkdir(parents=True, exist_ok=True)
    return paths

def get_visual_effects(img_w, img_h, duration_sec, move_type):
    """
    生成复合滤镜链：运镜(Zoom/Pan/Shake) + 视觉特效(Vignette/Noise/Color)
    确保动画全程持续，绝不静止。
    """
    fps = 120
    total_frames = int(duration_sec * fps)
    d_param = total_frames + 60
    
    s_size = f"{img_w}x{img_h}"
    
    if move_type == "zoom_in":
        z = "1.0+(0.15*on/duration)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
        
    elif move_type == "zoom_out":
        z = "1.15-(0.15*on/duration)" 
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
        
    elif move_type == "pan_right":
        z = "1.1"
        x = "(iw-iw/zoom)*(on/duration)"
        y = "ih/2-(ih/zoom/2)"
        
    elif move_type == "pan_left":
        z = "1.1"
        x = "(iw-iw/zoom)*(1-on/duration)"
        y = "ih/2-(ih/zoom/2)"
        
    elif move_type == "pan_up":
        z = "1.1"
        x = "iw/2-(iw/zoom/2)"
        y = "(ih-ih/zoom)*(1-on/duration)"
        
    elif move_type == "shake":
        z = "1.05+(0.05*on/duration)"
        x = "iw/2-(iw/zoom/2)+2*sin(on/2)"
        y = "ih/2-(ih/zoom/2)+2*cos(on/3)"
        
    else:
        z = "1.0+(0.1*on/duration)"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"

    base_vf = f"zoompan=z='{z}':x='{x}':y='{y}':d={d_param}:s={s_size}:fps={fps}"

    fx_options = ["none", "vignette", "grain", "warm", "cool", "pulse"]
    fx_weights = [0.2, 0.3, 0.3, 0.05, 0.05, 0.1]
    
    fx_type = random.choices(fx_options, weights=fx_weights, k=1)[0]
    fx_vf = ""
    
    if fx_type == "vignette":
        fx_vf = ",vignette=PI/4"
        
    elif fx_type == "grain":
        fx_vf = ",noise=alls=10:allf=t+u"
        
    elif fx_type == "warm":
        fx_vf = ",curves=r='0/0 1/1':g='0/0 1/0.9':b='0/0 1/0.8'"
        
    elif fx_type == "cool":
        fx_vf = ",curves=r='0/0 1/0.8':g='0/0 1/0.9':b='0/0 1/1'"
        
    elif fx_type == "pulse":
        fx_vf = ",eq=brightness=0.05*sin(t*2)"

    return base_vf + fx_vf

# ================= 接口 =================

@app.route('/scan_batch', methods=['GET'])
def scan_batch():
    files = sorted(glob.glob(str(BATCH_INPUT_DIR / "*.txt")))
    file_list = []
    for f in files:
        p = Path(f)
        try:
            content = p.read_text(encoding='utf-8')
        except:
            content = p.read_text(encoding='gbk', errors='ignore')
        file_list.append({"filename": p.stem, "content": content})
    return jsonify({"count": len(file_list), "files": file_list})

@app.route('/check_role', methods=['POST'])
def check_role():
    data = request.json
    paths = get_project_paths("temp", data.get('isBatch', False), data.get('batchTaskName', 'default'))
    role_file = paths['role'] / f"{data.get('name')}.txt"
    if role_file.exists():
        return jsonify({"exists": True, "description": role_file.read_text(encoding='utf-8')})
    return jsonify({"exists": False})

@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        data = request.json
        paths = get_project_paths(data.get('projectName'), data.get('isBatch', False), data.get('batchTaskName', ''))
        
        type_ = data.get('type')
        index = data.get('index', 0)
        content = data.get('content')
        
        filename = ""
        if type_ == 'role':
            f = paths['role'] / f"{content.get('name')}.txt"
            f.write_text(content.get('tags'), encoding='utf-8')
            filename = f.name
        elif type_ == 'image':
            f = paths['image'] / f"{index:03d}.png"
            if ',' in content: content = content.split(',')[1]
            f.write_bytes(base64.b64decode(content))
            filename = f.name
        elif type_ == 'audio':
            f = paths['audio'] / f"{index:03d}.wav"
            if ',' in content: content = content.split(',')[1]
            f.write_bytes(base64.b64decode(content))
            filename = f.name
        elif type_ == 'subtitle':
            f = paths['subtitle'] / f"{index:03d}.txt"
            f.write_text(content, encoding='utf-8')
            filename = f.name
        elif type_ == 'video_clip':
            video_dir = paths['root'] / "video"
            video_dir.mkdir(exist_ok=True)
            f = video_dir / f"{index:03d}.mp4"
            if ',' in content: content = content.split(',')[1]
            f.write_bytes(base64.b64decode(content))
            filename = f.name

        return jsonify({"status": "ok", "path": str(filename)})
    except Exception as e:
        print(f"[Error] Save: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/render_video', methods=['POST'])
def render_video():
    try:
        data = request.json
        project_name = data.get('projectName')
        enable_subtitle = data.get('enableSubtitle', True)
        paths = get_project_paths(project_name, data.get('isBatch', False), data.get('batchTaskName', ''))
        
        images = sorted(list(paths['image'].glob("*.png")))
        audios = sorted(list(paths['audio'].glob("*.wav")))
        subtitles = sorted(list(paths['subtitle'].glob("*.txt")))
        
        video_dir = paths['root'] / "video"
        video_clips = sorted(list(video_dir.glob("*.mp4"))) if video_dir.exists() else []
        
        is_video_mode = len(video_clips) > 0 and len(video_clips) >= len(audios)
        
        if not images and not video_clips: 
            return jsonify({"error": "No images or videos found"}), 400
        
        count = len(audios)
        print(f"[Info] Rendering {project_name}: {count} clips (Mode: {'VIDEO' if is_video_mode else 'IMAGE'}, Subtitle: {'ON' if enable_subtitle else 'OFF'})")
        
        temp_dir = paths['root'] / "temp_render"
        if temp_dir.exists(): shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        video_parts = []
        
        for i in range(count):
            aud_path = str(audios[i].resolve())
            sub_text = subtitles[i].read_text(encoding='utf-8').strip()
            
            font_path_str = "ffmpeg/font.ttf"
            text_vf = "null"
            if enable_subtitle:
                lines = textwrap.wrap(sub_text, 18)
                drawtext_filters = []
                for idx, line in enumerate(lines):
                    y_off = (len(lines)-1-idx)*60
                    safe_line = line.replace("'", "").replace(":", "")
                    drawtext_filters.append(
                        f"drawtext=fontfile='{font_path_str}':text='{safe_line}':fontsize=40:fontcolor=yellow:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-180-{y_off}"
                    )
                text_vf = ",".join(drawtext_filters) if drawtext_filters else "null"
            
            part_out = temp_dir / f"part_{i:03d}.mp4"
            target_duration = get_audio_duration(aud_path)
            if target_duration < 2.0: target_duration = 2.0

            if is_video_mode:
                vid_path = str(video_clips[i].resolve())
                
                try:
                    res = subprocess.run([str(FFMPEG_BIN), '-i', vid_path], capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    import re
                    m = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", res.stderr)
                    orig_dur = float(m.group(1))*3600 + float(m.group(2))*60 + float(m.group(3)) if m else 5.0
                except: orig_dur = 5.0

                time_scale = target_duration / orig_dur
                
                vf = f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setpts={time_scale}*PTS,{text_vf}"
                
                cmd = [
                    str(FFMPEG_BIN), '-y',
                    '-i', vid_path,
                    '-i', aud_path,
                    '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac',
                    '-t', str(target_duration),
                    str(part_out.resolve())
                ]
            else:
                img_path = str(images[i].resolve())
                img_w, img_h = get_image_size(img_path)
                if img_w % 2 != 0: img_w -= 1
                if img_h % 2 != 0: img_h -= 1
                
                move_types = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "shake"]
                move = random.choice(move_types)
                visual_vf = get_visual_effects(img_w, img_h, target_duration, move)
                vf = f"{visual_vf},{text_vf}"

                cmd = [
                    str(FFMPEG_BIN), '-y',
                    '-loop', '1', '-i', img_path,
                    '-i', aud_path,
                    '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac',
                    '-t', str(target_duration),
                    str(part_out.resolve())
                ]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            video_parts.append(str(part_out.resolve()))

        concat_list = temp_dir / "concat.txt"
        with open(concat_list, 'w', encoding='utf-8') as f:
            for v in video_parts:
                f.write(f"file '{v.replace(os.sep, '/')}'\n")
        
        merged_mp4 = temp_dir / "merged.mp4"
        subprocess.run([
            str(FFMPEG_BIN), '-y', '-f', 'concat', '-safe', '0',
            '-i', str(concat_list.resolve()), '-c', 'copy', str(merged_mp4.resolve())
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        
        final_output = paths['final'] / f"{project_name}_final.mp4"
        bgm_base64 = data.get('bgm')
        
        if bgm_base64:
            bgm_path = temp_dir / "bgm.mp3"
            if ',' in bgm_base64: bgm_base64 = bgm_base64.split(',')[1]
            bgm_path.write_bytes(base64.b64decode(bgm_base64))
            
            subprocess.run([
                str(FFMPEG_BIN), '-y', '-i', str(merged_mp4.resolve()),
                '-stream_loop', '-1', '-i', str(bgm_path.resolve()),
                '-filter_complex', '[0:a]volume=1.0[v];[1:a]volume=0.2[b];[v][b]amix=inputs=2:duration=first',
                '-c:v', 'copy', '-c:a', 'aac', str(final_output.resolve())
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        else:
            shutil.move(str(merged_mp4), str(final_output))

        relative_path = final_output.relative_to(OUTPUT_DIR)
        url_path = str(relative_path).replace(os.sep, '/')

        return jsonify({"status": "ok", "url": url_path})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/output/<path:filename>')
def download_file(filename):
    try:
        safe_path = (OUTPUT_DIR / filename).resolve()
        if not str(safe_path).startswith(str(OUTPUT_DIR.resolve())):
            return jsonify({"error": "Invalid path"}), 403
        if safe_path.exists() and safe_path.is_file():
            return send_file(str(safe_path))
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"Server V4.0 Ready. FFmpeg: {FFMPEG_BIN}")
    app.run(host='0.0.0.0', port=5001, debug=False)

#!/usr/bin/env python3
"""
Kinetic Motion Design Intro Generator for Aritro Saha's GitHub Profile
Paced down for optimal readability (11.2s runtime @ 25 FPS, 280 frames).

Usage:
  python3 scripts/generate_intro.py [--format gif|mp4|webm|all]
"""

import argparse
import math
import os
import random
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio

WIDTH = 960
HEIGHT = 320
FPS = 25
TOTAL_FRAMES = 280  # 11.2 seconds, paced comfortably for readability

def load_fonts():
    fonts = {}
    try:
        fonts["hero"] = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 62)
        fonts["bms"] = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 44)
        fonts["stack"] = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Black.ttf', 44)
        fonts["title"] = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 24)
        fonts["subtitle"] = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 16)
        fonts["tag"] = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 13)
        fonts["mono"] = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 13)
        fonts["mono_sm"] = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 11)
        fonts["mono_xs"] = ImageFont.truetype('/System/Library/Fonts/SFNSMono.ttf', 9)
    except Exception:
        default = ImageFont.load_default()
        for k in ["hero", "bms", "stack", "title", "subtitle", "tag", "mono", "mono_sm", "mono_xs"]:
            fonts[k] = default
    return fonts

FONTS = load_fonts()

def get_text_w(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]

def ease_out_expo(t):
    return 1.0 if t >= 1.0 else 1.0 - math.pow(2, -10 * t)

def ease_out_back(t, s=1.4):
    t -= 1.0
    return (t * t * ((s + 1) * t + s) + 1.0)

def draw_perspective_grid(draw, frame_idx, speed=1.2, color=(16, 26, 46)):
    horizon_y = HEIGHT // 2
    cx = WIDTH // 2
    cy = horizon_y
    
    num_radials = 18
    for i in range(num_radials + 1):
        x_target = (i / num_radials) * WIDTH
        draw.line([(cx, cy), (x_target, HEIGHT)], fill=color, width=1)
        draw.line([(cx, cy), (x_target, 0)], fill=color, width=1)
    
    offset = (frame_idx * speed * 4) % 40
    for d in range(1, 10):
        y_frac = math.pow((d * 20 + offset) / 220, 2)
        if y_frac <= 1.0:
            y_bot = int(cy + y_frac * (HEIGHT - cy))
            y_top = int(cy - y_frac * cy)
            alpha = int(255 * y_frac)
            c = (min(255, color[0] + alpha//6), min(255, color[1] + alpha//4), min(255, color[2] + alpha//2))
            draw.line([(0, y_bot), (WIDTH, y_bot)], fill=c, width=1)
            draw.line([(0, y_top), (WIDTH, y_top)], fill=c, width=1)

def draw_hud_brackets(draw, color=(56, 189, 248), margin=18, size=16, width=2):
    draw.line([(margin, margin), (margin + size, margin)], fill=color, width=width)
    draw.line([(margin, margin), (margin, margin + size)], fill=color, width=width)
    draw.line([(WIDTH - margin, margin), (WIDTH - margin - size, margin)], fill=color, width=width)
    draw.line([(WIDTH - margin, margin), (WIDTH - margin, margin + size)], fill=color, width=width)
    draw.line([(margin, HEIGHT - margin), (margin + size, HEIGHT - margin)], fill=color, width=width)
    draw.line([(margin, HEIGHT - margin), (margin, HEIGHT - margin - size)], fill=color, width=width)
    draw.line([(WIDTH - margin, HEIGHT - margin), (WIDTH - margin - size, HEIGHT - margin)], fill=color, width=width)
    draw.line([(WIDTH - margin, HEIGHT - margin), (WIDTH - margin, HEIGHT - margin - size)], fill=color, width=width)

def draw_lens_flare(img, cx, cy, radius_x=420, radius_y=3, color=(120, 200, 255)):
    flare_layer = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    f_draw = ImageDraw.Draw(flare_layer)
    f_draw.ellipse([cx - radius_x, cy - radius_y*4, cx + radius_x, cy + radius_y*4], fill=(*color, 35))
    f_draw.ellipse([cx - radius_x*0.7, cy - radius_y*1.5, cx + radius_x*0.7, cy + radius_y*1.5], fill=(*color, 95))
    f_draw.ellipse([cx - 40, cy - 6, cx + 40, cy + 6], fill=(255, 255, 255, 210))
    flare_blurred = flare_layer.filter(ImageFilter.GaussianBlur(radius=2))
    img.alpha_composite(flare_blurred)

def apply_chromatic_split(pil_img, offset_x=6, slice_h=0):
    img_np = np.array(pil_img.convert('RGB'))
    h, w, _ = img_np.shape
    r = img_np[:, :, 0]
    g = img_np[:, :, 1]
    b = img_np[:, :, 2]
    
    r_shifted = np.roll(r, offset_x, axis=1)
    b_shifted = np.roll(b, -offset_x, axis=1)
    
    if slice_h > 0:
        y1 = random.randint(30, h - 50)
        y2 = min(h, y1 + slice_h)
        shift_slice = random.choice([-16, -10, 10, 16])
        r_shifted[y1:y2, :] = np.roll(r_shifted[y1:y2, :], shift_slice, axis=1)
        g[y1:y2, :] = np.roll(g[y1:y2, :], shift_slice // 2, axis=1)
        b_shifted[y1:y2, :] = np.roll(b_shifted[y1:y2, :], -shift_slice, axis=1)
        
    merged = np.stack([r_shifted, g, b_shifted], axis=2)
    return Image.fromarray(merged).convert('RGBA')

def draw_audio_equalizer(draw, x_start, y_base, width, height, frame_idx):
    num_bars = 48
    bar_w = width / num_bars
    for i in range(num_bars):
        phase = frame_idx * 0.22 + i * 0.38
        h_factor = (math.sin(phase) * 0.45 + math.sin(phase * 2.2) * 0.35 + math.sin(phase * 0.65) * 0.2 + 1.0) / 2.0
        bar_h = max(3, int(h_factor * height))
        bx = int(x_start + i * bar_w)
        col = (
            int(56 + 120 * (i / num_bars)),
            int(189 - 50 * (i / num_bars)),
            int(248 + 7 * (i / num_bars))
        )
        draw.rectangle([bx, y_base - bar_h, bx + int(bar_w - 2), y_base], fill=col)

def draw_unified_top_hud(draw, f):
    top_y = 20
    radar_pulse = (f % 20) / 20.0
    r_size = int(3 + radar_pulse * 4)
    draw.ellipse([42 - r_size, top_y + 8 - r_size, 42 + r_size, top_y + 8 + r_size], outline=(34, 197, 94), width=1)
    draw.ellipse([39, top_y + 5, 45, top_y + 11], fill=(34, 197, 94))
    
    draw.text((54, top_y + 1), "SYS_ONLINE // HYD, IN", fill=(226, 232, 240), font=FONTS["mono_sm"])
    
    center_text = "17.3850° N, 78.4867° E • BRISTOL MYERS SQUIBB"
    cw = get_text_w(draw, center_text, FONTS["mono_sm"])
    draw.text(((WIDTH - cw) // 2, top_y + 1), center_text, fill=(148, 163, 184), font=FONTS["mono_sm"])
    
    right_text = "SE-1 // PROD_ACTIVE"
    rw = get_text_w(draw, right_text, FONTS["mono_sm"])
    draw.text((WIDTH - 42 - rw, top_y + 1), right_text, fill=(56, 189, 248), font=FONTS["mono_sm"])
    
    draw.line([(38, top_y + 20), (WIDTH - 38, top_y + 20)], fill=(255, 255, 255, 20), width=1)

def render_frame(f):
    img = Image.new('RGBA', (WIDTH, HEIGHT), (4, 6, 12, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([1, 1, WIDTH - 2, HEIGHT - 2], outline=(255, 255, 255, 24), width=1)
    
    # -----------------------------------------------------------------
    # Scene 1: Initializing & Lock-On (Frames 0 to 34 • 1.4s)
    # -----------------------------------------------------------------
    if 0 <= f <= 34:
        progress = f / 35.0
        draw_perspective_grid(draw, f, speed=1.2 + progress * 1.5, color=(18, 32, 54))
        draw_unified_top_hud(draw, f)
        
        cx, cy = WIDTH // 2, HEIGHT // 2 + 10
        angle = f * 0.12
        r_cross = int(46 + 12 * math.sin(f * 0.18))
        for a_off in [0, math.pi/2, math.pi, 3*math.pi/2]:
            x1 = cx + int(r_cross * math.cos(angle + a_off))
            y1 = cy + int(r_cross * math.sin(angle + a_off))
            x2 = cx + int((r_cross + 16) * math.cos(angle + a_off))
            y2 = cy + int((r_cross + 16) * math.sin(angle + a_off))
            draw.line([(x1, y1), (x2, y2)], fill=(56, 189, 248), width=2)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255))
        
        msg_chars = int(min(28, f * 1.0))
        full_msg = "INITIALIZING AGENT PROFILE..."[:msg_chars]
        mw = get_text_w(draw, full_msg, FONTS["mono"])
        draw.text(((WIDTH - mw) // 2, cy + 70), full_msg, fill=(255, 255, 255), font=FONTS["mono"])
        
        sub_init = f"ADDRESS: 0x7F{f:02X}A9 • PROTOCOL: V3.8_STREAM"
        sw = get_text_w(draw, sub_init, FONTS["mono_sm"])
        draw.text(((WIDTH - sw) // 2, cy + 92), sub_init, fill=(100, 116, 139), font=FONTS["mono_sm"])
        draw_hud_brackets(draw, (56, 189, 248), margin=18, size=16)
        
        if 31 <= f <= 34:
            img = apply_chromatic_split(img, offset_x=10, slice_h=20)
            if f % 2 == 1:
                strobe = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 80))
                img.alpha_composite(strobe)

    # -----------------------------------------------------------------
    # Scene 2: Kinetic Impact Slam — "ARITRO SAHA" (Frames 35 to 84 • 2.0s)
    # -----------------------------------------------------------------
    elif 35 <= f <= 84:
        sf = f - 35
        dur = 50.0
        p = min(1.0, sf / 14.0)
        
        shake_x, shake_y = 0, 0
        if sf < 6:
            intensity = int((6 - sf) * 2)
            shake_x = random.randint(-intensity, intensity)
            shake_y = random.randint(-intensity, intensity)
            
        draw_perspective_grid(draw, f, speed=2.5, color=(16, 32, 58))
        draw_unified_top_hud(draw, f)
        
        sw_radius = int(sf * 18)
        if sw_radius < 520:
            draw.ellipse([WIDTH//2 - sw_radius, HEIGHT//2 + 5 - sw_radius//2,
                          WIDTH//2 + sw_radius, HEIGHT//2 + 5 + sw_radius//2],
                         outline=(56, 189, 248), width=2)
                         
        title_text = "ARITRO SAHA"
        tw = get_text_w(draw, title_text, FONTS["hero"])
        title_x = (WIDTH - tw) // 2 + shake_x
        title_y = HEIGHT // 2 - 38 + shake_y
        
        draw.text((title_x - 2, title_y - 2), title_text, fill=(56, 189, 248), font=FONTS["hero"])
        draw.text((title_x, title_y), title_text, fill=(255, 255, 255), font=FONTS["hero"])
        
        # Subtitle slides in cleanly and stays readable for 40+ frames
        sub_p = min(1.0, max(0.0, (sf - 8) / 10.0))
        sub_y = int(title_y + 82 - (1.0 - ease_out_expo(sub_p)) * 20)
        sub_text = "SOFTWARE ENGINEER 1  •  BRISTOL MYERS SQUIBB"
        sub_w = get_text_w(draw, sub_text, FONTS["mono"])
        badge_w = sub_w + 36
        badge_x = (WIDTH - badge_w) // 2
        
        draw.rectangle([badge_x, sub_y, badge_x + badge_w, sub_y + 32], fill=(15, 23, 42), outline=(56, 189, 248), width=1)
        draw.text(((WIDTH - sub_w) // 2, sub_y + 8), sub_text, fill=(255, 255, 255), font=FONTS["mono"])
        
        flare_x = int((sf / dur) * (WIDTH + 400) - 200)
        draw_lens_flare(img, flare_x, title_y + 35, radius_x=380, radius_y=3, color=(56, 189, 248))
        draw_hud_brackets(draw, (56, 189, 248), margin=18, size=16)
        
        if 81 <= f <= 84:
            img = apply_chromatic_split(img, offset_x=12, slice_h=25)

    # -----------------------------------------------------------------
    # Scene 3: Enterprise Cut — "BRISTOL MYERS SQUIBB" (Frames 85 to 134 • 2.0s)
    # -----------------------------------------------------------------
    elif 85 <= f <= 134:
        sf = f - 85
        dur = 50.0
        p = min(1.0, sf / 10.0)
        
        draw_perspective_grid(draw, f, speed=1.8, color=(24, 20, 48))
        draw_unified_top_hud(draw, f)
        
        node_coords = [
            (120, 90), (220, 220), (360, 110), (500, 240),
            (640, 100), (820, 210), (460, 70), (300, 250)
        ]
        for i, (nx, ny) in enumerate(node_coords):
            draw.ellipse([nx - 4, ny - 4, nx + 4, ny + 4], fill=(129, 140, 248))
            next_pt = node_coords[(i + 1) % len(node_coords)]
            draw.line([(nx, ny), next_pt], fill=(99, 102, 241, 50), width=1)
            
        bms_text = "BRISTOL MYERS SQUIBB"
        bw = get_text_w(draw, bms_text, FONTS["bms"])
        slide_offset = int((1.0 - ease_out_expo(p)) * 50)
        bms_y = HEIGHT // 2 - 40
        draw.text(((WIDTH - bw) // 2 + slide_offset, bms_y), bms_text, fill=(255, 255, 255), font=FONTS["bms"])
        
        ent_text = "ENTERPRISE BIG DATA & GENAI SYSTEMS"
        ew = get_text_w(draw, ent_text, FONTS["mono"])
        ebadge_w = ew + 40
        ebadge_x = (WIDTH - ebadge_w) // 2
        badge_y = bms_y + 64
        draw.rectangle([ebadge_x, badge_y, ebadge_x + ebadge_w, badge_y + 30], fill=(30, 27, 75), outline=(129, 140, 248), width=1)
        draw.text(((WIDTH - ew) // 2, badge_y + 7), ent_text, fill=(224, 231, 255), font=FONTS["mono"])
        
        tele_text = "THROUGHPUT: 2.8 TB/S   |   LATENCY: 3.4ms   |   CLUSTER: HYD_PROD"
        tw = get_text_w(draw, tele_text, FONTS["mono_sm"])
        draw.text(((WIDTH - tw) // 2, badge_y + 42), tele_text, fill=(148, 163, 184), font=FONTS["mono_sm"])
        
        draw_lens_flare(img, WIDTH // 2 + 150, bms_y + 20, radius_x=280, radius_y=3, color=(129, 140, 248))
        draw_hud_brackets(draw, (129, 140, 248), margin=18, size=16)
        
        if 131 <= f <= 134:
            img = apply_chromatic_split(img, offset_x=12, slice_h=25)

    # -----------------------------------------------------------------
    # Scene 4: Tech Stack Arsenal (Frames 135 to 214 • 3.2s, 0.8s per beat)
    # -----------------------------------------------------------------
    elif 135 <= f <= 214:
        sf = f - 135
        beat_frames = 20  # 20 frames = 0.8s per beat (ample time to read)
        beat = sf // beat_frames
        beat_f = sf % beat_frames
        bp = beat_f / float(beat_frames)
        
        beats_data = [
            {
                "num": "01",
                "name": "PYTHON",
                "sub": "SYSTEMS • ASYNCIO • PIPELINES • ARCHITECTURE",
                "color": (56, 189, 248),
                "bg_accent": (8, 28, 48),
                "code": "def ingest_stream(source: Kafka) -> DeltaLake: yield model.infer()"
            },
            {
                "num": "02",
                "name": "AWS CLOUD",
                "sub": "S3 • LAMBDA • ECS • GLUE • KINESIS • INFRASTRUCTURE",
                "color": (245, 158, 11),
                "bg_accent": (42, 24, 6),
                "code": "aws.cloudformation.deploy(stack='production-lakehouse-v2')"
            },
            {
                "num": "03",
                "name": "DATABRICKS",
                "sub": "APACHE SPARK • DELTA LAKE • MEDALLION ARCHITECTURE",
                "color": (239, 68, 68),
                "bg_accent": (42, 12, 12),
                "code": "spark.readStream.format('delta').load('/lake/gold').writeStream()"
            },
            {
                "num": "04",
                "name": "GENAI & AGENTS",
                "sub": "AUTONOMOUS AGENTS • MULTIMODAL • RAG PIPELINES",
                "color": (168, 85, 247),
                "bg_accent": (32, 10, 48),
                "code": "agent = ReActCoordinator(llm=GeminiFlash, memory=VectorLake)"
            }
        ]
        
        cur = beats_data[min(3, beat)]
        col = cur["color"]
        
        draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(*cur["bg_accent"], 255))
        draw_perspective_grid(draw, f, speed=2.5, color=(col[0]//4, col[1]//4, col[2]//4))
        draw_unified_top_hud(draw, f)
        
        card_w = 760
        card_h = 175
        card_x = (WIDTH - card_w) // 2
        card_y = 70
        
        draw.rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                       fill=(10, 14, 24, 230), outline=(*col, 160), width=1)
                       
        card_tag = f"[ STACK {cur['num']} / 04 ]  •  CORE COMPETENCY"
        draw.text((card_x + 24, card_y + 14), card_tag, fill=col, font=FONTS["mono_sm"])
        
        # Smooth ease-in for first 4 frames, then locked for 16 frames of readability
        scale_in = (1.0 - ease_out_expo(min(1.0, bp * 4.0))) * 20
        title_text = f"{cur['num']} // {cur['name']}"
        tw = get_text_w(draw, title_text, FONTS["stack"])
        draw.text(((WIDTH - tw) // 2, card_y + 38 + int(scale_in)), title_text, fill=(255, 255, 255), font=FONTS["stack"])
        
        sub_text = cur["sub"]
        sub_w = get_text_w(draw, sub_text, FONTS["title"])
        draw.text(((WIDTH - sub_w) // 2, card_y + 94), sub_text, fill=col, font=FONTS["title"])
        
        code_w = 680
        code_h = 28
        code_x = (WIDTH - code_w) // 2
        code_y = card_y + 130
        draw.rectangle([code_x, code_y, code_x + code_w, code_y + code_h], fill=(5, 8, 15), outline=(*col, 120), width=1)
        code_txt_w = get_text_w(draw, cur["code"], FONTS["mono"])
        draw.text(((WIDTH - code_txt_w) // 2, code_y + 6), cur["code"], fill=(203, 213, 225), font=FONTS["mono"])
        
        draw_lens_flare(img, WIDTH // 2 + 180, card_y + 60, radius_x=280, radius_y=3, color=col)
        draw_hud_brackets(draw, col, margin=18, size=16)
        
        # Subtle glitch transition on final 2 frames of each beat
        if beat_f >= 18:
            img = apply_chromatic_split(img, offset_x=10, slice_h=18)

    # -----------------------------------------------------------------
    # Scene 5: Grand Climax & Master Console (Frames 215 to 279 • 2.6s)
    # -----------------------------------------------------------------
    else:
        sf = f - 215
        dur = 65.0
        p = min(1.0, sf / 14.0)
        
        draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(4, 6, 12, 255))
        draw_perspective_grid(draw, f, speed=0.8, color=(15, 25, 45))
        draw_unified_top_hud(draw, f)
        
        hero_text = "ARITRO SAHA"
        hw = get_text_w(draw, hero_text, FONTS["hero"])
        hero_x = (WIDTH - hw) // 2
        hero_y = HEIGHT // 2 - 52
        
        sheen_offset = int(math.sin(sf * 0.18) * 5)
        draw.text((hero_x, hero_y), hero_text, fill=(56, 189, 248), font=FONTS["hero"])
        draw.text((hero_x + sheen_offset, hero_y), hero_text, fill=(255, 255, 255), font=FONTS["hero"])
        
        sub_text = "BIG DATA ARCHITECTURE  •  GENAI  •  CLOUD PLATFORMS"
        sub_w = get_text_w(draw, sub_text, FONTS["subtitle"])
        draw.text(((WIDTH - sub_w) // 2, hero_y + 72), sub_text, fill=(203, 213, 225), font=FONTS["subtitle"])
        
        chips_data = [
            ("PYTHON", (56, 189, 248)),
            ("AWS CLOUD", (245, 158, 11)),
            ("DATABRICKS", (239, 68, 68)),
            ("GENAI & LLMS", (168, 85, 247))
        ]
        
        gap = 14
        chip_widths = []
        for c_name, _ in chips_data:
            cw = get_text_w(draw, c_name, FONTS["tag"]) + 32
            chip_widths.append(cw)
        total_chips_w = sum(chip_widths) + gap * (len(chips_data) - 1)
        start_chip_x = (WIDTH - total_chips_w) // 2
        chip_y = hero_y + 102
        
        cur_cx = start_chip_x
        for (c_name, c_col), cw in zip(chips_data, chip_widths):
            draw.rectangle([cur_cx, chip_y, cur_cx + cw, chip_y + 24], fill=(15, 23, 42), outline=c_col, width=1)
            draw.ellipse([cur_cx + 8, chip_y + 8, cur_cx + 14, chip_y + 14], fill=c_col)
            draw.text((cur_cx + 20, chip_y + 4), c_name, fill=(255, 255, 255), font=FONTS["tag"])
            cur_cx += cw + gap
            
        eq_w = 720
        draw_audio_equalizer(draw, (WIDTH - eq_w) // 2, HEIGHT - 18, eq_w, 20, f)
        
        laser_x = int((sf / dur) * WIDTH)
        draw.line([(0, 1), (WIDTH, 1)], fill=(56, 189, 248, 70), width=1)
        draw.line([(laser_x - 50, 1), (laser_x + 50, 1)], fill=(255, 255, 255), width=2)
        draw_hud_brackets(draw, (56, 189, 248), margin=18, size=16)
        
        if f >= 277:
            img = apply_chromatic_split(img, offset_x=6, slice_h=15)
            
    return img.convert('RGB')

def main():
    parser = argparse.ArgumentParser(description="Generate profile motion design intro")
    parser.add_argument("--format", choices=["gif", "mp4", "webm", "all"], default="gif", help="Output format to render")
    args = parser.parse_args()

    os.makedirs("assets", exist_ok=True)

    print(f"Rendering {TOTAL_FRAMES} motion design frames ({TOTAL_FRAMES/FPS:.1f}s @ {FPS} FPS)...")
    frames = []
    for i in range(TOTAL_FRAMES):
        if i % 35 == 0:
            print(f"Rendered frame {i}/{TOTAL_FRAMES} ({(i/TOTAL_FRAMES)*100:.0f}%)...")
        frames.append(render_frame(i))
    print("All frames rendered!")

    # GIF
    if args.format in ["gif", "all"]:
        gif_path = "assets/intro-motion.gif"
        print(f"Quantizing and encoding {gif_path}...")
        pil_frames = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for f in frames]
        pil_frames[0].save(
            gif_path,
            save_all=True,
            append_images=pil_frames[1:],
            duration=int(1000 / FPS),
            loop=0,
            optimize=True
        )
        print(f"Saved {gif_path} ({os.path.getsize(gif_path)} bytes)")

    # MP4
    if args.format in ["mp4", "all"]:
        mp4_path = "assets/intro-motion.mp4"
        print(f"Encoding {mp4_path}...")
        writer = imageio.get_writer(mp4_path, fps=FPS, codec='libx264', pixelformat='yuv420p', quality=9)
        for f in frames:
            writer.append_data(np.array(f))
        writer.close()
        print(f"Saved {mp4_path} ({os.path.getsize(mp4_path)} bytes)")

    # WebM
    if args.format in ["webm", "all"]:
        webm_path = "assets/intro-motion.webm"
        print(f"Encoding {webm_path}...")
        try:
            writer_webm = imageio.get_writer(webm_path, fps=FPS, codec='libvpx-vp9', pixelformat='yuv420p')
            for f in frames:
                writer_webm.append_data(np.array(f))
            writer_webm.close()
            print(f"Saved {webm_path} ({os.path.getsize(webm_path)} bytes)")
        except Exception as e:
            print(f"WebM error: {e}")

if __name__ == "__main__":
    main()

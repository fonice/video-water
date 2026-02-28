#!/usr/bin/env python3
"""
批量给视频添加素材或水印
使用 MoviePy 和 tkinter
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

try:
    from PIL import Image as _PILImage
    if not hasattr(_PILImage, "ANTIALIAS"):
        try:
            _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
        except Exception:
            _PILImage.ANTIALIAS = getattr(_PILImage, "LANCZOS", getattr(_PILImage, "BICUBIC", None))
except Exception:
    pass

# 尝试导入 moviepy，兼容 v2 与 v1
try:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
except Exception:
    try:
        from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
    except Exception:
        print("请先安装依赖: uv sync")
        sys.exit(1)


class VideoWatermarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("视频批量加水印工具")
        self.root.geometry("600x500")
        
        # 变量
        self.video_folder = tk.StringVar()
        self.watermark_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.watermark_position = tk.StringVar(value="右下角")
        self.watermark_size = tk.DoubleVar(value=0.2)  # 水印占视频的比例
        self.watermark_opacity = tk.DoubleVar(value=0.8)  # 水印不透明度
        self.is_processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="视频批量加水印工具", font=("Arial", 18, "bold"))
        title_label.pack(pady=10)
        
        # 视频文件夹选择
        folder_frame = ttk.LabelFrame(main_frame, text="视频文件夹", padding="10")
        folder_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(folder_frame, textvariable=self.video_folder, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_frame, text="选择", command=self.select_video_folder).pack(side=tk.LEFT)
        
        # 水印/素材选择
        watermark_frame = ttk.LabelFrame(main_frame, text="水印/素材文件 (图片或视频)", padding="10")
        watermark_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(watermark_frame, textvariable=self.watermark_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(watermark_frame, text="选择", command=self.select_watermark).pack(side=tk.LEFT)
        
        # 输出文件夹
        output_frame = ttk.LabelFrame(main_frame, text="输出文件夹", padding="10")
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Entry(output_frame, textvariable=self.output_folder, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="选择", command=self.select_output_folder).pack(side=tk.LEFT)
        
        # 水印设置
        settings_frame = ttk.LabelFrame(main_frame, text="水印设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)
        
        # 位置选择
        pos_frame = ttk.Frame(settings_frame)
        pos_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pos_frame, text="位置:").pack(side=tk.LEFT)
        positions = ["左上角", "右上角", "左下角", "右下角", "居中"]
        self.position_combo = ttk.Combobox(pos_frame, textvariable=self.watermark_position, 
                                           values=positions, state="readonly", width=15)
        self.position_combo.pack(side=tk.LEFT, padx=10)
        
        # 水印大小 - 使用 tk.Scale 替代 ttk.Scale
        size_frame = ttk.Frame(settings_frame)
        size_frame.pack(fill=tk.X, pady=5)
        ttk.Label(size_frame, text="大小比例:").pack(side=tk.LEFT)
        tk.Scale(size_frame, from_=0.05, to=0.5, orient=tk.HORIZONTAL, 
                  variable=self.watermark_size, length=300).pack(side=tk.LEFT, padx=10)
        ttk.Label(size_frame, textvariable=self.watermark_size).pack(side=tk.LEFT)
        
        # 不透明度
        opacity_frame = ttk.Frame(settings_frame)
        opacity_frame.pack(fill=tk.X, pady=5)
        ttk.Label(opacity_frame, text="不透明度:").pack(side=tk.LEFT)
        tk.Scale(opacity_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL,
                 resolution=0.05, variable=self.watermark_opacity, length=300).pack(side=tk.LEFT, padx=10)
        ttk.Label(opacity_frame, textvariable=self.watermark_opacity).pack(side=tk.LEFT)
        
        # 进度显示
        self.progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="10")
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.progress_label = ttk.Label(self.progress_frame, text="等待开始...")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_text = tk.Text(self.progress_frame, height=8, width=60, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)
    
    def select_video_folder(self):
        """选择视频文件夹"""
        folder = filedialog.askdirectory(title="选择视频文件夹")
        if folder:
            self.video_folder.set(folder)
    
    def select_watermark(self):
        """选择水印文件"""
        file_path = filedialog.askopenfilename(
            title="选择水印/素材文件",
            filetypes=[
                ("图片/视频文件", "*.png *.jpg *.jpeg *.gif *.mp4 *.avi *.mov"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.watermark_path.set(file_path)
    
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def log_status(self, message):
        """更新状态文本"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def get_watermark_position(self, video_width, video_height, watermark_width, watermark_height):
        """计算水印位置"""
        margin = 20  # 边距
        pos = self.watermark_position.get()
        
        if pos == "左上角":
            return (margin, margin)
        elif pos == "右上角":
            return (video_width - watermark_width - margin, margin)
        elif pos == "左下角":
            return (margin, video_height - watermark_height - margin)
        elif pos == "右下角":
            return (video_width - watermark_width - margin, video_height - watermark_height - margin)
        elif pos == "居中":
            return ((video_width - watermark_width) // 2, (video_height - watermark_height) // 2)
        else:
            return (video_width - watermark_width - margin, video_height - watermark_height - margin)
    
    def process_video(self, video_path, watermark_path, output_path):
        """处理单个视频"""
        try:
            # 读取视频
            video = VideoFileClip(video_path)
            
            # 判断水印类型
            watermark_ext = Path(watermark_path).suffix.lower()
            
            if watermark_ext in ['.png', '.jpg', '.jpeg', '.gif']:
                # 图片水印
                watermark = ImageClip(watermark_path).set_duration(video.duration)
            else:
                # 视频水印
                watermark = VideoFileClip(watermark_path)
                # 若素材视频比目标视频长，则裁剪；若更短，则仅在素材时长内显示
                if watermark.duration and video.duration:
                    end = min(video.duration, watermark.duration)
                    watermark = watermark.subclip(0, end)
            
            # 计算水印大小
            target_width = video.w * self.watermark_size.get()
            watermark = watermark.resize(width=target_width)
            # 不透明度
            watermark = watermark.set_opacity(self.watermark_opacity.get())
            
            # 设置位置
            pos = self.get_watermark_position(video.w, video.h, watermark.w, watermark.h)
            watermark = watermark.set_position(pos)
            
            # 合成
            final = CompositeVideoClip([video, watermark])
            
            # 写入文件
            final.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # 清理
            video.close()
            watermark.close()
            final.close()
            
            return True
        except Exception as e:
            self.log_status(f"处理失败: {e}")
            return False
    
    def process_videos(self):
        """批量处理视频"""
        video_folder = self.video_folder.get()
        watermark_path = self.watermark_path.get()
        output_folder = self.output_folder.get()
        
        if not video_folder or not watermark_path or not output_folder:
            messagebox.showwarning("警告", "请填写所有路径")
            self.is_processing = False
            self.start_button.config(state=tk.NORMAL)
            return
        
        # 获取视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = []
        for f in os.listdir(video_folder):
            if Path(f).suffix.lower() in video_extensions:
                video_files.append(f)
        
        if not video_files:
            messagebox.showwarning("警告", "所选文件夹中没有视频文件")
            self.is_processing = False
            self.start_button.config(state=tk.NORMAL)
            return
        
        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)
        
        # 设置进度条
        self.progress_bar['maximum'] = len(video_files)
        self.progress_bar['value'] = 0
        
        success_count = 0
        for i, video_file in enumerate(video_files):
            self.progress_label.config(text=f"正在处理: {video_file} ({i+1}/{len(video_files)})")
            self.log_status(f"开始处理: {video_file}")
            
            video_path = os.path.join(video_folder, video_file)
            output_path = os.path.join(output_folder, f"output_{video_file}")
            
            if self.process_video(video_path, watermark_path, output_path):
                success_count += 1
                self.log_status(f"完成: {video_file}")
            else:
                self.log_status(f"失败: {video_file}")
            
            self.progress_bar['value'] = i + 1
            self.root.update_idletasks()
        
        self.progress_label.config(text=f"处理完成! 成功: {success_count}/{len(video_files)}")
        self.log_status(f"\n处理完成! 成功: {success_count}/{len(video_files)}")
        messagebox.showinfo("完成", f"处理完成!\n成功: {success_count}/{len(video_files)}")
        
        self.is_processing = False
        self.start_button.config(state=tk.NORMAL)
    
    def start_processing(self):
        """开始处理"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        
        # 清空状态
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_videos)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    app = VideoWatermarkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

import os
from PIL import Image
import torch
import clip
import base64
import io
from config import Config

class ImageProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load(Config.CLIP_MODEL_NAME, device=self.device)
    
    def process_image(self, image_path):
        """
        处理图片，返回PIL Image对象
        """
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 转换为RGB格式（处理RGBA等格式）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 调整图片大小（可选，根据需要调整）
            max_size = 1024
            if image.size[0] > max_size or image.size[1] > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise Exception(f"图片处理失败: {str(e)}")
    
    def image_to_base64(self, image):
        """
        将PIL Image转换为base64字符串
        """
        try:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return img_str
        except Exception as e:
            raise Exception(f"图片转base64失败: {str(e)}")
    
    def base64_to_image(self, base64_str):
        """
        将base64字符串转换为PIL Image
        """
        try:
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            raise Exception(f"base64转图片失败: {str(e)}")
    
    def resize_image(self, image, size=(224, 224)):
        """
        调整图片大小
        """
        return image.resize(size, Image.Resampling.LANCZOS)
    
    def validate_image(self, image_path):
        """
        验证图片文件是否有效
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False